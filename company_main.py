from datetime import datetime
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from threading import Event
from threading import Thread
from time import sleep

from analysis import Analysis
from logs import Logs
from logs import Logs
from logs_trade import LogsTrade
from trading import Trading
from company_twitter import Twitter

# Whether to send all logs to the cloud instead of a local file.
LOGS_TO_CLOUD = False

# The duration of the smallest backoff step in seconds.
BACKOFF_STEP_S = 0.1

# The maximum number of retry steps, equivalent to 0.1 * (2^12 - 1) = 409.5
# seconds of total delay. This is the largest interval that one backoff
# sequence may take.
MAX_TRIES = 12

# The time in seconds after which to reset a backoff sequence. This is the
# smallest interval at which backoff sequences may repeat normally.
BACKOFF_RESET_S = 30 * 60

# The host for the monitor Web server.
MONITOR_HOST = "0.0.0.0"

# The port for the monitor Web server.
MONITOR_PORT = 80

# The message returned by the monitor Web server.
MONITOR_MESSAGE = "OK"


class Monitor:
    """A monitor exposing a Web server while the main loop is running."""

    def __init__(self):
        """Creates a Web server on a background thread."""

        self.server = HTTPServer((MONITOR_HOST, MONITOR_PORT),
                                 self.MonitorHandler)
        self.thread = Thread(target=self.server.serve_forever)
        self.thread.daemon = True

    def start(self):
        """Starts the Web server background thread."""

        self.thread.start()

    def stop(self):
        """Stops the Web server and background thread."""

        self.server.shutdown()
        self.server.server_close()

    class MonitorHandler(BaseHTTPRequestHandler):
        """An HTTP request handler that responds with "OK" while running."""

        def _set_headers(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()

        def do_GET(self):
            self._set_headers()
            self.wfile.write(MONITOR_MESSAGE.encode("utf-8"))

        def do_HEAD(self):
            self._set_headers()


class Main:
    """A wrapper for the main application logic and retry loop."""

    def __init__(self):
        self.logs = Logs(name="main", to_cloud=LOGS_TO_CLOUD)
        self.twitter = Twitter(logs_to_cloud=LOGS_TO_CLOUD)

    def twitter_callback(self, tweet):
        """Analyzes Trump tweets, trades stocks, and tweets about it."""
        
        # Initialize the Analysis, Logs, Trading, and Twitter instances inside
        # the callback to create separate httplib2 instances per thread.
        analysis = Analysis(logs_to_cloud=LOGS_TO_CLOUD)
        logs = Logs(name="main-callback", to_cloud=LOGS_TO_CLOUD)

        logs_trade = LogsTrade(name="main", to_cloud=LOGS_TO_CLOUD)

        # Analyze the tweet.
        companies = analysis.find_companies(tweet)
        logs.info("Using companies: %s" % companies)
        if not companies:
            return

        logs_trade.info("%s" % companies)

        # Trade stocks.
        # trading = Trading(logs_to_cloud=LOGS_TO_CLOUD)
        # trading.make_trades(companies)

        # Tweet about it.
        # twitter = Twitter(logs_to_cloud=LOGS_TO_CLOUD)
        # twitter.tweet(companies, tweet)

    def run_session(self):
        """Runs a single streaming session. Logs and cleans up after
        exceptions.
        """

        self.logs.info("Starting new session.")
        try:
            self.twitter.start_streaming(self.twitter_callback)
        except:
            self.logs.catch()
        finally:
            self.twitter.stop_streaming()
            self.logs.info("Ending session.")

    def backoff(self, tries):
        """Sleeps an exponential number of seconds based on the number of
        tries.
        """

        delay = BACKOFF_STEP_S * pow(2, tries)
        self.logs.warn("Waiting for %.1f seconds." % delay)
        sleep(delay)

    def run(self):
        """Runs the main retry loop with exponential backoff."""

        tries = 0
        while True:

            # The session blocks until an error occurs.
            self.run_session()

            # Remember the first time a backoff sequence starts.
            now = datetime.now()
            if tries == 0:
                self.logs.debug("Starting first backoff sequence.")
                backoff_start = now

            # Reset the backoff sequence if the last error was long ago.
            if (now - backoff_start).total_seconds() > BACKOFF_RESET_S:
                self.logs.debug("Starting new backoff sequence.")
                tries = 0
                backoff_start = now

            # Give up after the maximum number of tries.
            if tries >= MAX_TRIES:
                self.logs.warn("Exceeded maximum retry count.")
                break

            # Wait according to the progression of the backoff sequence.
            self.backoff(tries)

            # Increment the number of tries for the next error.
            tries += 1


if __name__ == "__main__":
    monitor = Monitor()
    monitor.start()
    try:
        Main().run()
    finally:
        monitor.stop()
