import aiohttp
from collections import defaultdict, deque
from pathlib import Path
from functools import partial
import asyncio
from .constants import MatColors, GRAPH_TYPES, SAMPLING_FREQS
from .charts import CHARTS

import os
import streamlit as st

TKN = os.getenv("FINNHUB_TOKEN")

WS_CONN = f"wss://ws.finnhub.io?token={TKN}"


def add_custom_css():
    st.markdown(
        f"""
        <style>
        .stocks-up {{
            background: {MatColors.GREEN_700.value} !important;
            width: fit-content !important;
            padding: 10px !important;
            color: white !important;
            font-weight: 700 !important;
            border-radius: 10px !important;
        }}
        .stocks-down {{
            background: {MatColors.RED_700.value} !important;
            width: fit-content !important;
            padding: 10px !important;
            color: white !important;
            font-weight: 700 !important;
            border-radius: 10px !important;
        }}
        </style>
    """,
        unsafe_allow_html=True,
    )


def colored_text(price, change):
    return f"""
        <p class={["stocks-down", "stocks-up"][change>0]}>{price} {change:+.2f} </p>
    """


def create_data_box(container, channel_name, global_graph_type, global_sampling_freq):
    container.subheader(channel_name)
    up_down = container.empty()
    graph = container.empty()

    with container.beta_expander("Chart Config"):
        graph_type = st.selectbox(
            "Graph Type",
            GRAPH_TYPES,
            key=f"gtype{channel_name}",
            index=GRAPH_TYPES.index(global_graph_type)
        )
        sampling_freq = st.selectbox(
            "Sampling Frequency",
            SAMPLING_FREQS,
            key=f"stype{channel_name}",
            index=SAMPLING_FREQS.index(global_sampling_freq)
        )
    return {
        "stat": up_down,
        "chart": graph,
        "chart_type": graph_type,
        "chart_opt": {"sampling_freq": sampling_freq},
    }


def process_message(channel_data, graph):
    prev = channel_data[-2]["price"]
    current = channel_data[-1]["price"]
    graph["stat"].markdown(
        colored_text(current, current - prev), unsafe_allow_html=True
    )
    chart_key = graph["chart_type"].lower()
    graph["chart"].altair_chart(
        CHARTS[chart_key](channel_data, **graph["chart_opt"]), use_container_width=True
    )


async def consumer(graphs, selected_channels, status, state):
    state.windows = state.windows or defaultdict(partial(deque, maxlen=1_000))

    for channel, graph in graphs.items():
        if state.windows[channel] and len(state.windows[channel]) > 2:
            process_message(channel_data=state.windows[channel], graph=graph)
        else:
            graph["chart"].info(f"Waiting for data in channel {channel}")

    async with aiohttp.ClientSession(trust_env=True) as session:
        status.subheader(f"Connecting...")
        async with session.ws_connect(WS_CONN) as websocket:
            status.subheader(f"Connected.")
            for symbl in graphs:
                await websocket.send_json({"type": "subscribe", "symbol": symbl})

            async for message in websocket:
                data = message.json()
                if "data" in data:
                    for d in data["data"]:
                        state.windows[d["s"]].append({"ts": d["t"], "price": d["p"]})

                    for channel, graph in graphs.items():
                        if state.windows[channel] and len(state.windows[channel]) > 2:
                            process_message(
                                channel_data=state.windows[channel], graph=graph
                            )
