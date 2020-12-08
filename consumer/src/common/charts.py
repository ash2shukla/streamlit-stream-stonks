import altair as alt
import pandas as pd
from .constants import MatColors


def get_candlestick(data_dict, sampling_freq, **kwargs):
    source = pd.DataFrame(list(data_dict))

    source.ts = source.ts.astype("datetime64[ms]")

    source = source.set_index("ts")

    source = source.price.resample(sampling_freq).ohlc().reset_index().bfill()

    open_close_color = alt.condition(
        "datum.open <= datum.close",
        alt.value(MatColors.GREEN_700.value),
        alt.value(MatColors.RED_700.value),
    )

    base_chart = alt.Chart(source).encode(
        alt.X("ts:T", axis=alt.Axis(labelAngle=-45,)), color=open_close_color
    )

    rule = base_chart.mark_rule().encode(
        alt.Y("low:Q", scale=alt.Scale(zero=False), title="Price"), alt.Y2("high:Q")
    )

    bar = base_chart.mark_bar().encode(alt.Y("open:Q"), alt.Y2("close:Q"))

    return rule + bar


def get_line(data_dict, sampling_freq, **kwargs):
    source = pd.DataFrame(list(data_dict))

    source.ts = source.ts.astype("datetime64[ms]")

    source = source.set_index("ts").resample(sampling_freq).mean().reset_index().bfill()

    base_chart = (
        alt.Chart(source)
        .mark_area(
            line={"color": "darkgreen"},
            color=alt.Gradient(
                gradient="linear",
                stops=[
                    alt.GradientStop(color="white", offset=0),
                    alt.GradientStop(color="darkgreen", offset=1),
                ],
                x1=1,
                x2=1,
                y1=1,
                y2=0,
            ),
        )
        .encode(
            x=alt.X("ts:T"),
            y=alt.Y(
                "price:Q",
                scale=alt.Scale(domain=[source.price.min(), source.price.max()]),
            ),
        )
    )

    return base_chart


def get_bars(data_dict, sampling_freq, **kwargs):
    source = pd.DataFrame(list(data_dict))

    source.ts = source.ts.astype("datetime64[ms]")

    source = source.set_index("ts").resample(sampling_freq).mean().reset_index().bfill()

    base_chart = (
        alt.Chart(source).mark_bar().encode(x=alt.X("ts:T"), y=alt.Y("price:Q"))
    )

    return base_chart


CHARTS = {"candlestick": get_candlestick, "line": get_line, "bar": get_bars}
