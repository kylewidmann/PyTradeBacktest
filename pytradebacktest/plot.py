import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pytrade.interfaces.data import IInstrumentData
from pytrade.models import Trade

# from pytradebacktest.data import MarketData


def plot(data: IInstrumentData, equity: pd.DataFrame, trades: list[Trade]):
    fig = make_subplots(rows=2, cols=1, row_heights=[0.2, 0.8], subplot_titles=("Equity", "Trades"))

    _plot_equity(fig, equity)
    _plot_ohlc(fig, data)
    _plot_trades(fig, data, trades)

    fig.show()


def _plot_equity(fig: go.Figure, equity: pd.DataFrame):
    fig.add_trace(
        go.Scatter(x=equity.index, y=equity["Equity"], mode="lines", name="Equity"),
        row=1,
        col=1,
    )


def _plot_ohlc(fig: go.Figure, data: IInstrumentData):
    df = data.df
    ohlc = go.Candlestick(
        x=df.index, open=df["open"], high=df["high"], low=df["low"], close=df["close"]
    )

    fig.add_trace(ohlc, row=2, col=1)
    fig.update_layout(xaxis2_rangeslider_visible=False)


def _plot_trades(fig: go.Figure, data: IInstrumentData, trades: list[Trade]):
    for trade in trades:
        # Add entry points
        fig.add_trace(
            go.Scatter(
                x=[trade.entry_time],
                y=[trade.entry_price],
                mode="markers",
                marker=dict(
                    size=10,
                    symbol="triangle-up" if trade.is_long else "triangle-down",
                    color="green" if trade.is_long else "red",
                    line=dict(color="black", width=1),
                ),
                hovertemplate=f"""
Date:%{{x}}<br>
Entry:%{{y}}<br>
Exit:{trade.exit_price}<br>
Size:{trade.size}<br>
{(f"SL: {trade.sl.stop}<br>" if trade.sl is not None else "")}
{(f"TP: {trade.tp.limit}<br>" if trade.tp is not None else "")}
P/L:{trade.pl}
""",
            ),
            row=2,
            col=1,
        )

        # Add line to exit
        fig.add_trace(
            go.Scatter(
                x=[trade.entry_time, trade.exit_time],
                y=[trade.entry_price, trade.exit_price],
                mode="lines",
                line=dict(color="green" if trade.pl > 0 else "red"),
            ),
            row=2,
            col=1,
        )

        if trade.sl is not None:
            # Add stop loss line
            fig.add_trace(
                go.Scatter(
                    x=[trade.entry_time, trade.exit_time],
                    y=[trade.sl.stop, trade.sl.stop],
                    mode="lines",
                    line=dict(color="red", dash="dashdot"),
                ),
                row=2,
                col=1,
            )

        if trade.tp is not None:
            # Add take profit line
            fig.add_trace(
                go.Scatter(
                    x=[trade.entry_time, trade.exit_time],
                    y=[trade.tp.limit, trade.tp.limit],
                    mode="lines",
                    line=dict(color="green", dash="dashdot"),
                ),
                row=2,
                col=1,
            )
