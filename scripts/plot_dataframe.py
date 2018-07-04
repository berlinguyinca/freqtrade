#!/usr/bin/env python3
"""
Script to display when the bot will buy a specific pair

Mandatory Cli parameters:
-p / --pair: pair to examine

Optional Cli parameters
-s / --strategy: strategy to use
-d / --datadir: path to pair backtest data
--timerange: specify what timerange of data to use.
-l / --live: Live, to download the latest ticker for the pair
-db / --db-url: Show trades stored in database

--plot-max-ticks N: plot N data points and overwrite the internal 750 cut of


Plotting Subplots, require the name of the dataframe column.

Each plot will be displayed as usual on exchanges

--plot-rsi <RSI>
--plot-cci <CCI>
--plot-osc <CCI>
--plot-macd <MACD>
--plot-cmf <CMF>


--
"""
import datetime
import logging
import sys
from argparse import Namespace
from typing import List

import plotly.graph_objs as go
from plotly import tools
from plotly.offline import plot

from typing import Dict, List, Any
from sqlalchemy import create_engine

import freqtrade.optimize as optimize
from freqtrade import exchange
from freqtrade.analyze import Analyze
from freqtrade.arguments import Arguments
from freqtrade.analyze import Analyze
from freqtrade import exchange
import freqtrade.optimize as optimize
from freqtrade import persistence
from freqtrade.persistence import Trade
from freqtrade.configuration import Configuration
from pandas import DataFrame

logger = logging.getLogger(__name__)
_CONF: Dict[str, Any] = {
}
logger = logging.getLogger('freqtrade')


def plot_dataframes_markers(data, fig, args):
    """
        plots additional dataframe markers in the main plot
    :param data:
    :param fig:
    :param args:
    :return:
    """

    if args.plotdataframemarker:
        for x in args.plotdataframemarker:
            filter = data[(data[x] == 100) | (data[x] == -100)]
            marker = go.Scatter(
                x=filter.date,
                y=filter.low * 0.99,
                mode='markers',
                name=x,
                marker=dict(
                    symbol='diamond-tall-open',
                    size=10,
                    line=dict(width=1)
                )

            )

            fig.append_trace(marker, 1, 1)


def plot_dataframes(data, fig, args):
    """
        plots additional dataframes in the main plot
    :param data:
    :param fig:
    :param args:
    :return:
    """

    if args.plotdataframe:
        for x in args.plotdataframe:
            chart = go.Scattergl(x=data['date'], y=data[x], name=x)
            fig.append_trace(chart, 1, 1)


def plot_volume_dataframe(data, fig, args, plotnumber):
    """
        adds the plotting of the volume
    :param data:
    :param fig:
    :param args:
    :return:
    """

    volume = go.Bar(x=data['date'], y=data['volume'], name='Volume')
    fig.append_trace(volume, plotnumber, 1)


def plot_macd_dataframe(data, fig, args, plotnumber):
    """
        adds the plotting of the MACD if specified
    :param data:
    :param fig:
    :param args:
    :return:
    """

    macd = go.Scattergl(x=data['date'], y=data[args.plotmacd], name='MACD')
    macdsignal = go.Scattergl(x=data['date'], y=data[args.plotmacd + 'signal'], name='MACD signal')
    fig.append_trace(macd, plotnumber, 1)
    fig.append_trace(macdsignal, plotnumber, 1)


def plot_rsi_dataframe(data, fig, args, plotnumber):
    """

        this function plots an additional RSI chart under the exiting charts
    :param data:
    :param fig:
    :param args:
    :return:
    """
    if args.plotrsi:
        for x in args.plotrsi:
            rsi = go.Scattergl(x=data['date'], y=data[x], name=x)
            fig.append_trace(rsi, plotnumber, 1)

    fig['layout']['shapes'].append(
        {
            'yref': 'y' + str(plotnumber),
            'fillcolor': 'red',
            'opacity': 0.1,
            'type': 'rect',
            'x0': DataFrame.min(data['date']),
            'x1': DataFrame.max(data['date']),
            'y0': 70,
            'y1': 100,
            'line': {'color': 'gray'}
        }
    )
    fig['layout']['shapes'].append(
        {
            'yref': 'y' + str(plotnumber),
            'fillcolor': 'green',
            'opacity': 0.1,
            'type': 'rect',
            'x0': DataFrame.min(data['date']),
            'x1': DataFrame.max(data['date']),
            'y0': 0,
            'y1': 30,
            'line': {'color': 'gray'}
        }
    )


