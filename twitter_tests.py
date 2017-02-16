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
        u"Boeing $BA \U0001f44e\n"
        u"https://twitter.com/realDonaldTrump/status/806134244384899072")
    assert twitter.make_tweet_text([{
        "name": "Ford",
        "sentiment": 0.3,
        "ticker": "F"}, {
        "name": "Fiat",
        "root": "Fiat Chrysler Automobiles",
        "sentiment": 0.3,
        "ticker": "FCAU"}],
        "https://twitter.com/realDonaldTrump/status/818461467766824961") == (
        u"Ford $F \U0001f44d\n"
        u"Fiat (Fiat Chrysler Automobiles) $FCAU \U0001f44d\n"
        u"https://twitter.com/realDonaldTrump/status/818461467766824961")
    assert twitter.make_tweet_text([{
        "name": "Lockheed Martin",
        "sentiment": -0.1,
        "ticker": "LMT"}, {
        "name": "Boeing",
        "sentiment": 0.1,
        "ticker": "BA"}],
        "https://twitter.com/realDonaldTrump/status/812061677160202240") == (
        u"Lockheed Martin $LMT \U0001f44e\n"
        u"Boeing $BA \U0001f44d\n"
        u"https://twitter.com/realDonaldTrump/status/812061677160202240")
    assert twitter.make_tweet_text([{
        "name": "General Motors",
        "sentiment": 0,
        "ticker": "GM"}],
        "https://twitter.com/realDonaldTrump/status/821697182235496450") == (
        u"General Motors $GM ¯\_(\u30c4)_/¯\n"
        u"https://twitter.com/realDonaldTrump/status/821697182235496450")


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
