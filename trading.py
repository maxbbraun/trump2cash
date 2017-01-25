# -*- coding: utf-8 -*-

from simplejson import loads
from oauth2 import Consumer
from oauth2 import Client
from oauth2 import Token
from os import getenv
from lxml.etree import Element
from lxml.etree import SubElement
from lxml.etree import tostring

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

# Blacklsited stock ticker symbols, e.g. to avoid insider trading.
TICKER_BLACKLIST = ["GOOG", "GOOGL"]


class Trading:
    """A helper for making stock trades."""

    def __init__(self, logs_to_cloud=True):
        self.logs = Logs(name="trading", to_cloud=logs_to_cloud)

    def make_trades(self, companies):
        """Executes trades for the specified companies based on sentiment."""

        # TODO: Figure out some strategy for the markets closed case.
        # We don't attempt to place orders while the markets are closed,
        # because we can't place the matching on close orders.
        if not self.get_markets_open_now():
            self.logs.warn("Markets are closed.")
            return False

        # Make sure we can trade the companies.
        tradable_companies = self.filter_companies(companies)

        if not tradable_companies:
            self.logs.warn("No companies for trading.")
            return False

        # Calculate the budget per company.
        balance = self.get_balance()
        budget = self.get_budget(balance, tradable_companies)

        if not budget:
            self.logs.warn("No budget for trading: %s %s %s" %
                           (budget, balance, tradable_companies))
            return False

        self.logs.debug("Using budget: %s x $%s" % (len(companies), budget))

        # Handle trades for each company.
        success = True
        for company in tradable_companies:
            ticker = company["ticker"]

            # TODO: Use limits for orders.
            # Buy if the sentiment was positive, otherwise sell short.
            if company["sentiment"] > 0:
                self.logs.debug("Bull: %s" % company)
                success = success and self.bull(ticker, budget)
            else:
                self.logs.debug("Bear: %s" % company)
                success = success and self.bear(ticker, budget)

        return success

    def filter_companies(self, companies):
        """Filters the companies based on the blacklist and available sentiment.
        """

        tradable_companies = []

        for company in companies:
            sentiment = company["sentiment"]
            if not sentiment or sentiment == 0:
                self.logs.warn(
                    "Not trading company due to sentiment: %s" % company)
                continue

            ticker = company["ticker"]
            if not ticker or ticker in TICKER_BLACKLIST:
                self.logs.warn(
                    "Not trading company due to blacklist: %s" % company)
                continue

            tradable_companies.append(company)

        return tradable_companies

    def get_budget(self, balance, companies):
        """Calculates the budget per company based on the available balance."""

        if not companies:
            return 0.0
        return round(max(0.0, balance - CASH_HOLD) / len(companies), 2)

    def get_markets_open_now(self):
        """Finds out whether the markets are open right now."""

        clock_url = TRADEKING_API_URL % "market/clock"
        response = self.make_request(url=clock_url)

        if not response or "response" not in response:
            self.logs.error("Missing clock response: %s" % response)
            return False

        clock_response = response["response"]
        if ("status" not in clock_response or
            "current" not in clock_response["status"]):
            self.logs.error("Malformed clock response: %s" % clock_response)
            return False

        # We consider both regular hours and extended pre market hours, but not
        # closed or extended after market.
        current = clock_response["status"]["current"]
        self.logs.debug("Current market status: %s" % current)
        return (current == "open" or current == "pre")

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

        if not response or "response" not in response:
            self.logs.error("Missing balances response: %s" % response)
            return 0.0

        balances = response["response"]
        if ("accountbalance" not in balances or
            "money" not in balances["accountbalance"] or
            "cash" not in balances["accountbalance"]["money"] or
            "uncleareddeposits" not in balances["accountbalance"]["money"]):
            self.logs.error("Malformed balance response: %s" % balances)
            return 0.0

        money = balances["accountbalance"]["money"]
        try:
            cash = float(money["cash"])
            uncleareddeposits = float(money["uncleareddeposits"])
            return cash - uncleareddeposits
        except ValueError:
            self.logs.error("Malformed number in response: %s" % money)
            return 0.0

    def get_last_price(self, ticker):
        """Finds the last trade price for the specified stock."""

        quotes_url = TRADEKING_API_URL % "market/ext/quotes"
        quotes_url += "?symbols=%s" % ticker
        quotes_url += "&fids=last,date,symbol,exch_desc,name"

        response = self.make_request(url=quotes_url)

        if not response or "response" not in response:
            self.logs.error("Missing quotes response for %s: %s" %
                            (ticker, response))
            return None

        quotes = response["response"]
        if (not quotes or "quotes" not in quotes or
            "quote" not in quotes["quotes"]):
            self.logs.error("Malformed quotes response for %s: %s" %
                            (ticker, quotes_response))
            return None

        quote = quotes["quotes"]["quote"]
        self.logs.debug("Quote for %s: %s" % (ticker, quote))
        if not "last" in quote:
            self.logs.error("Malformed quote for %s: %s" % (ticker, quote))
            return None

        try:
            last = float(quote["last"])
        except ValueError:
            self.logs.error("Malformed last for %s: %s" % (ticker, quote["last"]))
            return None

        if last > 0:
            return last
        else:
            self.logs.error("Zero quote for: %s" % ticker)
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
        if not self.make_order_request(sell_fixml):
            return False

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
        if not self.make_order_request(cover_fixml):
            return False

        return True

    def make_order_request(self, fixml):
        """Executes an order defined by FIXML and verifies the response."""

        response = self.make_request(url=self.get_order_url(), method="POST",
                                     body=fixml, headers=FIXML_HEADERS)

        # Check if there is a response.
        if not response or "response" not in response:
            self.logs.error("Order request failed: %s %s" % (fixml, response))
            return False

        # Check if the response is in the expected format.
        order_response = response["response"]
        if not order_response or "error" not in order_response:
            self.logs.error("Malformed order response: %s" % order_response)
            return False

        # The error field indicates whether the order succeeded.
        error = order_response["error"]
        if error != "Success":
            self.logs.error("Error in order response: %s %s" %
                            (error, order_response))
            return False

        return True