def plot_osc_dataframe(data, fig, args, plotnumber):
    """

        this function plots an additional cci chart under the exiting charts
    :param data:
    :param fig:
    :param args:
    :return:
    """

    if args.plotosc:
        for x in args.plotosc:
            chart = go.Scattergl(x=data['date'], y=data[x], name=x)
            fig.append_trace(chart, plotnumber, 1)

    fig['layout']['shapes'].append(
        {
            'yref': 'y' + str(plotnumber),
            'fillcolor': 'gray',
            'opacity': 0.1,
            'type': 'rect',
            'x0': DataFrame.min(data['date']),
            'x1': DataFrame.max(data['date']),
            'y0': 0.3,
            'y1': 0.7,
            'line': {'color': 'gray'}
        }
    )
    fig['layout']['shapes'].append(
        {
            'yref': 'y' + str(plotnumber),
            'type': 'line',
            'x0': DataFrame.min(data['date']),
            'x1': DataFrame.max(data['date']),
            'y0': 0.6,
            'y1': 0.6,
            'line': {'color': 'red','width': 1}
        }
    )
    fig['layout']['shapes'].append(
        {
            'yref': 'y' + str(plotnumber),
            'type': 'line',
            'x0': DataFrame.min(data['date']),
            'x1': DataFrame.max(data['date']),
            'y0': 0.4,
            'y1': 0.4,
            'line': {'color': 'green','width':1}
        }
    )


def plot_cmf_dataframe(data, fig, args, plotnumber):
    """

        this function plots an additional cci chart under the exiting charts
    :param data:
    :param fig:
    :param args:
    :return:
    """

    minValue = 0;
    maxValue = 0;
    if args.plotcmf:
        for x in args.plotcmf:
            chart = go.Bar(x=data['date'], y=data[x], name=x)
            fig.append_trace(chart, plotnumber, 1)


def plot_cci_dataframe(data, fig, args, plotnumber):
    """

        this function plots an additional cci chart under the exiting charts
    :param data:
    :param fig:
    :param args:
    :return:
    """

    minValue = 0;
    maxValue = 0;
    if args.plotcci:
        for x in args.plotcci:
            if minValue > min(data[x]):
                minValue = min(data[x])
            if maxValue < max(data[x]):
                maxValue = max(data[x])

            chart = go.Scattergl(x=data['date'], y=data[x], name=x)
            fig.append_trace(chart, plotnumber, 1)

    fig['layout']['shapes'].append(
        {
            'yref': 'y' + str(plotnumber),
            'fillcolor': 'red',
            'opacity': 0.1,
            'type': 'rect',
            'x0': DataFrame.min(data['date']),
            'x1': DataFrame.max(data['date']),
            'y0': 100,
            'y1': maxValue,
            'line': {'color': 'gray'}
        }
    )
    fig['layout']['shapes'].append(
        {
            'yref': 'y' + str(plotnumber),
            'fillcolor': 'green',
            'opacity': 0.1,
            'type': 'rect',
            'x0': DataFrame.min(data['date']),
            'x1': DataFrame.max(data['date']),
            'y0': -100,
            'y1': minValue,
            'line': {'color': 'gray'}
        }
    )


