# PyAlgoTrade
#
# Copyright 2011-2015 Gabriel Martin Becedillas Ruiz
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""

import os
import datetime
import time
import requests
import random
from retrying import retry
import pandas as pd
import numpy as np
import ConfigParser

import pyalgotrade.logger
from pyalgotrade import bar
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.utils import dt
from pyalgotrade.utils import csvutils


def __adjust_month(month):
    if month > 12 or month < 1:
        raise Exception("Invalid month")
    month -= 1  # Months for yahoo are 0 based
    return month

@retry(wait_random_min=1000, wait_random_max=2000,stop_max_attempt_number=5)
def download_csv(instrument, begin, end, frequency):
    #url = "http://ichart.finance.yahoo.com/table.csv?s=%s&a=%d&b=%d&c=%d&d=%d&e=%d&f=%d&g=%s&ignore=.csv" % (instrument, __adjust_month(begin.month), begin.day, begin.year, __adjust_month(end.month), end.day, end.year, frequency)
    s = requests.Session()
    r = s.get('https://finance.yahoo.com')    
    crumb = s.get('https://query1.finance.yahoo.com/v1/test/getcrumb')
    print(crumb.text)
    url = "https://query1.finance.yahoo.com/v7/finance/download/%s?period1=%d&period2=%d&interval=1d&events=history&crumb=%s" % (instrument, int(begin.strftime("%s")), int(end.strftime("%s")), crumb.text)
    print(url)
    res = s.get(url)
    print(res.text)
    res.raise_for_status()
    #return csvutils.download_csv(url)
    return res.text


def download_daily_bars(instrument, year, csvFile):
    """Download daily bars from Yahoo! Finance for a given year.

    :param instrument: Instrument identifier.
    :type instrument: string.
    :param year: The year.
    :type year: int.
    :param csvFile: The path to the CSV file to write.
    :type csvFile: string.
    """

    bars = download_csv(instrument, datetime.date(year, 1, 1), datetime.date(year, 12, 31), "d")
    f = open(csvFile, "w")
    f.write(bars)
    f.close()

    df = pd.read_csv(csvFile)

    #filter out the rows that contain null
    df['High'].replace('null', np.nan, inplace=True)
    #df['Volume'].replace('0', np.nan, inplace=True)
    df = df[df['High'].notnull()]
    #df = df[df['Volume'].notnull()]
    df = df.drop_duplicates(['Date'])
    #reset the columns
    colTitles = ['Date','Open','High','Low','Close','Volume','Adj Close']
    df=df.reindex(columns=colTitles)
    df=df.sort_values('Date', ascending=False)

    df.to_csv(csvFile, index=False)


def download_weekly_bars(instrument, year, csvFile):
    """Download weekly bars from Yahoo! Finance for a given year.

    :param instrument: Instrument identifier.
    :type instrument: string.
    :param year: The year.
    :type year: int.
    :param csvFile: The path to the CSV file to write.
    :type csvFile: string.
    """

    begin = dt.get_first_monday(year)
    end = dt.get_last_monday(year) + datetime.timedelta(days=6)
    bars = download_csv(instrument, begin, end, "w")
    f = open(csvFile, "w")
    f.write(bars)
    f.close()


def is_working_hour():
    tm_hour = int(time.strftime('%H', time.localtime()))
    weekdayNumber = datetime.datetime.today().weekday()
    if ( weekdayNumber >= 0 and weekdayNumber <= 4) and (tm_hour >= 9 and tm_hour <= 15 ):
        return False
    else:
        return False

def is_download_data_enabled():
    config = ConfigParser.ConfigParser()
    config.read("/home/qipingli/stock/python/stock.ini")
    downloadEnabled = config.getboolean('feature', 'enable_download_data')
    return True


def build_feed(instruments, fromYear, toYear, storage, frequency=bar.Frequency.DAY, timezone=None, skipErrors=False, toYearOnly=True):
    """Build and load a :class:`pyalgotrade.barfeed.yahoofeed.Feed` using CSV files downloaded from Yahoo! Finance.
    CSV files are downloaded if they haven't been downloaded before.

    :param instruments: Instrument identifiers.
    :type instruments: list.
    :param fromYear: The first year.
    :type fromYear: int.
    :param toYear: The last year.
    :type toYear: int.
    :param storage: The path were the files will be loaded from, or downloaded to.
    :type storage: string.
    :param frequency: The frequency of the bars. Only **pyalgotrade.bar.Frequency.DAY** or **pyalgotrade.bar.Frequency.WEEK**
        are supported.
    :param timezone: The default timezone to use to localize bars. Check :mod:`pyalgotrade.marketsession`.
    :type timezone: A pytz timezone.
    :param skipErrors: True to keep on loading/downloading files in case of errors.
    :type skipErrors: boolean.
    :rtype: :class:`pyalgotrade.barfeed.yahoofeed.Feed`.
    """

    logger = pyalgotrade.logger.getLogger("yahoofinance")
    ret = yahoofeed.Feed(frequency, timezone)

    if not os.path.exists(storage):
        logger.info("Creating %s directory" % (storage))
        os.mkdir(storage)

    for year in range(fromYear, toYear+1):
        for instrument in instruments:
            fileName = os.path.join(storage, "%s-%d-yahoofinance.csv" % (instrument, year))
            if (not os.path.exists(fileName)) and (not is_working_hour()) and is_download_data_enabled():
                logger.info("Downloading %s %d to %s" % (instrument, year, fileName))
                try:
                    if frequency == bar.Frequency.DAY:
                        download_daily_bars(instrument, year, fileName)
                    elif frequency == bar.Frequency.WEEK:
                        download_weekly_bars(instrument, year, fileName)
                    else:
                        raise Exception("Invalid frequency")
                except Exception, e:
                    if skipErrors:
                        logger.error(str(e))
                        continue
                    else:
                        raise e
            if os.path.exists(fileName):
                ret.addBarsFromCSV(instrument, fileName)
    return ret