#
# Tests
#

import pytest


@pytest.fixture
def trading():
    return Trading(logs_to_cloud=False)


def test_environment_variables():
    assert TRADEKING_CONSUMER_KEY
    assert TRADEKING_CONSUMER_SECRET
    assert TRADEKING_ACCESS_TOKEN
    assert TRADEKING_ACCESS_TOKEN_SECRET
    assert TRADEKING_ACCOUNT_NUMBER
    assert not USE_REAL_MONEY


def test_filter_companies_none(trading):
    assert trading.filter_companies([{
        "name": "Ford",
        "sentiment": 0.3,
        "ticker": "F"}, {
        "name": "Fiat",
        "root": "Fiat Chrysler Automobiles",
        "sentiment": 0.3,
        "ticker": "FCAU"}]) == [{
            "name": "Ford",
            "sentiment": 0.3,
            "ticker": "F"}, {
            "name": "Fiat",
            "root": "Fiat Chrysler Automobiles",
            "sentiment": 0.3,
            "ticker": "FCAU"}]


def test_filter_companies_blacklist(trading):
    assert trading.filter_companies([{
        "name": "General Motors",
        "sentiment": 0.4,
        "ticker": "GM"}, {
        "name": "Google",
        "sentiment": 0.4,
        "ticker": "GOOG"}, {
        "name": "Google",
        "sentiment": 0.4,
        "ticker": "GOOGL"}]) == [{
            "name": "General Motors",
            "sentiment": 0.4,
            "ticker": "GM"}]


def test_filter_companies_sentiment(trading):
    assert trading.filter_companies([{
        "name": "Ford",
        "sentiment": 0.0,
        "ticker": "F"}, {
        "name": "Fiat",
        "root": "Fiat Chrysler Automobiles",
        "sentiment": 0.3,
        "ticker": "FCAU"}]) == [{
            "name": "Fiat",
            "root": "Fiat Chrysler Automobiles",
            "sentiment": 0.3,
            "ticker": "FCAU"}]


def test_get_budget(trading):
    assert trading.get_budget(11000.0, [{
        "name": "General Motors",
        "sentiment": -0.1,
        "ticker": "GM"}]) == 10000.0
    assert trading.get_budget(11000.0, [{
        "name": "Ford",
        "sentiment": 0.3,
        "ticker": "F"}, {
        "name": "Fiat",
        "root": "Fiat Chrysler Automobiles",
        "sentiment": 0.3,
        "ticker": "FCAU"}]) == 5000.0
    assert trading.get_budget(11000.0, [{
        "name": "General Motors",
        "sentiment": 0.4,
        "ticker": "GM"}, {
        "name": "Walmart",
        "sentiment": 0.4,
        "ticker": "WMT"}, {
        "name": "Walmart",
        "root": "State Street Corporation",
        "sentiment": 0.4,
        "ticker": "STT"}]) == 3333.33
    assert trading.get_budget(11000.0, []) == 0.0


def test_make_request_success(trading):
    url = "https://api.tradeking.com/v1/member/profile.json"
    response = trading.make_request(url=url)
    assert response is not None
    account = response["response"]["userdata"]["account"]["account"]
    assert account == TRADEKING_ACCOUNT_NUMBER
    assert response["response"]["error"] == "Success"


