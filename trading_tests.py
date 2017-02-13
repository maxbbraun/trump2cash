# -*- coding: utf-8 -*-

from datetime import datetime
from pytest import fixture
from pytz import utc

from trading import Trading
from trading import MARKET_TIMEZONE
from trading import TRADEKING_CONSUMER_KEY
from trading import TRADEKING_CONSUMER_SECRET
from trading import TRADEKING_ACCESS_TOKEN
from trading import TRADEKING_ACCESS_TOKEN_SECRET
from trading import TRADEKING_ACCOUNT_NUMBER
from trading import USE_REAL_MONEY


@fixture
def trading():
    return Trading(logs_to_cloud=False)


def as_market_time(year, month, day, hour=0, minute=0, second=0):
    """Creates a timestamp in market time."""

    market_time = datetime(year, month, day, hour, minute, second)
    return MARKET_TIMEZONE.localize(market_time)


def test_environment_variables():
    assert TRADEKING_CONSUMER_KEY
    assert TRADEKING_CONSUMER_SECRET
    assert TRADEKING_ACCESS_TOKEN
    assert TRADEKING_ACCESS_TOKEN_SECRET
    assert TRADEKING_ACCOUNT_NUMBER
    assert not USE_REAL_MONEY


def test_get_strategy_blacklist(trading):
    assert trading.get_strategy({
        "exchange": "NASDAQ",
        "name": "Google",
        "sentiment": 0.4,
        "ticker": "GOOG"}, "open") == {
            "action": "hold",
            "exchange": "NASDAQ",
            "name": "Google",
            "reason": "blacklist",
            "sentiment": 0.4,
            "ticker": "GOOG"}
    assert trading.get_strategy({
        "exchange": "New York Stock Exchange",
        "name": "Ford",
        "sentiment": 0.3,
        "ticker": "F"}, "open") == {
            "action": "bull",
            "exchange": "New York Stock Exchange",
            "name": "Ford",
            "reason": "positive sentiment",
            "sentiment": 0.3,
            "ticker": "F"}


def test_get_strategy_market_status(trading):
    assert trading.get_strategy({
        "exchange": "New York Stock Exchange",
        "name": "General Motors",
        "sentiment": 0.5,
        "ticker": "GM"}, "pre") == {
            "action": "bull",
            "exchange": "New York Stock Exchange",
            "name": "General Motors",
            "reason": "positive sentiment",
            "sentiment": 0.5,
            "ticker": "GM"}
    assert trading.get_strategy({
        "exchange": "New York Stock Exchange",
        "name": "General Motors",
        "sentiment": 0.5,
        "ticker": "GM"}, "open") == {
            "action": "bull",
            "exchange": "New York Stock Exchange",
            "name": "General Motors",
            "reason": "positive sentiment",
            "sentiment": 0.5,
            "ticker": "GM"}
    assert trading.get_strategy({
        "exchange": "New York Stock Exchange",
        "name": "General Motors",
        "sentiment": 0.5,
        "ticker": "GM"}, "after") == {
            "action": "hold",
            "exchange": "New York Stock Exchange",
            "name": "General Motors",
            "reason": "market closed",
            "sentiment": 0.5,
            "ticker": "GM"}
    assert trading.get_strategy({
        "exchange": "New York Stock Exchange",
        "name": "General Motors",
        "sentiment": 0.5,
        "ticker": "GM"}, "close") == {
            "action": "hold",
            "exchange": "New York Stock Exchange",
            "name": "General Motors",
            "reason": "market closed",
            "sentiment": 0.5,
            "ticker": "GM"}


def test_get_strategy_sentiment(trading):
    assert trading.get_strategy({
        "exchange": "New York Stock Exchange",
        "name": "General Motors",
        "sentiment": 0,
        "ticker": "GM"}, "open") == {
            "action": "hold",
            "exchange": "New York Stock Exchange",
            "name": "General Motors",
            "reason": "neutral sentiment",
            "sentiment": 0,
            "ticker": "GM"}
    assert trading.get_strategy({
        "exchange": "New York Stock Exchange",
        "name": "Ford",
        "sentiment": 0.5,
        "ticker": "F"}, "open") == {
            "action": "bull",
            "exchange": "New York Stock Exchange",
            "name": "Ford",
            "reason": "positive sentiment",
            "sentiment": 0.5,
            "ticker": "F"}
    assert trading.get_strategy({
        "exchange": "New York Stock Exchange",
        "name": "Fiat",
        "root": "Fiat Chrysler Automobiles",
        "sentiment": -0.5,
        "ticker": "FCAU"}, "open") == {
            "action": "bear",
            "exchange": "New York Stock Exchange",
            "name": "Fiat",
            "reason": "negative sentiment",
            "root": "Fiat Chrysler Automobiles",
            "sentiment": -0.5,
            "ticker": "FCAU"}


