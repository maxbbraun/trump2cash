from json import loads
from os import getenv
from queue import Empty
from queue import Queue
from threading import Event
from threading import Thread
from time import time
from tweepy import API
from tweepy import Cursor
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy.streaming import StreamListener

from logs import Logs

from dotenv import load_dotenv
load_dotenv()

# The keys for the Twitter account we're using for API requests and tweeting
# alerts (@Trump2Cash). Read from environment variables.
TWITTER_ACCESS_TOKEN = getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = getenv("TWITTER_ACCESS_TOKEN_SECRET")

# The keys for the Twitter app we're using for API requests
# (https://apps.twitter.com/app/13239588). Read from environment variables.
TWITTER_CONSUMER_KEY = getenv("TWITTER_CONSUMER_KEY")
TWITTER_CONSUMER_SECRET = getenv("TWITTER_CONSUMER_SECRET")

# The number of worker threads processing tweets.
NUM_THREADS = 1

# The maximum time in seconds that workers wait for a new task on the queue.
QUEUE_TIMEOUT_S = 5 * 60

# The number of retries to attempt when an error occurs.
API_RETRY_COUNT = 10

# The number of seconds to wait between retries.
API_RETRY_DELAY_S = 1

# The HTTP status codes for which to retry.
API_RETRY_ERRORS = [400, 401, 500, 502, 503, 504]


class Twitter:
    """A helper for talking to Twitter APIs."""

    def __init__(self, logs_to_cloud, twitter_user_id):
        self.logs_to_cloud = logs_to_cloud
        self.twitter_user_id = twitter_user_id
        self.logs = Logs(name="twitter-dave", to_cloud=self.logs_to_cloud)
        self.twitter_auth = OAuthHandler(TWITTER_CONSUMER_KEY,
                                         TWITTER_CONSUMER_SECRET)
        self.twitter_auth.set_access_token(TWITTER_ACCESS_TOKEN,
                                           TWITTER_ACCESS_TOKEN_SECRET)
        self.twitter_api = API(auth_handler=self.twitter_auth,
                               retry_count=API_RETRY_COUNT,
                               retry_delay=API_RETRY_DELAY_S,
                               retry_errors=API_RETRY_ERRORS,
                               wait_on_rate_limit=True,
                               wait_on_rate_limit_notify=True)
        self.twitter_listener = None

    def start_streaming(self, callback):
        """Starts streaming tweets and returning data to the callback."""

        self.twitter_listener = TwitterListener(
            callback=callback, logs_to_cloud=self.logs_to_cloud, twitter_user_id=self.twitter_user_id)
        twitter_stream = Stream(self.twitter_auth, self.twitter_listener)

        self.logs.debug("Starting stream.")
        twitter_stream.filter(follow=[self.twitter_user_id])

        # If we got here because of an API error, raise it.
        if self.twitter_listener and self.twitter_listener.get_error_status():
            raise Exception("Twitter API error: %s" %
                            self.twitter_listener.get_error_status())

    def stop_streaming(self):
        """Stops the current stream."""

        if not self.twitter_listener:
            self.logs.warn("No stream to stop.")
            return

        self.logs.debug("Stopping stream.")
        self.twitter_listener.stop_queue()
        self.twitter_listener = None

    def get_tweet(self, tweet_id):
        """Looks up metadata for a single tweet."""

        # Use tweet_mode=extended so we get the full text.
        status = self.twitter_api.get_status(tweet_id, tweet_mode="extended")
        if not status:
            self.logs.error("Bad status response: %s" % status)
            return None

        # Use the raw JSON, just like the streaming API.
        return status._json

    def get_tweet_text(self, tweet):
        """Returns the full text of a tweet."""

        # The format for getting at the full text is different depending on
        # whether the tweet came through the REST API or the Streaming API:
        # https://dev.twitter.com/overview/api/upcoming-changes-to-tweets
        try:
            if "extended_tweet" in tweet:
                self.logs.debug("Decoding extended tweet from Streaming API.")
                return tweet["extended_tweet"]["full_text"]
            elif "full_text" in tweet:
                self.logs.debug("Decoding extended tweet from REST API.")
                return tweet["full_text"]
            else:
                self.logs.debug("Decoding short tweet.")
                return tweet["text"]
        except KeyError:
            self.logs.error("Malformed tweet: %s" % tweet)
            return None

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

    def __init__(self, callback, logs_to_cloud, twitter_user_id):
        self.logs_to_cloud = logs_to_cloud
        self.twitter_user_id = twitter_user_id
        self.logs = Logs(name="twitter-dave-listener",
                         to_cloud=self.logs_to_cloud)
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
        """Shuts down the queue and worker threads."""

        # First stop the queue.
        if self.queue:
            self.logs.debug("Stopping queue.")
            self.queue.join()
        else:
            self.logs.warn("No queue to stop.")

        # Then stop the worker threads.
        if self.workers:
            self.logs.debug("Stopping %d worker threads." % len(self.workers))
            self.stop_event.set()
            for worker in self.workers:
                # Block until the thread terminates.
                worker.join()
        else:
            self.logs.warn("No worker threads to stop.")

    def process_queue(self, worker_id):
        """Continuously processes tasks on the queue."""

        # Create a new logs instance (with its own httplib2 instance) so that
        # there is a separate one for each thread.
        logs = Logs("twitter-dave-listener-worker-%s" % worker_id,
                    to_cloud=self.logs_to_cloud)

        logs.debug("Started worker thread: %s" % worker_id)
        while not self.stop_event.is_set():
            try:
                data = self.queue.get(block=True, timeout=QUEUE_TIMEOUT_S)
                start_time = time()
                self.handle_data(logs, data)
                self.queue.task_done()
                end_time = time()
                qsize = self.queue.qsize()
                logs.debug("Worker %s took %.f ms with %d tasks remaining." %
                           (worker_id, end_time - start_time, qsize))
            except Empty:
                logs.debug("Worker %s timed out on an empty queue." %
                           worker_id)
                continue
            except Exception:
                # The main loop doesn't catch and report exceptions from
                # background threads, so do that here.
                logs.catch()
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
        # print(data)
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
        # if user_id_str != self.twitter_user_id:
        #     logs.debug("Skipping tweet from user: %s (%s)" %
        #                (screen_name, user_id_str))
        #     return

        logs.info("Examining tweet: %s" % tweet)

        # Call the callback.
        self.callback(tweet)
