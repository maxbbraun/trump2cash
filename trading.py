# -*- coding: utf-8 -*-

from datetime import datetime
from datetime import timedelta
from holidays import UnitedStates
from lxml.etree import Element
from lxml.etree import SubElement
from lxml.etree import tostring
from oauth2 import Consumer
from oauth2 import Client
from oauth2 import Token
from os import getenv
from os import path
from pytz import timezone
from pytz import utc
from simplejson import loads
from threading import Timer

from logs import Logs

# Read the authentication keys for TradeKing from environment variables.
TRADEKING_CONSUMER_KEY = getenv("TRADEKING_CONSUMER_KEY")
TRADEKING_CONSUMER_SECRET = getenv("TRADEKING_CONSUMER_SECRET")
TRADEKING_ACCESS_TOKEN = getenv("TRADEKING_ACCESS_TOKEN")
TRADEKING_ACCESS_TOKEN_SECRET = getenv("TRADEKING_ACCESS_TOKEN_SECRET")

# Read the TradeKing account number from the environment variable.
TRADEKING_ACCOUNT_NUMBER = getenv("TRADEKING_ACCOUNT_NUMBER")

# Only allow actual trades when the environment variable confirms it.
USE_REAL_MONEY = getenv("USE_REAL_MONEY") == "YES"

# The base URL for API requests to TradeKing.
TRADEKING_API_URL = "https://api.tradeking.com/v1/%s.json"

# The XML namespace for FIXML requests.
FIXML_NAMESPACE = "http://www.fixprotocol.org/FIXML-5-0-SP2"

# The HTTP headers for FIXML requests.
FIXML_HEADERS = {"Content-Type": "text/xml"}

# The amount of cash in dollars to hold from being spent.
CASH_HOLD = 1000

# The delay in seconds for the second leg of a trade.
ORDER_DELAY_S = 5 * 60

# Blacklsited stock ticker symbols, e.g. to avoid insider trading.
TICKER_BLACKLIST = ["GOOG", "GOOGL"]

# We're using NYSE and NASDAQ, which are both in the easters timezone.
MARKET_TIMEZONE = timezone("US/Eastern")

# The filename pattern for historical market data.
MARKET_DATA_FILE = "market_data/%s_%s.txt"