def test_get_budget(trading):
    assert trading.get_budget(11000.0, 1) == 10000.0
    assert trading.get_budget(11000.0, 2) == 5000.0
    assert trading.get_budget(11000.0, 3) == 3333.33
    assert trading.get_budget(11000.0, 0) == 0.0


def test_utc_to_market_time(trading):
    assert trading.utc_to_market_time(datetime(
        2017, 1, 3, 16, 44, 13)) == as_market_time(
        2017, 1, 3, 11, 44, 13)


def test_market_time_to_utc(trading):
    assert trading.market_time_to_utc(datetime(
        2017, 1, 3, 11, 44, 13)) == datetime(
        2017, 1, 3, 16, 44, 13, tzinfo=utc)


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


def test_get_market_status(trading):
    assert trading.get_market_status() in ["pre", "open", "after", "close"]


def test_get_order_url(trading):
    assert trading.get_order_url() == (
        "https://api.tradeking.com/v1/accounts/%s/"
        "orders/preview.json") % TRADEKING_ACCOUNT_NUMBER


def test_get_quantity(trading):
    assert trading.get_quantity("F", 10000.0) > 0


def test_get_historical_prices(trading):
    assert trading.get_historical_prices(
        "F", as_market_time(2017, 1, 24, 19, 46, 57)) == {
            "at": 12.6, "eod": 12.78}
    assert trading.get_historical_prices(
        "GM", as_market_time(2017, 1, 24, 19, 46, 57)) == {
            "at": 37.09, "eod": 38.28}
    assert trading.get_historical_prices(
        "TRP", as_market_time(2017, 1, 24, 12, 49, 17)) == {
            "at": 48.93, "eod": 48.87}
    assert trading.get_historical_prices(
        "BLK", as_market_time(2017, 1, 18, 8, 0, 51)) == {
            "at": 374.8, "eod": 378.0}
    assert trading.get_historical_prices(
        "F", as_market_time(2017, 1, 18, 7, 34, 9)) == {
            "at": 12.6, "eod": 12.41}
    assert trading.get_historical_prices(
        "GM", as_market_time(2017, 1, 18, 7, 34, 9)) == {
            "at": 37.31, "eod": 37.47}
    assert trading.get_historical_prices(
        "LMT", as_market_time(2017, 1, 18, 7, 34, 9)) == {
            "at": 254.12, "eod": 254.07}
    assert trading.get_historical_prices(
        "GM", as_market_time(2017, 1, 17, 12, 55, 38)) == {
            "at": 37.54, "eod": 37.31}
    assert trading.get_historical_prices(
        "STT", as_market_time(2017, 1, 17, 12, 55, 38)) == {
            "at": 81.19, "eod": 80.2}
    assert trading.get_historical_prices(
        "WMT", as_market_time(2017, 1, 17, 12, 55, 38)) == {
            "at": 68.53, "eod": 68.5}
    assert trading.get_historical_prices(
        "F", as_market_time(2017, 1, 9, 9, 16, 34)) == {
            "at": 12.84, "eod": 12.64}
    assert trading.get_historical_prices(
        "FCAU", as_market_time(2017, 1, 9, 9, 16, 34)) == {
            "at": 10.57, "eod": 10.57}
    assert trading.get_historical_prices(
        "FCAU", as_market_time(2017, 1, 9, 9, 14, 10)) == {
            "at": 10.55, "eod": 10.57}
    assert trading.get_historical_prices(
        "TM", as_market_time(2017, 1, 5, 13, 14, 30)) == {
            "at": 121.12, "eod": 120.44}
    assert trading.get_historical_prices(
        "F", as_market_time(2017, 1, 4, 8, 19, 9)) == {
            "at": 12.59, "eod": 13.17}
    assert trading.get_historical_prices(
        "F", as_market_time(2017, 1, 3, 11, 44, 13)) == {
            "at": 12.41, "eod": 12.59}
    assert trading.get_historical_prices(
        "GM", as_market_time(2017, 1, 3, 7, 30, 5)) == {
            "at": 34.84, "eod": 35.15}
    assert trading.get_historical_prices(
        "BA", as_market_time(2016, 12, 22, 17, 26, 5)) == {
            "at": 157.46, "eod": 157.92}
    assert trading.get_historical_prices(
        "BA", as_market_time(2016, 12, 6, 8, 52, 35)) == {
            "at": 152.16, "eod": 152.3}
    assert trading.get_historical_prices(
        "M", as_market_time(2015, 11, 12, 16, 5, 28)) == {
            "at": 40.73, "eod": 40.15}
    assert trading.get_historical_prices(
        "M", as_market_time(2015, 7, 16, 9, 14, 15)) == {
            "at": 71.75, "eod": 72.8}