def test_make_request_fail(trading):
    url = "https://api.tradeking.com/v1/member/profile.xml"
    response = trading.make_request(url=url)
    assert response is None


def test_fixml_buy_now(trading):
    assert trading.fixml_buy_now("GM", 23) == (
        '<FIXML xmlns="http://www.fixprotocol.org/FIXML-5-0-SP2">'
        '<Order TmInForce="0" Typ="1" Side="1" Acct="%s">'
        '<Instrmt SecTyp="CS" Sym="GM"/>'
        '<OrdQty Qty="23"/>'
        '</Order>'
        '</FIXML>' % TRADEKING_ACCOUNT_NUMBER)


def test_fixml_sell_eod(trading):
    assert trading.fixml_sell_eod("GM", 23) == (
        '<FIXML xmlns="http://www.fixprotocol.org/FIXML-5-0-SP2">'
        '<Order TmInForce="7" Typ="1" Side="2" Acct="%s">'
        '<Instrmt SecTyp="CS" Sym="GM"/>'
        '<OrdQty Qty="23"/>'
        '</Order>'
        '</FIXML>' % TRADEKING_ACCOUNT_NUMBER)


def test_fixml_short_now(trading):
    assert trading.fixml_short_now("GM", 23) == (
        '<FIXML xmlns="http://www.fixprotocol.org/FIXML-5-0-SP2">'
        '<Order TmInForce="0" Typ="1" Side="5" Acct="%s">'
        '<Instrmt SecTyp="CS" Sym="GM"/>'
        '<OrdQty Qty="23"/>'
        '</Order>'
        '</FIXML>' % TRADEKING_ACCOUNT_NUMBER)


def test_fixml_cover_eod(trading):
    assert trading.fixml_cover_eod("GM", 23) == (
        '<FIXML xmlns="http://www.fixprotocol.org/FIXML-5-0-SP2">'
        '<Order TmInForce="7" Typ="1" Side="1" AcctTyp="5" Acct="%s">'
        '<Instrmt SecTyp="CS" Sym="GM"/>'
        '<OrdQty Qty="23"/>'
        '</Order>'
        '</FIXML>' % TRADEKING_ACCOUNT_NUMBER)


def test_get_balance(trading):
    assert trading.get_balance() > 0.0


def test_get_last_price(trading):
    assert trading.get_last_price("GM") > 0.0
    assert trading.get_last_price("GOOG") > 0.0
    assert trading.get_last_price("$NAP") is None
    assert trading.get_last_price("") is None


def test_get_markets_open_now(trading):
    # This avoids test failures when markets are closed while still exercising
    # the code paths. TODO: Find a better way.
    assert (trading.get_markets_open_now() or
            not trading.get_markets_open_now())


def test_get_order_url(trading):
    assert trading.get_order_url() == (
        "https://api.tradeking.com/v1/accounts/%s/"
        "orders/preview.json") % TRADEKING_ACCOUNT_NUMBER


def test_get_quantity(trading):
    assert trading.get_quantity("F", 10000.0) > 0


def test_make_order_request_success(trading):
    assert not USE_REAL_MONEY
    assert trading.make_order_request((
        '<FIXML xmlns="http://www.fixprotocol.org/FIXML-5-0-SP2">'
        '<Order TmInForce="0" Typ="1" Side="1" Acct="%s">'
        '<Instrmt SecTyp="CS" Sym="GM"/>'
        '<OrdQty Qty="23"/>'
        '</Order>'
        '</FIXML>' % TRADEKING_ACCOUNT_NUMBER))


def test_make_order_request_fail(trading):
    assert not USE_REAL_MONEY
    assert not trading.make_order_request("<FIXML\>")


def test_bull(trading):
    assert not USE_REAL_MONEY
    # TODO: Find a way to test while the markets are closed and how to test sell
    #        short orders without holding the stock.
    #assert trading.bull("F", 10000.0)


def test_bear(trading):
    assert not USE_REAL_MONEY
    # TODO: Find a way to test while the markets are closed and how to test sell
    #        short orders without holding the stock.
    #assert trading.bear("F", 10000.0)


def test_make_trades_success(trading):
    assert not USE_REAL_MONEY
    # TODO: Find a way to test while the markets are closed and how to test sell
    #        short orders without holding the stock.
    #assert trading.make_trades([{
    #    "name": "Lockheed Martin",
    #    "sentiment": -0.1,
    #    "ticker": "LMT"}, {
    #    "name": "Boeing",
    #    "sentiment": 0.1,
    #    "ticker": "BA"}])


def test_make_trades_fail(trading):
    assert not USE_REAL_MONEY
    assert not trading.make_trades([{
        "name": "Boeing",
        "sentiment": 0,
        "ticker": "BA"}])