def plot_stop_loss_trade(df_sell, fig, analyze, args):
    """
        plots the stop loss for the associated trades and buys
        as well as the estimated profit ranges.

        will be enabled if --stop-loss is provided
        as argument

    :param data:
    :param trades:
    :return:
    """

    if args.stoplossdisplay is False:
        return

    if 'associated_buy_price' not in df_sell:
        return

    stoploss = analyze.strategy.stoploss

    for index, x in df_sell.iterrows():
        if x['associated_buy_price'] > 0:
            # draw stop loss
            fig['layout']['shapes'].append(
                {
                    'fillcolor': 'red',
                    'opacity': 0.1,
                    'type': 'rect',
                    'x0': x['associated_buy_date'],
                    'x1': x['date'],
                    'y0': x['associated_buy_price'],
                    'y1': (x['associated_buy_price'] - abs(stoploss) * x['associated_buy_price']),
                    'line': {'color': 'red'}
                }
            )

            totalTime = 0
            for time in analyze.strategy.minimal_roi:
                t = int(time)
                totalTime = t + totalTime

                enddate = x['date']

                date = x['associated_buy_date'] + datetime.timedelta(minutes=totalTime)

                # draw profit range
                fig['layout']['shapes'].append(
                    {
                        'fillcolor': 'green',
                        'opacity': 0.1,
                        'type': 'rect',
                        'x0': date,
                        'x1': enddate,
                        'y0': x['associated_buy_price'],
                        'y1': x['associated_buy_price'] + x['associated_buy_price'] * analyze.strategy.minimal_roi[
                            time],
                        'line': {'color': 'green'}
                    }
                )


def find_profits(data):
    """
        finds the profits between sells and the associated buys. This does not take in account
        ROI!
    :param data:
    :return:
    """

    # go over all the sells
    # find all previous buys

    df_sell = data[data['sell'] == 1]
    df_sell['profit'] = 0
    df_buys = data[data['buy'] == 1]
    lastDate = data['date'].iloc[0]

    for index, row in df_sell.iterrows():

        buys = df_buys[(df_buys['date'] < row['date']) & (df_buys['date'] > lastDate)]

        profit = None
        if buys['date'].count() > 0:
            buys = buys.tail()
            profit = round(row['close'] / buys['close'].values[0] * 100 - 100, 2)
            lastDate = row['date']

            df_sell.loc[index, 'associated_buy_date'] = buys['date'].values[0]
            df_sell.loc[index, 'associated_buy_price'] = buys['close'].values[0]

        df_sell.loc[index, 'profit'] = profit

    return df_sell


