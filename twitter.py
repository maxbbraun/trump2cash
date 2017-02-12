# -*- coding: utf-8 -*-

from os import getenv
from simplejson import loads
from Queue import Queue
from threading import Event
from threading import Thread
from tweepy import API
from tweepy import Cursor
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy.streaming import StreamListener

from logs import Logs

# The keys for the Twitter account we're using for API requests and tweeting
# alerts (@Trump2Cash). Read from environment variables.
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

    def __init__(self, logs_to_cloud):
        self.logs_to_cloud = logs_to_cloud
        self.logs = Logs(name="twitter", to_cloud=self.logs_to_cloud)
        self.twitter_auth = OAuthHandler(TWITTER_CONSUMER_KEY,
                                         TWITTER_CONSUMER_SECRET)
        self.twitter_auth.set_access_token(TWITTER_ACCESS_TOKEN,
                                           TWITTER_ACCESS_TOKEN_SECRET)
        self.twitter_api = API(self.twitter_auth)

    def start_streaming(self, callback):
        """Starts streaming tweets and returning data to the callback."""

        self.twitter_listener = TwitterListener(
            callback=callback, logs_to_cloud=self.logs_to_cloud)
        twitter_stream = Stream(self.twitter_auth, self.twitter_listener)

        self.logs.debug("Starting stream.")
        twitter_stream.filter(follow=[TRUMP_USER_ID])

        # If we got here because of an API error, raise it.
        if self.twitter_listener.get_error_status():
            raise Exception(self.twitter_listener.get_error_status())

    def stop_streaming(self):
        """Stops the current stream."""

        if not self.twitter_listener:
            self.logs.warn("No stream to stop.")
            return

        self.logs.debug("Stopping stream.")
        self.twitter_listener.stop_queue()

    def tweet(self, companies, tweet):
        """Posts a tweet listing the companies, their ticker symbols, and a
        quote of the original tweet.
        """

        link = self.get_tweet_link(tweet)
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

    def get_tweet(self, tweet_id):
        """Looks up metadata for a single tweet."""

        statuses = self.twitter_api.statuses_lookup([tweet_id])
        if not statuses or len(statuses) != 1:
            self.logs.error("Bad statuses response: %s" % statuses)
            return None

        # Use the raw JSON, just like the streaming API.
        return statuses[0]._json

    def get_tweets(self, since_id):
        """Looks up metadata for all Trump tweets since the specified ID."""

        # Include the first ID by passing along an earlier one.
        since_id = str(int(since_id) - 1)

        tweets = []
        for status in Cursor(self.twitter_api.user_timeline,
                             user_id=TRUMP_USER_ID,
                             since_id=since_id).items():

            # Use the raw JSON, just like the streaming API.
            tweets.append(status._json)

        self.logs.debug("Got tweets: %s" % tweets)

        return tweets

    def get_tweet_link(self, tweet):
        """Creates the link URL to a tweet."""

        if not tweet:
            self.logs.error("No tweet to get link.")
            return None

        try:
            screen_name = tweet["user"]["screen_name"]
            id_str = tweet["id_str"]
        except KeyError:
            self.logs.error("Malformed tweet for link: %s" % tweet)
            return None

        link = TWEET_URL % (screen_name, id_str)
        return link


class TwitterListener(StreamListener):
    """A listener class for handling streaming Twitter data."""

    def __init__(self, callback, logs_to_cloud):
        self.logs_to_cloud = logs_to_cloud
        self.logs = Logs(name="twitter-listener", to_cloud=self.logs_to_cloud)
        self.callback = callback
        self.error_status = None
        self.start_queue()

    def start_queue(self):
        """Creates a queue and starts the worker threads."""

        self.queue = Queue()
        self.stop_event = Event()
        self.logs.debug("Starting %s worker threads." % NUM_THREADS)
        self.workers = []
        for worker_id in range(NUM_THREADS):
            worker = Thread(target=self.process_queue, args=[worker_id])
            worker.daemon = True
            worker.start()
            self.workers.append(worker)

    def stop_queue(self):
        """Shuts down the worker threads."""

        if not self.workers:
            self.logs.warn("No worker threads to stop.")
            return

        self.stop_event.set()
        for worker in self.workers:
            # Terminate the thread immediately.
            worker.join(0)

    def process_queue(self, worker_id):
        """Continuously processes tasks on the queue."""

        # Create a new logs instance (with its own httplib2 instance) so that
        # there is a separate one for each thread.
        logs = Logs("twitter-listener-worker-%s" % worker_id,
                    to_cloud=self.logs_to_cloud)

        logs.debug("Started worker thread: %s" % worker_id)
        while not self.stop_event.is_set():
            # The main loop doesn't catch and report exceptions from background
            # threads, so do that here.
            try:
                size = self.queue.qsize()
                logs.debug("Processing queue of size: %s" % size)
                data = self.queue.get(block=True)
                self.handle_data(logs, data)
                self.queue.task_done()
            except BaseException as exception:
                logs.catch(exception)
        logs.debug("Stopped worker thread: %s" % worker_id)

    def on_error(self, status):
        """Handles any API errors."""

        self.logs.error("Twitter error: %s" % status)
        self.error_status = status
        self.stop_queue()
        return False

    def get_error_status(self):
        """Returns the API error status, if there was one."""
        return self.error_status

    def on_data(self, data):
        """Puts a task to process the new data on the queue."""

        # Stop streaming if requested.
        if self.stop_event.is_set():
            return False

        # Put the task on the queue and keep streaming.
        self.queue.put(data)
        return True

    def handle_data(self, logs, data):
        """Sanity-checks and extracts the data before sending it to the
        callback.
        """

        try:
            tweet = loads(data)
        except ValueError:
            logs.error("Failed to decode JSON data: %s" % data)
            return

        try:
            user_id_str = tweet["user"]["id_str"]
            screen_name = tweet["user"]["screen_name"]
        except KeyError:
            logs.error("Malformed tweet: %s" % tweet)
            return

        # We're only interested in tweets from Mr. Trump himself, so skip the
        # rest.
        if user_id_str != TRUMP_USER_ID:
            logs.debug("Skipping tweet from user: %s (%s)" %
                       (screen_name, user_id_str))
            return

        logs.info("Examining tweet: %s" % tweet)

        # Call the callback.
        self.callback(tweet)
