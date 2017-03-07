# -*- coding: utf-8 -*-

from pytest import fixture
from threading import Timer
from time import sleep

from twitter import Twitter
from twitter import TWITTER_CONSUMER_KEY
from twitter import TWITTER_CONSUMER_SECRET
from twitter import TWITTER_ACCESS_TOKEN
from twitter import TWITTER_ACCESS_TOKEN_SECRET


@fixture
def twitter():
    return Twitter(logs_to_cloud=False)


def test_environment_variables():
    assert TWITTER_CONSUMER_KEY
    assert TWITTER_CONSUMER_SECRET
    assert TWITTER_ACCESS_TOKEN
    assert TWITTER_ACCESS_TOKEN_SECRET


def callback(tweet):
    # TODO: Test the callback without relying on Trump tweets.
    assert tweet


def test_streaming(twitter):
    # Let the stream run for two seconds and run it again after a pause.
    Timer(2, twitter.stop_streaming).start()
    twitter.start_streaming(callback)
    sleep(2)
    Timer(2, twitter.stop_streaming).start()
    twitter.start_streaming(callback)


def test_make_tweet_text(twitter):
    assert twitter.make_tweet_text([{
        "name": "Boeing",
        "sentiment": -0.1,
        "ticker": "BA"}],
        "https://twitter.com/realDonaldTrump/status/806134244384899072") == (
        u"Boeing \U0001f44e $BA\n"
        "https://twitter.com/realDonaldTrump/status/806134244384899072")
    assert twitter.make_tweet_text([{
        "name": "Ford",
        "sentiment": 0.3,
        "ticker": "F"}, {
        "name": "Fiat",
        "root": "Fiat Chrysler Automobiles",
        "sentiment": 0.3,
        "ticker": "FCAU"}],
        "https://twitter.com/realDonaldTrump/status/818461467766824961") == (
        u"Ford \U0001f44d $F\n"
        u"Fiat \U0001f44d $FCAU\n"
        "https://twitter.com/realDonaldTrump/status/818461467766824961")
    assert twitter.make_tweet_text([{
        "name": "Lockheed Martin",
        "sentiment": -0.1,
        "ticker": "LMT"}, {
        "name": "Boeing",
        "sentiment": 0.1,
        "ticker": "BA"}],
        "https://twitter.com/realDonaldTrump/status/812061677160202240") == (
        u"Lockheed Martin \U0001f44e $LMT\n"
        u"Boeing \U0001f44d $BA\n"
        "https://twitter.com/realDonaldTrump/status/812061677160202240")
    assert twitter.make_tweet_text([{
        "name": "General Motors",
        "sentiment": 0,
        "ticker": "GM"}],
        "https://twitter.com/realDonaldTrump/status/821697182235496450") == (
        u"General Motors ¯\_(\u30c4)_/¯ $GM\n"
        "https://twitter.com/realDonaldTrump/status/821697182235496450")
    assert twitter.make_tweet_text([{
        "ticker": "XOM",
        "name": "ExxonMobil",
        "sentiment": 0.5,
        "exchange": "New York Stock Exchange"}, {
        "root": "BlackRock",
        "ticker": "BLK",
        "name": "ExxonMobil",
        "sentiment": 0.5,
        "exchange": "New York Stock Exchange"}, {
        "root": "PNC Financial Services",
        "ticker": "PNC",
        "name": "ExxonMobil",
        "sentiment": 0.5,
        "exchange": "New York Stock Exchange"}, {
        "root": "State Street Corporation",
        "ticker": "STT",
        "name": "ExxonMobil",
        "sentiment": 0.5,
        "exchange": "New York Stock Exchange"}],
        "https://twitter.com/realDonaldTrump/status/838862131852369922") == (
        u"ExxonMobil \U0001f44d $XOM $BLK $PNC $STT\n"
        "https://twitter.com/realDonaldTrump/status/838862131852369922")
    assert twitter.make_tweet_text([{
        "ticker": "GM",
        "name": "General Motors",
        "sentiment": 0.4,
        "exchange": "New York Stock Exchange"}, {
        "ticker": "WMT",
        "name": "Walmart",
        "sentiment": 0.4,
        "exchange": "New York Stock Exchange"}, {
        "root": "State Street Corporation",
        "ticker": "STT",
        "name": "Walmart",
        "sentiment": 0.4,
        "exchange": "New York Stock Exchange"}],
        "https://twitter.com/realDonaldTrump/status/821415698278875137") == (
        u"General Motors \U0001f44d $GM\n"
        u"Walmart \U0001f44d $WMT $STT\n"
        "https://twitter.com/realDonaldTrump/status/821415698278875137")
    assert twitter.make_tweet_text([{
        "ticker": chr(i - 32),
        "name": chr(i),
        "sentiment": 0} for i in range(97, 123)],
        "https://twitter.com/realDonaldTrump/status/0") == (
        u"a ¯\_(\u30c4)_/¯ $A\n"
        u"b ¯\_(\u30c4)_/¯ $B\n"
        u"c ¯\_(\u30c4)_/¯ $C\n"
        u"d ¯\_(\u30c4)_/¯ $D\n"
        u"e ¯\_(\u30c4)_/¯ $E\n"
        u"f ¯\_(\u30c4)_/¯ $F\n"
        u"g ¯\\\u2026\n"
        "https://twitter.com/realDonaldTrump/status/0")


def test_get_sentiment_emoji(twitter):
    assert twitter.get_sentiment_emoji(0.5) == u"\U0001f44d"
    assert twitter.get_sentiment_emoji(-0.5) == u"\U0001f44e"
    assert twitter.get_sentiment_emoji(0) == u"¯\_(\u30c4)_/¯"
    assert twitter.get_sentiment_emoji(None) == u"¯\_(\u30c4)_/¯"


def test_get_tweet(twitter):
    tweet = twitter.get_tweet("806134244384899072")
    assert tweet["text"] == (
        "Boeing is building a brand new 747 Air Force One for future president"
        "s, but costs are out of control, more than $4 billion. Cancel order!")
    assert tweet["id_str"] == "806134244384899072"
    assert tweet["user"]["id_str"] == "25073877"
    assert tweet["user"]["screen_name"] == "realDonaldTrump"
    assert tweet["created_at"] == "Tue Dec 06 13:52:35 +0000 2016"


def test_get_tweets(twitter):
    # TODO: Test without relying on latest tweets.
    pass


def test_get_tweet_link(twitter):
    tweet = twitter.get_tweet("828574430800539648")
    assert twitter.get_tweet_link(tweet) == (
        "https://twitter.com/realDonaldTrump/status/828574430800539648")