class Trading:
    """A helper for making stock trades."""

    def __init__(self, logs_to_cloud):
        self.logs = Logs(name="trading", to_cloud=logs_to_cloud)

    def make_trades(self, companies):
        """Executes trades for the specified companies based on sentiment."""

        # Determine whether the markets are open.
        market_status = self.get_market_status()
        if not market_status:
            self.logs.error("Not trading without market status.")
            return False

        # Filter for any strategies resulting in trades.
        actionable_strategies = []
        market_status = self.get_market_status()
        for company in companies:
            strategy = self.get_strategy(company, market_status)
            if strategy["action"] != "hold":
                actionable_strategies.append(strategy)
            else:
                self.logs.warn("Dropping strategy: %s" % strategy)

        if not actionable_strategies:
            self.logs.warn("No actionable strategies for trading.")
            return False

        # Calculate the budget per strategy.
        balance = self.get_balance()
        budget = self.get_budget(balance, len(actionable_strategies))

        if not budget:
            self.logs.warn("No budget for trading: %s %s %s" %
                           (budget, balance, actionable_strategies))
            return False

        self.logs.debug("Using budget: %s x $%s" %
                        (len(actionable_strategies), budget))

        # Handle trades for each strategy.
        success = True
        for strategy in actionable_strategies:
            ticker = strategy["ticker"]
            action = strategy["action"]

            # TODO: Use limits for orders.
            # Execute the strategy.
            if action == "bull":
                self.logs.debug("Bull: %s %s" % (ticker, budget))
                success = success and self.bull(ticker, budget)
            elif action == "bear":
                self.logs.debug("Bear: %s %s" % (ticker, budget))
                success = success and self.bear(ticker, budget)
            else:
                self.logs.error("Unknown strategy: %s" % strategy)

        return success

    def get_strategy(self, company, market_status):
        """Determines the strategy for trading a company based on sentiment and
        market status.
        """

        ticker = company["ticker"]
        sentiment = company["sentiment"]

        strategy = {}
        strategy["name"] = company["name"]
        if "root" in company:
            strategy["root"] = company["root"]
        strategy["sentiment"] = company["sentiment"]
        strategy["ticker"] = ticker
        strategy["exchange"] = company["exchange"]

        # Don't do anything with blacklisted stocks.
        if ticker in TICKER_BLACKLIST:
            strategy["action"] = "hold"
            strategy["reason"] = "blacklist"
            return strategy

        # TODO: Figure out some strategy for the markets closed case.
        # Don't trade unless the markets are open or are about to open.
        if market_status != "open" and market_status != "pre":
            strategy["action"] = "hold"
            strategy["reason"] = "market closed"
            return strategy

        # Can't trade without sentiment.
        if sentiment == 0:
            strategy["action"] = "hold"
            strategy["reason"] = "neutral sentiment"
            return strategy

        # Determine bull or bear based on sentiment direction.
        if sentiment > 0:
            strategy["action"] = "bull"
            strategy["reason"] = "positive sentiment"
            return strategy
        else:  # sentiment < 0
            strategy["action"] = "bear"
            strategy["reason"] = "negative sentiment"
            return strategy

    def get_budget(self, balance, num_strategies):
        """Calculates the budget per company based on the available balance."""

        if num_strategies <= 0:
            self.logs.warn("No budget without strategies.")
            return 0.0
        return round(max(0.0, balance - CASH_HOLD) / num_strategies, 2)

    def get_market_status(self):
        """Finds out whether the markets are open right now."""

        clock_url = TRADEKING_API_URL % "market/clock"
        response = self.make_request(url=clock_url)

        if not response:
            self.logs.error("No clock response.")
            return None

        try:
            clock_response = response["response"]
            current = clock_response["status"]["current"]
        except KeyError:
            self.logs.error("Malformed clock response: %s" % response)
            return None

        if current not in ["pre", "open", "after", "close"]:
            self.logs.error("Unknown market status: %s" % current)
            return None

        self.logs.debug("Current market status: %s" % current)
        return current

    def get_historical_prices(self, ticker, timestamp):
        """Finds the last price at or before a timestamp and at EOD."""

        # Start with today's quotes.
        quotes = self.get_day_quotes(ticker, timestamp)
        if not quotes:
            self.logs.warn("No quotes for day: %s" % timestamp)
            return None

        # Depending on where we land relative to the trading day, pick the
        # right quote and EOD quote.
        first_quote = quotes[0]
        first_quote_time = first_quote["time"]
        last_quote = quotes[-1]
        last_quote_time = last_quote["time"]
        if timestamp < first_quote_time:
            self.logs.debug("Using previous quote.")
            previous_day = self.get_previous_day(timestamp)
            previous_quotes = self.get_day_quotes(ticker, previous_day)
            if not previous_quotes:
                self.logs.error("No quotes for previous day: %s" %
                                previous_day)
                return None
            quote_at = previous_quotes[-1]
            quote_eod = last_quote
        elif timestamp >= first_quote_time and timestamp <= last_quote_time:
            self.logs.debug("Using closest quote.")
            # Walk through the quotes unitl we stepped over the timestamp.
            previous_quote = first_quote
            for quote in quotes:
                quote_time = quote["time"]
                if quote_time > timestamp:
                    break
                previous_quote = quote
            quote_at = previous_quote
            quote_eod = last_quote
        else:  # timestamp > last_quote_time
            self.logs.debug("Using last quote.")
            quote_at = last_quote
            next_day = self.get_next_day(timestamp)
            next_quotes = self.get_day_quotes(ticker, next_day)
            if not next_quotes:
                self.logs.error("No quotes for next day: %s" % next_day)
                return None
            quote_eod = next_quotes[-1]

        self.logs.debug("Using quotes: %s %s" % (quote_at, quote_eod))
        return {"at": quote_at["price"], "eod": quote_eod["price"]}

    def get_day_quotes(self, ticker, timestamp):
        """Collects all quotes from the day of the market timestamp."""

        # The timestamp is expected in market time.
        day = timestamp.strftime("%Y%m%d")
        filename = MARKET_DATA_FILE % (ticker, day)

        if not path.isfile(filename):
            self.logs.error("Day quotes not on file for: %s %s" %
                            (ticker, timestamp))
            return None

        quotes_file = open(filename, "r")
        try:
            lines = quotes_file.readlines()
            quotes = []

            # Skip the header line, then read the quotes.
            for line in lines[1:]:
                columns = line.split(",")

                market_time_str = columns[1]
                try:
                    market_time = MARKET_TIMEZONE.localize(datetime.strptime(
                        market_time_str, "%Y%m%d%H%M"))
                except ValueError:
                    self.logs.error("Failed to decode market time: %s" %
                                    market_time_str)
                    return None

                price_str = columns[2]
                try:
                    price = float(price_str)
                except ValueError:
                    self.logs.error("Failed to decode price: %s" % price_str)
                    return None

                quote = {"time": market_time, "price": price}
                quotes.append(quote)

            return quotes
        except IOError as exception:
            self.logs.error("Failed to read quotes cache file: %s" % exception)
            return None
        finally:
            quotes_file.close()

    def is_trading_day(self, timestamp):
        """Tests whether markets are open on a given day."""

        # Markets are closed on holidays.
        if timestamp in UnitedStates():
            self.logs.debug("Identified holiday: %s" % timestamp)
            return False

        # Markets are closed on weekends.
        if timestamp.weekday() in [5, 6]:
            self.logs.debug("Identified weekend: %s" % timestamp)
            return False

        # Otherwise markets are open.
        return True

    def get_previous_day(self, timestamp):
        """Finds the previous trading day."""

        previous_day = timestamp - timedelta(days=1)

        # Walk backwards until we hit a trading day.
        while not self.is_trading_day(previous_day):
            previous_day -= timedelta(days=1)

        self.logs.debug("Previous trading day for %s: %s" %
                        (timestamp, previous_day))
        return previous_day

    def get_next_day(self, timestamp):
        """Finds the next trading day."""

        next_day = timestamp + timedelta(days=1)

        # Walk forward until we hit a trading day.
        while not self.is_trading_day(next_day):
            next_day += timedelta(days=1)

        self.logs.debug("Next trading day for %s: %s" %
                        (timestamp, next_day))
        return next_day

    def utc_to_market_time(self, timestamp):
        """Converts a UTC timestamp to local market time."""

        utc_time = utc.localize(timestamp)
        market_time = utc_time.astimezone(MARKET_TIMEZONE)

        return market_time

    def market_time_to_utc(self, timestamp):
        """Converts a timestamp in local market time to UTC."""

        market_time = MARKET_TIMEZONE.localize(timestamp)
        utc_time = market_time.astimezone(utc)

        return utc_time

    def as_market_time(self, year, month, day, hour=0, minute=0, second=0):
        """Creates a timestamp in market time."""

        market_time = datetime(year, month, day, hour, minute, second)
        return MARKET_TIMEZONE.localize(market_time)

    def make_request(self, url, method="GET", body="", headers=None):
        """Makes a request to the TradeKing API."""

        consumer = Consumer(key=TRADEKING_CONSUMER_KEY,
                            secret=TRADEKING_CONSUMER_SECRET)
        token = Token(key=TRADEKING_ACCESS_TOKEN,
                      secret=TRADEKING_ACCESS_TOKEN_SECRET)
        client = Client(consumer, token)

        self.logs.debug("TradeKing request: %s %s %s %s" %
                        (url, method, body, headers))
        response, content = client.request(url, method=method, body=body,
                                           headers=headers)
        self.logs.debug("TradeKing response: %s %s" % (response, content))

        try:
            return loads(content)
        except ValueError:
            self.logs.error("Failed to decode JSON response: %s" % content)
            return None

    def fixml_buy_now(self, ticker, quantity):
        """Generates the FIXML for a buy order at market price."""

        fixml = Element("FIXML")
        fixml.set("xmlns", FIXML_NAMESPACE)
        order = SubElement(fixml, "Order")
        order.set("TmInForce", "0")  # Day order
        order.set("Typ", "1")  # Market price
        order.set("Side", "1")  # Buy
        order.set("Acct", TRADEKING_ACCOUNT_NUMBER)
        instrmt = SubElement(order, "Instrmt")
        instrmt.set("SecTyp", "CS")  # Common stock
        instrmt.set("Sym", ticker)
        ord_qty = SubElement(order, "OrdQty")
        ord_qty.set("Qty", str(quantity))

        return tostring(fixml)

    def fixml_sell_eod(self, ticker, quantity):
        """Generates the FIXML for a sell order at market price on close."""

        fixml = Element("FIXML")
        fixml.set("xmlns", FIXML_NAMESPACE)
        order = SubElement(fixml, "Order")
        order.set("TmInForce", "7")  # Market on close
        order.set("Typ", "1")  # Market price
        order.set("Side", "2")  # Sell
        order.set("Acct", TRADEKING_ACCOUNT_NUMBER)
        instrmt = SubElement(order, "Instrmt")
        instrmt.set("SecTyp", "CS")  # Common stock
        instrmt.set("Sym", ticker)
        ord_qty = SubElement(order, "OrdQty")
        ord_qty.set("Qty", str(quantity))

        return tostring(fixml)

    def fixml_short_now(self, ticker, quantity):
        """Generates the FIXML for a sell short order at market price."""

        fixml = Element("FIXML")
        fixml.set("xmlns", FIXML_NAMESPACE)
        order = SubElement(fixml, "Order")
        order.set("TmInForce", "0")  # Day order
        order.set("Typ", "1")  # Market price
        order.set("Side", "5")  # Sell short
        order.set("Acct", TRADEKING_ACCOUNT_NUMBER)
        instrmt = SubElement(order, "Instrmt")
        instrmt.set("SecTyp", "CS")  # Common stock
        instrmt.set("Sym", ticker)
        ord_qty = SubElement(order, "OrdQty")
        ord_qty.set("Qty", str(quantity))

        return tostring(fixml)

    def fixml_cover_eod(self, ticker, quantity):
        """Generates the FIXML for a sell to cover order at market close."""

        fixml = Element("FIXML")
        fixml.set("xmlns", FIXML_NAMESPACE)
        order = SubElement(fixml, "Order")
        order.set("TmInForce", "7")  # Market on close
        order.set("Typ", "1")  # Market price
        order.set("Side", "1")  # Buy
        order.set("AcctTyp", "5")  # Cover
        order.set("Acct", TRADEKING_ACCOUNT_NUMBER)
        instrmt = SubElement(order, "Instrmt")
        instrmt.set("SecTyp", "CS")  # Common stock
        instrmt.set("Sym", ticker)
        ord_qty = SubElement(order, "OrdQty")
        ord_qty.set("Qty", str(quantity))

        return tostring(fixml)

    def get_balance(self):
        """Finds the cash balance in dollars available to spend."""

        balances_url = TRADEKING_API_URL % (
            "accounts/%s" % TRADEKING_ACCOUNT_NUMBER)
        response = self.make_request(url=balances_url)

        if not response:
            self.logs.error("No balances response.")
            return 0

        try:
            balances = response["response"]
            money = balances["accountbalance"]["money"]
            cash_str = money["cash"]
            uncleareddeposits_str = money["uncleareddeposits"]
        except KeyError:
            self.logs.error("Malformed balances response: %s" % response)
            return 0

        try:
            cash = float(cash_str)
            uncleareddeposits = float(uncleareddeposits_str)
            return cash - uncleareddeposits
        except ValueError:
            self.logs.error("Malformed number in response: %s" % money)
            return 0

    def get_last_price(self, ticker):
        """Finds the last trade price for the specified stock."""

        quotes_url = TRADEKING_API_URL % "market/ext/quotes"
        quotes_url += "?symbols=%s" % ticker
        quotes_url += "&fids=last,date,symbol,exch_desc,name"

        response = self.make_request(url=quotes_url)

        if not response:
            self.logs.error("No quotes response for %s: %s" %
                            (ticker, response))
            return None

        try:
            quotes = response["response"]
            quote = quotes["quotes"]["quote"]
            last_str = quote["last"]
        except KeyError:
            self.logs.error("Malformed quotes response: %s" % response)
            return None

        self.logs.debug("Quote for %s: %s" % (ticker, quote))

        try:
            last = float(last_str)
        except ValueError:
            self.logs.error("Malformed last for %s: %s" % (ticker, last_str))
            return None

        if last > 0:
            return last
        else:
            self.logs.error("Bad quote for: %s" % ticker)
            return None

    def get_order_url(self):
        """Gets the TradeKing URL for placing orders."""

        url_path = "accounts/%s/orders" % TRADEKING_ACCOUNT_NUMBER
        if not USE_REAL_MONEY:
            url_path += "/preview"
        return TRADEKING_API_URL % url_path

    def get_quantity(self, ticker, budget):
        """Calculates the quantity of a stock based on the current market price
        and a maximum budget.
        """

        # Calculate the quantity based on the current price and the budget.
        price = self.get_last_price(ticker)
        if not price:
            self.logs.error("Failed to determine price for: %s" % ticker)
            return None

        # Use maximum possible quantity within the budget.
        quantity = int(budget // price)
        self.logs.debug("Determined quantity %s for %s at $%s within $%s." %
                        (quantity, ticker, price, budget))

        # If quantity is too low we can't buy.
        if quantity <= 0:
            return None

        return quantity

    def bull(self, ticker, budget):
        """Executes the bullish strategy on the specified stock within the
        specified budget: Buy now at market rate and sell at market rate at
        close.
        """

        # Calculate the quantity.
        quantity = self.get_quantity(ticker, budget)
        if not quantity:
            self.logs.warn("Not trading without quantity.")
            return False

        # Buy the stock now.
        buy_fixml = self.fixml_buy_now(ticker, quantity)
        if not self.make_order_request(buy_fixml):
            return False

        # Sell the stock at close.
        sell_fixml = self.fixml_sell_eod(ticker, quantity)
        # TODO: Do this properly by checking the order status API and using
        #       retries with exponential backoff.
        # Wait until the previous order has been executed.
        Timer(ORDER_DELAY_S, self.make_order_request, [sell_fixml]).start()

        return True

    def bear(self, ticker, budget):
        """Executes the bearish strategy on the specified stock within the
        specified budget: Sell short at market rate and buy to cover at market
        rate at close.
        """

        # Calculate the quantity.
        quantity = self.get_quantity(ticker, budget)
        if not quantity:
            self.logs.warn("Not trading without quantity.")
            return False

        # Short the stock now.
        short_fixml = self.fixml_short_now(ticker, quantity)
        if not self.make_order_request(short_fixml):
            return False

        # Cover the short at close.
        cover_fixml = self.fixml_cover_eod(ticker, quantity)
        # TODO: Do this properly by checking the order status API and using
        #       retries with exponential backoff.
        # Wait until the previous order has been executed.
        Timer(ORDER_DELAY_S, self.make_order_request, [cover_fixml]).start()

        return True

    def make_order_request(self, fixml):
        """Executes an order defined by FIXML and verifies the response."""

        response = self.make_request(url=self.get_order_url(), method="POST",
                                     body=fixml, headers=FIXML_HEADERS)

        if not response:
            self.logs.error("No order response for: %s" % fixml)
            return False

        try:
            order_response = response["response"]
            error = order_response["error"]
        except KeyError:
            self.logs.error("Malformed order response: %s" % response)
            return False

        # The error field indicates whether the order succeeded.
        error = order_response["error"]
        if error != "Success":
            self.logs.error("Error in order response: %s %s" %
                            (error, order_response))
            return False

        return True