def plot_analyzed_dataframe(args: Namespace) -> None:
    """
    Calls analyze() and plots the returned dataframe
    :return: None
    """
    pair = args.pair.replace('-', '_')
    timerange = Arguments.parse_timerange(args.timerange)

    # Init strategy
    try:
        config = Configuration(args)

        analyze = Analyze(config.get_config())
    except AttributeError:
        logger.critical(
            'Impossible to load the strategy. Please check the file "user_data/strategies/%s.py"',
            args.strategy
        )
        exit()

    tick_interval = analyze.strategy.ticker_interval

    tickers = {}
    if args.live:
        logger.info('Downloading pair.')
        # Init Bittrex to use public API
        exchange.init({'key': '', 'secret': ''})
        tickers[pair] = exchange.get_ticker_history(pair, tick_interval)
    else:
        print("load data")
        tickers = optimize.load_data(
            datadir=_CONF.get("datadir"),
            pairs=[pair],
            ticker_interval=tick_interval,
            refresh_pairs=True,
            timerange=timerange
        )
    dataframes = analyze.tickerdata_to_dataframe(tickers)
    dataframe = dataframes[pair]
    dataframe = analyze.populate_buy_trend(dataframe)
    dataframe = analyze.populate_sell_trend(dataframe)

    if len(dataframe.index) > args.plotticks:
        logger.warning('Ticker contained more than {} candles, clipping.'.format(args.plotticks))
    data = dataframe.tail(args.plotticks)

    if len(dataframe.index) > 750:
        logger.warning('Ticker contained more than 750 candles, clipping.')
    data = dataframe.tail(750)

    candles = go.Candlestick(
        x=data.date,
        open=data.open,
        high=data.high,
        low=data.low,
        close=data.close,
        name='Price'
    )

    df_buy = data[data['buy'] == 1]

    buys = go.Scattergl(
        x=df_buy.date,
        y=df_buy.close,
        mode='markers',
        name='buy',
        marker=dict(
            symbol='triangle-up-dot',
            size=15,
            line=dict(width=1),
            color='green',
        )
    )
    df_sell = find_profits(data)

    sells = go.Scatter(
        x=df_sell.date,
        y=df_sell.close,
        mode='markers+text',
        name='sell',
        text=df_sell.profit,
        textposition='top right',
        marker=dict(
            symbol='triangle-down-dot',
            size=15,
            line=dict(width=1),
            color='red',
        )

    )

    bb_lower = go.Scatter(
        x=data.date,
        y=data.bb_lowerband,
        name='BB lower',
        line={'color': "transparent"},
    )
    bb_upper = go.Scatter(
        x=data.date,
        y=data.bb_upperband,
        name='BB upper',
        fill="tonexty",
        fillcolor="rgba(0,176,246,0.2)",
        line={'color': "transparent"},
    )
    bb_middle = go.Scatter(
        x=data.date,
        y=data.bb_middleband,
        name='BB middle',
        fill="tonexty",
        fillcolor="rgba(0,176,246,0.2)",
        line={'color': "red"},
    )

    # ugly hack for now
    rowWidth = [1]
    if args.plotvolume:
        rowWidth.append(1)
    if args.plotmacd:
        rowWidth.append(1)
    if args.plotrsi:
        rowWidth.append(1)
    if args.plotcci:
        rowWidth.append(1)
    if args.plotcmf:
        rowWidth.append(1)
    if args.plotosc:
        rowWidth.append(1)

    # standard layout signal + volume
    fig = tools.make_subplots(
        rows=len(rowWidth),
        cols=1,
        shared_xaxes=True,
        row_width=rowWidth,
        vertical_spacing=0.0001,
    )

    # todo should be optional
    fig.append_trace(candles, 1, 1)
    fig.append_trace(bb_lower, 1, 1)
    fig.append_trace(bb_middle, 1, 1)
    fig.append_trace(bb_upper, 1, 1)

    fig.append_trace(buys, 1, 1)
    fig.append_trace(sells, 1, 1)

    # append stop loss/profit
    plot_stop_loss_trade(df_sell, fig, analyze, args)

    # plot other dataframes
    plot_dataframes(data, fig, args)
    plot_dataframes_markers(data, fig, args)

    fig['layout'].update(title=args.pair)
    fig['layout']['yaxis1'].update(title='Price')

    subplots = 1

    if args.plotvolume:
        subplots = subplots + 1
        plot_volume_dataframe(data, fig, args, subplots)
        fig['layout']['yaxis' + str(subplots)].update(title='Volume')

    if args.plotmacd:
        subplots = subplots + 1
        plot_macd_dataframe(data, fig, args, subplots)
        fig['layout']['yaxis' + str(subplots)].update(title='MACD')

    if args.plotrsi:
        subplots = subplots + 1
        plot_rsi_dataframe(data, fig, args, subplots)
        fig['layout']['yaxis' + str(subplots)].update(title='RSI', range=[0, 100])

    if args.plotcci:
        subplots = subplots + 1
        plot_cci_dataframe(data, fig, args, subplots)
        fig['layout']['yaxis' + str(subplots)].update(title='CCI')

    if args.plotosc:
        subplots = subplots + 1
        plot_osc_dataframe(data, fig, args, subplots)
        fig['layout']['yaxis' + str(subplots)].update(title='OSC')

    if args.plotcmf:
        subplots = subplots + 1
        plot_cmf_dataframe(data, fig, args, subplots)
        fig['layout']['yaxis' + str(subplots)].update(title='CMF')

    # updated all the

    plot(fig, filename='freqtrade-plot.html')


def plot_parse_args(args: List[str]) -> Namespace:
    """
    Parse args passed to the script
    :param args: Cli arguments
    :return: args: Array with all arguments
    """
    arguments = Arguments(args, 'Graph dataframe')
    arguments.scripts_options()
    arguments.common_args_parser()
    arguments.optimizer_shared_options(arguments.parser)
    arguments.backtesting_options(arguments.parser)

    return arguments.parse_args()


def main(sysargv: List[str]) -> None:
    """
    This function will initiate the bot and start the trading loop.
    :return: None
    """
    logger.info('Starting Plot Dataframe')
    plot_analyzed_dataframe(
        plot_parse_args(sysargv)
    )


if __name__ == '__main__':
    main(sys.argv[1:])
