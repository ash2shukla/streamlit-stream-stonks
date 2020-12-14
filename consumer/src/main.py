import asyncio

import streamlit as st
from common.utils import consumer, create_data_box, add_custom_css
from common.constants import SYMBLS, GRAPH_TYPES, SAMPLING_FREQS
from common.state import provide_state

st.set_page_config(page_title="STONKS!", layout="wide")

add_custom_css()


@provide_state
def main(state):
    with st.sidebar:
        token_placeholder = st.empty()

        token = token_placeholder.text_input("Finnhub Token")

        if token:
            token_placeholder.empty()

        status = st.empty()

        status.subheader("Disconnected.")

        selected_channels = st.multiselect(
            "Select Stocks",
            SYMBLS,
            format_func=lambda x: f'{x["symbol"]} - {x["description"]}',
        )
        start_streaming = st.checkbox("Start Streaming.")

        st.markdown("---")
        st.subheader("Global Chart Config")


        global_graph_type = st.selectbox(
            "Graph Type", GRAPH_TYPES, key="gtypeglob"
        )
        global_sampling_freq = st.selectbox(
            "Sampling Frequency",
            SAMPLING_FREQS,
            key="stypeglob",
        )


    if start_streaming and selected_channels:
        columns = []
        i = 0

        for i in range(0, len(selected_channels), 2):
            with st.beta_container():
                cols = st.beta_columns(2)
                for col, channel in zip(cols, selected_channels[i : i + 2]):
                    columns.append(create_data_box(col, channel["description"], global_graph_type, global_sampling_freq))

        selected_channels_symbols = [stock["symbol"] for stock in selected_channels]

        asyncio.run(
            consumer(
                dict(zip(selected_channels_symbols, columns)),
                selected_channels,
                status,
                state,
                FINNHUB_TOKEN=token
            )
        )


if __name__ == "__main__":
    main()
