import asyncio

import streamlit as st
from utils import consumer, create_data_box, add_custom_css
from constants import SYMBLS
from state import provide_state

st.set_page_config(page_title="Stonks", layout="wide")

add_custom_css()

@provide_state
def main(state):
    with st.sidebar:
        status = st.empty()

        status.subheader("Disconnected.")

        selected_channels = st.multiselect(
            "Select Stocks",
            SYMBLS,
            format_func=lambda x: f'{x["symbol"]} - {x["description"]}')

        start_streaming = st.checkbox("Start Streaming.")

    if start_streaming and selected_channels:
        columns = []
        i = 0

        for i in range(0, len(selected_channels), 3):
            with st.beta_container():
                cols = st.beta_columns(min(i+3, len(selected_channels))-i)
                for col, channel in zip(cols, selected_channels[i:i+3]):
                    columns.append(create_data_box(col, channel["description"]))

        selected_channels_symbols = [stock["symbol"] for stock in selected_channels]

        asyncio.run(consumer(dict(zip(selected_channels_symbols, columns)), selected_channels, status, state))


if __name__ == "__main__":
    main()