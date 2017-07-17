# -*- coding: utf-8 -*-
#!/usr/bin/python
import rsi2d
import sys
import time
import datetime
from pyalgotrade import plotter
from quantbayservice.tools import yahoofinance
from quantbayservice.tools import sinafinance
from pyalgotrade.stratanalyzer import sharpe

__data_csv__="../data/csv"

def rsi2Trade(plot, storage, instrument, entrySMA, exitSMA, rsiPeriod, overBoughtThreshold, overSoldThreshold):
#    instrument = "600036.ss"
#    entrySMA = 200
#    entrySMA = 77
#    exitSMA = 11
#    rsiPeriod = 3
#    overBoughtThreshold = 77
#    overSoldThreshold = 24

    # Download the bars.
    feed = yahoofinance.build_feed([instrument], 2015, 2017, storage,skipErrors=True)
    tm_hour = int(time.strftime('%H', time.localtime()))
    weekdayNumber = datetime.datetime.today().weekday()
    if ( weekdayNumber >= 0 and weekdayNumber <= 4) and (tm_hour >= 9 and tm_hour <= 23 ):
    	feed.addBarsFromCSV(instrument, sinafinance.download_current_trade(instrument, storage))
    strat = rsi2d.RSI2(feed, instrument, entrySMA, exitSMA, rsiPeriod, overBoughtThreshold, overSoldThreshold)

    sharpeRatioAnalyzer = sharpe.SharpeRatio()
    strat.attachAnalyzer(sharpeRatioAnalyzer)

    if plot:
        plt = plotter.StrategyPlotter(strat, True, False, True)
        plt.getInstrumentSubplot(instrument).addDataSeries("Entry SMA", strat.getEntrySMA())
        plt.getInstrumentSubplot(instrument).addDataSeries("Exit SMA", strat.getExitSMA())
        plt.getOrCreateSubplot("rsi").addDataSeries("RSI", strat.getRSI())
        plt.getOrCreateSubplot("rsi").addLine("Overbought", overBoughtThreshold)
        plt.getOrCreateSubplot("rsi").addLine("Oversold", overSoldThreshold)

    strat.run()
    print "Sharpe ratio: %.2f" % sharpeRatioAnalyzer.getSharpeRatio(0.05)
    print "RSI Portfilo: %.2f" % strat.getBroker().getEquity()

    if plot:
        plt.plot()


if __name__ == "__main__":
#./rsi2_sample.py 300222.sz 32 8 2 84 24
    instrument = sys.argv[1]
    entrySMA = int(sys.argv[2])
    exitSMA = int(sys.argv[3])
    rsiPeriod = int(sys.argv[4])
    overBoughtThreshold = int(sys.argv[5])
    overSoldThreshold = int(sys.argv[6])
#    rsi2Trade(True, market, instrument, entrySMA, exitSMA, rsiPeriod, overBoughtThreshold, overSoldThreshold)
    rsi2Trade(False, __data_csv__, instrument, entrySMA, exitSMA, rsiPeriod, overBoughtThreshold, overSoldThreshold)
#    main(False)
