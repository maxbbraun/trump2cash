# -*- coding: utf-8 -*-

from os import getenv
from simplejson import loads
from Queue import Queue
from threading import Thread
from tweepy import API
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy.streaming import StreamListener

from logs import Logs

# The keys for the Twitter account we're using for API requests and tweeting
# alerts (@TrumpCorrection). Read from environment variables.
TWITTER_ACCESS_TOKEN = getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = getenv("TWITTER_ACCESS_TOKEN_SECRET")

# The keys for the Twitter app we're using for API requests
# (https://apps.twitter.com/app/13239588). Read from environment variables.
TWITTER_CONSUMER_KEY = getenv("TWITTER_CONSUMER_KEY")
TWITTER_CONSUMER_SECRET = getenv("TWITTER_CONSUMER_SECRET")

# The user ID of @realDonaldTrump.
TRUMP_USER_ID = "25073877"

# The URL pattern for links to tweets.
TWEET_URL = "https://twitter.com/%s/status/%s"

# Some emoji.
EMOJI_THUMBS_UP = u"\U0001f44d"
EMOJI_THUMBS_DOWN = u"\U0001f44e"
EMOJI_SHRUG = u"¯\_(\u30c4)_/¯"

# The number of worker threads processing tweets.
NUM_THREADS = 100

class Twitter:
    """A helper for talking to Twitter APIs."""

    def __init__(self, streaming_callback=None, logs_to_cloud=True):
        self.logs = Logs(name="twitter", to_cloud=logs_to_cloud)
        twitter_listener = TwitterListener(callback=streaming_callback,
                                           logs_to_cloud=logs_to_cloud)
        twitter_auth = OAuthHandler(TWITTER_CONSUMER_KEY,
                                    TWITTER_CONSUMER_SECRET)
        twitter_auth.set_access_token(TWITTER_ACCESS_TOKEN,
                                      TWITTER_ACCESS_TOKEN_SECRET)
        self.twitter_stream = Stream(twitter_auth, twitter_listener)
        self.twitter_api = API(twitter_auth)

    def start_streaming(self):
        """Starts streaming tweets and returning data to the callback."""

        self.twitter_stream.filter(follow=[TRUMP_USER_ID])

    def tweet(self, companies, link):
        """Posts a tweet listing the companies, their ticker symbols, and a
        quote of the original tweet.
        """

        text = self.make_tweet_text(companies, link)
        self.logs.info("Tweeting: %s" % text)
        self.twitter_api.update_status(text)

    def make_tweet_text(self, companies, link):
        """Generates the text for a tweet."""

        text = ""

        for company in companies:
            line = company["name"]

            if "root" in company and company["root"]:
                line += " (%s)" % company["root"]

            ticker = company["ticker"]
            line += " $%s" % ticker

            if "sentiment" in company:
                if company["sentiment"] == 0:
                    sentiment = EMOJI_SHRUG
                else:
                    if company["sentiment"] > 0:
                        sentiment = EMOJI_THUMBS_UP
                    else:
                        sentiment = EMOJI_THUMBS_DOWN
                line += " %s" % sentiment

            text += "%s\n" % line

        text += link

        return text

    def get_tweets(self, ids):
        """Looks up metadata for a list of tweets."""

        statuses = self.twitter_api.statuses_lookup(ids)
        self.logs.debug("Got statuses response: %s" % statuses)

        return statuses


class TwitterListener(StreamListener):
    """A listener class for handling streaming Twitter data."""

    def __init__(self, callback, logs_to_cloud):
        self.logs_to_cloud = logs_to_cloud
        self.logs = Logs(name="twitter-listener", to_cloud=self.logs_to_cloud)
        self.callback = callback
        if self.callback:
            self.init_queue()

    def init_queue(self):
        """Creates a queue and starts the worker threads."""

        self.queue = Queue()
        for worker_id in range(NUM_THREADS):
            worker = Thread(target=self.process_queue, args=[worker_id])
            worker.start()

    def process_queue(self, worker_id):
        """Continuously processes tasks on the queue."""

        # Create a new logs instance (with its own httplib2 instance) so that
        # there is a separate one for each thread.
        logs = Logs("twitter-listener-worker-%s" % worker_id,
            to_cloud=self.logs_to_cloud)

        while True:
            # The main loop doesn't catch and report exceptions from background
            # threads, so do that here.
            try:
                size = self.queue.qsize()
                logs.debug("Processing queue of size: %s" % size)
                data = self.queue.get(block=True)
                self.handle_data(logs, data)
            except BaseException as exception:
                logs.catch(exception)

    def on_error(self, status):
        """Handles any API errors."""

        self.logs.error("Twitter error: %s" % status)

        # Don't stop.
        return True

    def on_data(self, data):
        """Puts a task to process the new data on the queue."""

        self.queue.put(data)

        # Don't stop.
        return True

    def handle_data(self, logs, data):
        """Sanity-checks and extracts the data before sending it to the
        callback.
        """

        # Decode the JSON response.
        try:
            tweet = loads(data)
        except ValueError:
            logs.error("Failed to decode JSON data: %s" % data)
            return

        # Do a basic check on the response format we expect.
        if not "user" in tweet:
            logs.warn("Malformed tweet: %s" % tweet)
            return

        # We're only interested in tweets from Mr. Trump himself, so skip the
        # rest.
        user_id_str = tweet["user"]["id_str"]
        screen_name = tweet["user"]["screen_name"]
        if user_id_str != TRUMP_USER_ID:
            logs.debug("Skipping tweet from user: %s (%s)" %
                       (screen_name, user_id_str))
            return

        # Extract what data we need from the tweet.
        text = tweet["text"]
        id_str = tweet["id_str"]
        link = TWEET_URL % (screen_name, id_str)
        logs.debug("Examining tweet: %s %s" % (link, data))

        # Call the callback.
        self.callback(text, link)

#
# Tests
#

import pytest
from datetime import datetime


@pytest.fixture
def twitter():
    # TODO: Test callback.
    return Twitter(streaming_callback=None, logs_to_cloud=False)


def test_environment_variables():
    assert TWITTER_CONSUMER_KEY
    assert TWITTER_CONSUMER_SECRET
    assert TWITTER_ACCESS_TOKEN
    assert TWITTER_ACCESS_TOKEN_SECRET


def test_twitter_listener():
    # TODO
    pass


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
    statuses = twitter.get_tweets(["806134244384899072", "812061677160202240"])
    assert len(statuses) == 2
    assert statuses[0].text == (
        "Boeing is building a brand new 747 Air Force One for future presidents"
        ", but costs are out of control, more than $4 billion. Cancel order!")
    assert statuses[0].id_str == "806134244384899072"
    assert statuses[0].user.id_str == "25073877"
    assert statuses[0].user.screen_name == "realDonaldTrump"
    assert statuses[0].created_at == datetime(2016, 12, 6, 13, 52, 35)
    assert statuses[1].text == (
        "Based on the tremendous cost and cost overruns of the Lockheed Martin "
        "F-35, I have asked Boeing to price-out a comparable F-18 Super Hornet!"
        )
    assert statuses[1].id_str == "812061677160202240"
    assert statuses[1].user.id_str == "25073877"
    assert statuses[1].user.screen_name == "realDonaldTrump"
    assert statuses[1].created_at == datetime(2016, 12, 22, 22, 26, 5)
