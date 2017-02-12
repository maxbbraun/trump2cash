from optparse import OptionParser

from datetime import datetime

from pytz import timezone

from os import getenv

import requests
from requests_oauthlib import OAuth1

ENDPOINT = 'https://api.tradeking.com/v1'

MARKET_DATA_FILE = 'market_data/%s_%s.txt'


class TradeKing(object):
    def __init__(self, consumer_key=getenv('TRADEKING_CONSUMER_KEY'),
                 consumer_secret=getenv('TRADEKING_CONSUMER_SECRET'),
                 access_token=getenv('TRADEKING_ACCESS_TOKEN'),
                 access_secret=getenv('TRADEKING_ACCESS_TOKEN_SECRET')):
        self.requests = requests.Session()
        self.requests.auth = OAuth1(consumer_key,
                                    consumer_secret,
                                    access_token,
                                    access_secret)

    def _get(self, request, params=None):
        url = '%s/%s.json' % (ENDPOINT, request)
        return self.requests.get(url, params=params).json().get('response')

    def market_timesales(self, symbols, interval='1min', rpp='10', index=None,
                         startdate=None, enddate=None, starttime=None):
        params = dict(symbols=symbols,
                      interval=interval,
                      rpp=rpp,
                      index=index,
                      startdate=startdate,
                      enddate=enddate,
                      starttime=starttime)
        return self._get('market/timesales', params=params)


def gen_historical(ticker, day):
    tk = TradeKing()
    result = tk.market_timesales([ticker], startdate=day, enddate=day)

    f = open(MARKET_DATA_FILE % (ticker, day.strftime("%Y%m%d")), 'w')
    f.write("<ticker>,<date>,<last>\n")
    for quote in result["quotes"]["quote"]:
        time_str = datetime.strptime(quote["datetime"], "%Y-%m-%dT%H:%M:%SZ") \
            .replace(tzinfo=timezone("UTC")).astimezone(timezone("US/Eastern")) \
            .strftime("%Y%m%d%H%M")
        f.write("%s,%s,%s\n" % (ticker, time_str, float(quote["last"])))
    f.close()


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-d", "--date", dest="date",
                      help="date to get historical data for: YYYYMMDD")
    parser.add_option("-t", "--ticker", dest="ticker",
                      help="ticker symbol")

    options, args = parser.parse_args()
    day = datetime.strptime(options.date, "%Y%m%d")
    gen_historical(options.ticker, day)