def test_get_day_quotes(trading):
    quotes = trading.get_day_quotes(
        "BA", as_market_time(2016, 12, 22, 17, 26, 0))
    assert len(quotes) == 395
    assert quotes[0] == {
        "price": 158.73, "time": as_market_time(2016, 12, 22, 9, 3, 0)}
    assert quotes[-1] == {
        "price": 157.46, "time": as_market_time(2016, 12, 22, 16, 30, 0)}


def test_is_trading_day(trading):
    assert not trading.is_trading_day(as_market_time(2017, 1, 22))
    assert trading.is_trading_day(as_market_time(2017, 1, 23))
    assert trading.is_trading_day(as_market_time(2017, 1, 24))
    assert trading.is_trading_day(as_market_time(2017, 1, 25))
    assert trading.is_trading_day(as_market_time(2017, 1, 26))
    assert trading.is_trading_day(as_market_time(2017, 1, 27))
    assert not trading.is_trading_day(as_market_time(2017, 1, 28))
    assert not trading.is_trading_day(as_market_time(2017, 1, 2))


def test_get_previous_day(trading):
    assert trading.get_previous_day(as_market_time(
        2017, 1, 22)) == as_market_time(2017, 1, 20)
    assert trading.get_previous_day(as_market_time(
        2017, 1, 23)) == as_market_time(2017, 1, 20)
    assert trading.get_previous_day(as_market_time(
        2017, 1, 24)) == as_market_time(2017, 1, 23)
    assert trading.get_previous_day(as_market_time(
        2017, 1, 25)) == as_market_time(2017, 1, 24)
    assert trading.get_previous_day(as_market_time(
        2017, 1, 26)) == as_market_time(2017, 1, 25)
    assert trading.get_previous_day(as_market_time(
        2017, 1, 27)) == as_market_time(2017, 1, 26)
    assert trading.get_previous_day(as_market_time(
        2017, 1, 28)) == as_market_time(2017, 1, 27)
    assert trading.get_previous_day(as_market_time(
        2017, 1, 3)) == as_market_time(2016, 12, 30)


def test_get_next_day(trading):
    assert trading.get_next_day(as_market_time(
        2017, 1, 22)) == as_market_time(2017, 1, 23)
    assert trading.get_next_day(as_market_time(
        2017, 1, 23)) == as_market_time(2017, 1, 24)
    assert trading.get_next_day(as_market_time(
        2017, 1, 24)) == as_market_time(2017, 1, 25)
    assert trading.get_next_day(as_market_time(
        2017, 1, 25)) == as_market_time(2017, 1, 26)
    assert trading.get_next_day(as_market_time(
        2017, 1, 26)) == as_market_time(2017, 1, 27)
    assert trading.get_next_day(as_market_time(
        2017, 1, 27)) == as_market_time(2017, 1, 30)
    assert trading.get_next_day(as_market_time(
        2017, 1, 28)) == as_market_time(2017, 1, 30)
    assert trading.get_next_day(as_market_time(
        2016, 12, 30)) == as_market_time(2017, 1, 3)


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
    # TODO: Find a way to test while the markets are closed and how to test
    #       sell short orders without holding the stock.
    # assert trading.bull("F", 10000.0)


def test_bear(trading):
    assert not USE_REAL_MONEY
    # TODO: Find a way to test while the markets are closed and how to test
    #       sell short orders without holding the stock.
    # assert trading.bear("F", 10000.0)


def test_make_trades_success(trading):
    assert not USE_REAL_MONEY
    # TODO: Find a way to test while the markets are closed and how to test
    #       sell short orders without holding the stock.
    # assert trading.make_trades([{
    #     "exchange": "New York Stock Exchange",
    #     "name": "Lockheed Martin",
    #     "sentiment": -0.1,
    #     "ticker": "LMT"}, {
    #     "exchange": "New York Stock Exchange",
    #     "name": "Boeing",
    #     "sentiment": 0.1,
    #     "ticker": "BA"}])


def test_make_trades_fail(trading):
    assert not USE_REAL_MONEY
    assert not trading.make_trades([{
        "exchange": "New York Stock Exchange",
        "name": "Boeing",
        "sentiment": 0,
        "ticker": "BA"}])
