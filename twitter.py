# -*- coding: utf-8 -*-

from google.cloud import error_reporting
from google.cloud import logging
from os import environ
from simplejson import loads
from threading import Thread
from tweepy import API
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy.streaming import StreamListener

# The keys for the Twitter account we're using for API requests and tweeting
# alerts (@TrumpCorrection). Read from environment variables.
TWITTER_ACCESS_TOKEN = environ["TWITTER_ACCESS_TOKEN"]
TWITTER_ACCESS_TOKEN_SECRET = environ["TWITTER_ACCESS_TOKEN_SECRET"]

# The keys for the Twitter app we're using for API requests 
# (https://apps.twitter.com/app/13239588). Read from environment variables.
TWITTER_CONSUMER_KEY = environ["TWITTER_CONSUMER_KEY"]
TWITTER_CONSUMER_SECRET = environ["TWITTER_CONSUMER_SECRET"]

# The user ID of @realDonaldTrump.
TRUMP_USER_ID = "25073877"

# The URL pattern for links to tweets. The parameter is the tweet's ID.
TWEET_URL = "https://twitter.com/%s/status/%s"

# Some emoji.
EMOJI_THUMBS_UP = u"\U0001f44d"
EMOJI_THUMBS_DOWN = u"\U0001f44e"
EMOJI_SHRUG = u"¯\_(\u30c4)_/¯"

# A helper for talking to Twitter APIs.
class Twitter:
  def __init__(self, callback):
    self.logger = logging.Client(use_gax=False).logger("twitter")
    twitter_listener = TwitterListener(callback)
    twitter_auth = OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
    twitter_auth.set_access_token(TWITTER_ACCESS_TOKEN,
      TWITTER_ACCESS_TOKEN_SECRET)
    self.twitter_stream = Stream(twitter_auth, twitter_listener)
    self.twitter_api = API(twitter_auth)

  # Starts streaming tweets and returning data to the callback.
  def start_streaming(self):
    self.twitter_stream.filter(follow=[TRUMP_USER_ID])

  # Post a tweet listing the companies, their ticker symbols, and a quote of the
  # original tweet.
  def tweet(self, companies, link):
    text = self.make_tweet_text(companies, link)
    self.logger.log_text(text, severity="INFO")
    self.twitter_api.update_status(text)

  # Creates the text for a tweet.
  def make_tweet_text(self, companies, link):
    text = u""

    for company in companies:
      line = company["name"]

      if "root" in company and company["root"]:
        line += u" (%s)" % company["root"]

      ticker = company["ticker"]
      line += u" $%s" % ticker

      if "sentiment" in company:
        if company["sentiment"] == 0:
          sentiment = EMOJI_SHRUG
        else:
          positive = company["sentiment"] > 0
          sentiment = EMOJI_THUMBS_UP if positive else EMOJI_THUMBS_DOWN
        line += u" %s" % sentiment

      text += u"%s\n" % line

    text += link

    return text

# A listener class for handling streaming Twitter data.
class TwitterListener(StreamListener):
  def __init__(self, callback):
    self.logger = logging.Client(use_gax=False).logger("twitter-listener")
    self.callback = callback

  # Handles any API errors.
  def on_error(self, status):
    self.logger.log_text("Twitter error: %s" % status, severity="ERROR")

    # Don't stop.
    return True

  # Kicks off a new thread to handle data.
  def on_data(self, data):
    thread = Thread(target=self.safe_handle_data, args=[data])
    thread.start()

    # Don't stop.
    return True

  # Calls handle_data() in a thread-safe way.
  def safe_handle_data(self, data):

    # Create new logging and error clients (with their own httplib2 instances)
    # to be used on background threads.
    logger = logging.Client(use_gax=False).logger("twitter-listener-background")
    error_client = error_reporting.Client()

    # The main loop doesn't catch and report exceptions from background
    # threads, so do that here.
    try:
      self.handle_data(logger, data)
    except Exception as exception:
      error_client.report_exception()
      logger.log_text("Exception on background thread: %s" % exception,
        severity="ERROR")

  # Sanity-checks and extracts the data before sending it to the callback.
  def handle_data(self, logger, data):

    # Decode the JSON response.
    try:
      tweet = loads(data)
    except ValueError:
      logger.log_text("Failed to decode JSON data: %s" % data, severity="ERROR")
      return

    # Do a basic check on the response format we expect.
    if not "user" in tweet:
      logger.log_text("Malformed tweet: %s" % tweet, severity="WARNING")
      return

    # We're only interested in tweets from Mr. Trump himself, so skip the rest.
    user_id = tweet["user"]["id"]
    screen_name = tweet["user"]["screen_name"]
    if str(user_id) != TRUMP_USER_ID:
      logger.log_text("Skipping tweet from user: %s (%s)" % (screen_name,
        user_id), severity="DEBUG")
      return

    # Extract what data we need from the tweet.
    text = tweet["text"]
    id_str = tweet["id_str"]
    link = TWEET_URL % (screen_name, id_str)
    logger.log_text("Examining tweet: %s %s" % (link, data),
      severity="DEBUG")

    # Call the callback.
    self.callback(text, link)

#
# Tests
#

import pytest

def callback(text, link):
  pass

@pytest.fixture
def twitter():
  return Twitter(callback)

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
    "ticker": "F"},{
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
    "ticker": "LMT"},{
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
