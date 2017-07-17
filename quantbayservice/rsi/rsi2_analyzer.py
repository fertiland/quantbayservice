#!/usr/bin/python
import rsi2d
import sys
import sinafinance
import time
import datetime
from pyalgotrade import plotter
from pyalgotrade.tools import yahoofinance
from pyalgotrade.stratanalyzer import returns
from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade.stratanalyzer import drawdown
from pyalgotrade.stratanalyzer import trades

__data_csv__="../data/csv"

def rsi2Trade(plot, storage, instrument, entrySMA, exitSMA, rsiPeriod, overBoughtThreshold, overSoldThreshold):
    # Download the bars.
    feed = yahoofinance.build_feed([instrument], 2015, 2017, storage)
    tm_hour = int(time.strftime('%H', time.localtime()))
    weekdayNumber = datetime.datetime.today().weekday()
    if ( weekdayNumber >= 0 and weekdayNumber <= 4) and ( tm_hour >= 9 and tm_hour <= 23 ):
        feed.addBarsFromCSV(instrument, sinafinance.download_current_trade(instrument, storage))

    strat = rsi2d.RSI2(feed, instrument, entrySMA, exitSMA, rsiPeriod, overBoughtThreshold, overSoldThreshold)

    strat.attachAnalyzer(retAnalyzer)
    sharpeRatioAnalyzer = sharpe.SharpeRatio()
    strat.attachAnalyzer(sharpeRatioAnalyzer)
    drawDownAnalyzer = drawdown.DrawDown()
    strat.attachAnalyzer(drawDownAnalyzer)
    tradesAnalyzer = trades.Trades()
    strat.attachAnalyzer(tradesAnalyzer)

    if plot:
        plt = plotter.StrategyPlotter(strat, True, False, True)
        plt.getInstrumentSubplot(instrument).addDataSeries("Entry SMA", strat.getEntrySMA())
        plt.getInstrumentSubplot(instrument).addDataSeries("Exit SMA", strat.getExitSMA())
        plt.getOrCreateSubplot("rsi").addDataSeries("RSI", strat.getRSI())
        plt.getOrCreateSubplot("rsi").addLine("Overbought", overBoughtThreshold)
        plt.getOrCreateSubplot("rsi").addLine("Oversold", overSoldThreshold)

    strat.run()

    print "Correct Ratio: %.2f" % ((float(tradesAnalyzer.getProfitableCount())/tradesAnalyzer.getCount()) if tradesAnalyzer.getCount() else -1.0)
    print "Evaluation Final portfolio value: %.2f" % strat.getResult()
    print "Evaluation Cumulative returns: %.2f" % (retAnalyzer.getCumulativeReturns()[-1] * 100)
    print "Evaluation Sharpe ratio: %.2f" % (sharpeRatioAnalyzer.getSharpeRatio(0.05))
    print "Evaluation Max. drawdown: %.2f" % (drawDownAnalyzer.getMaxDrawDown() * 100)
    print "Evaluation Longest drawdown duration: %s" % (drawDownAnalyzer.getLongestDrawDownDuration())

    print
    print "Final trades: %d" % (tradesAnalyzer.getCount())
    if tradesAnalyzer.getCount() > 0:
        profits = tradesAnalyzer.getAll()
        print "Final Avg. profit: %.2f" % (profits.mean())
        print "Final Profits std. dev.: %.2f" % (profits.std())
        print "Final Max. profit: %.2f" % (profits.max())
        print "Final Min. profit: %.2f" % (profits.min())
        returns = tradesAnalyzer.getAllReturns()
        print "Final Avg. return: %2.f" % (returns.mean() * 100)
        print "Final Returns std. dev.: %2.f" % (returns.std() * 100)
        print "Final Max. return: %2.f" % (returns.max() * 100)
        print "Final Min. return: %2.f" % (returns.min() * 100)

    print
    print "Profitable trades: %d" % (tradesAnalyzer.getProfitableCount())
    if tradesAnalyzer.getProfitableCount() > 0:
        profits = tradesAnalyzer.getProfits()
        print "Profitable Avg. profit: $%.2f" % (profits.mean())
        print "Profitable Profits std. dev.: $%.2f" % (profits.std())
        print "Profitable Max. profit: $%.2f" % (profits.max())
        print "Profitable Min. profit: $%.2f" % (profits.min())
        returns = tradesAnalyzer.getPositiveReturns()
        print "Profitable Avg. return: %2.f %%" % (returns.mean() * 100)
        print "Profitable Returns std. dev.: %2.f %%" % (returns.std() * 100)
        print "Profitable Max. return: %2.f %%" % (returns.max() * 100)
        print "Profitable Min. return: %2.f %%" % (returns.min() * 100)

    print
    print "Unprofitable trades: %d" % (tradesAnalyzer.getUnprofitableCount())
    if tradesAnalyzer.getUnprofitableCount() > 0:
        losses = tradesAnalyzer.getLosses()
        print "Unprofitable Avg. loss: $%.2f" % (losses.mean())
        print "Unprofitable Losses std. dev.: $%.2f" % (losses.std())
        print "Unprofitable Max. loss: $%.2f" % (losses.min())
        print "Unprofitable Min. loss: $%.2f" % (losses.max())
        returns = tradesAnalyzer.getNegativeReturns()
        print "Unprofitable Avg. return: %2.f %%" % (returns.mean() * 100)
        print "Unprofitable Returns std. dev.: %2.f %%" % (returns.std() * 100)
        print "Unprofitable Max. return: %2.f %%" % (returns.max() * 100)
        print "Unprofitable Min. return: %2.f %%" % (returns.min() * 100)

    if plot:
        plt.plot()


if __name__ == "__main__":
    instrument = sys.argv[1]
    entrySMA = int(sys.argv[2])
    exitSMA = int(sys.argv[3])
    rsiPeriod = int(sys.argv[4])
    overBoughtThreshold = int(sys.argv[5])
    overSoldThreshold = int(sys.argv[6])
    retAnalyzer = returns.Returns()
#    rsi2Trade(True, market, instrument, entrySMA, exitSMA, rsiPeriod, overBoughtThreshold, overSoldThreshold)
    rsi2Trade(False, __data_csv__, instrument, entrySMA, exitSMA, rsiPeriod, overBoughtThreshold, overSoldThreshold)
