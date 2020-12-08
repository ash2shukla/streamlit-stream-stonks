import aiohttp
from collections import defaultdict, deque
from pathlib import Path
import altair as alt
import pandas as pd
from functools import partial
import asyncio

import streamlit as st

TKN = open(Path(__file__).parent.parent / 'token').read()

WS_CONN = f"wss://ws.finnhub.io?token={TKN}"

open_close_color = alt.condition("datum.open <= datum.close", alt.value("#06982d"), alt.value("#ae1325"))


def add_custom_css():
    st.markdown("""
        <style>
        .stocks-up {
            background: green !important;
            width: fit-content !important;
            padding: 10px !important;
            color: white !important;
            font-weight: 700 !important;
            border-radius: 10px !important;
        }
        .stocks-down {
            background: maroon !important;
            width: fit-content !important;
            padding: 10px !important;
            color: white !important;
            font-weight: 700 !important;
            border-radius: 10px !important;
        }
        </style>
    """, unsafe_allow_html=True)

def colored_text(price, change):
    return f"""
        <p class={["stocks-down", "stocks-up"][change>0]}>{price} {change:+.2f} </p>
    """

def get_candlestick(data_dict, sampling_freq, **kwargs):
    source = pd.DataFrame(list(data_dict))

    source.ts = source.ts.astype("datetime64[ms]")

    source = source.set_index("ts")
    
    source = source.price.resample("10S").ohlc().reset_index().bfill()

    base_chart = alt.Chart(source).encode(
        alt.X('ts:T',
          axis=alt.Axis(
              labelAngle=-45,
          )
        ),
        color=open_close_color
    )

    rule = base_chart.mark_rule().encode(
        alt.Y(
            'low:Q',
            scale=alt.Scale(zero=False),
            title="Price"
        ),
        alt.Y2('high:Q')
    )

    bar = base_chart.mark_bar().encode(
        alt.Y('open:Q'),
        alt.Y2('close:Q')
    )

    return rule + bar

def get_line(data_dict, sampling_freq, **kwargs):
    source = pd.DataFrame(list(data_dict))

    source.ts = source.ts.astype("datetime64[ms]")

    source = source.set_index("ts").resample(sampling_freq).mean().reset_index().bfill()

    base_chart = alt.Chart(source).mark_area(
        line={'color':'darkgreen'},
        color=alt.Gradient(
            gradient='linear',
            stops=[alt.GradientStop(color='white', offset=0),
                alt.GradientStop(color='darkgreen', offset=1)],
            x1=1,
            x2=1,
            y1=1,
            y2=0
        )
    ).encode(
        x=alt.X('ts:T'),
        y=alt.Y("price:Q", scale=alt.Scale(domain=[source.price.min(), source.price.max()]))
    )

    return base_chart

def get_bars(data_dict, sampling_freq, **kwargs):
    source = pd.DataFrame(list(data_dict))

    source.ts = source.ts.astype("datetime64[ms]")

    base_chart = alt.Chart(source).mark_bar().encode(
        x=alt.X('ts:T'),
        y=alt.Y("price:Q")
    )

    return base_chart


CHARTS = {
    "candlestick": get_candlestick,
    "line": get_line
}

def create_data_box(container, channel_name):
    container.subheader(channel_name)
    up_down = container.empty()
    graph = container.empty()
    graph_type = container.selectbox("Graph Type", ["CandleStick", "Line", "Bar"], key=f"gtype{channel_name}")
    sampling_freq = container.selectbox("Sampling Frequency", ["1S", "5S", "10S", "1Min", "5Min"], key=f"ctype{channel_name}")
    return {"stat": up_down, "chart": graph, "chart_type": graph_type, "chart_opt": {"sampling_freq": sampling_freq}}  


def process_message(channel_data, graph):
    prev = channel_data[-2]["price"]
    current = channel_data[-1]["price"]
    graph["stat"].markdown(colored_text(current, current-prev), unsafe_allow_html=True)
    chart_key = graph["chart_type"].lower()
    graph["chart"].altair_chart(CHARTS[chart_key](channel_data, **graph["chart_opt"]), use_container_width=True)


async def consumer(graphs, selected_channels, status, state):
    state.windows = state.windows or defaultdict(partial(deque, maxlen=1_000))

    for channel, graph in graphs.items():
        if state.windows[channel] and len(state.windows[channel]) > 2:
            process_message(channel_data=state.windows[channel], graph=graph)
        else:
            graph["chart"].info(f"Waiting for data in channel {channel}")
    
    async with aiohttp.ClientSession(trust_env = True) as session:
        status.subheader(f"Connecting...")
        async with session.ws_connect(WS_CONN) as websocket:
            status.subheader(f"Connected.")
            for symbl in graphs:
                await websocket.send_json({"type":"subscribe","symbol": symbl})

            async for message in websocket:
                data = message.json()
                if "data" in data:
                    for d in data["data"]:
                        state.windows[d["s"]].append({"ts": d["t"], "price": d["p"]})

                    for channel, graph in graphs.items():
                        if state.windows[channel] and len(state.windows[channel]) > 2:
                            process_message(channel_data=state.windows[channel], graph=graph)