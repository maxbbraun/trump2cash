# -*- coding: utf-8 -*-

from google.cloud import error_reporting
from google.cloud import logging
from logging import basicConfig
from logging import getLogger
from logging import NOTSET

# The format for local logs.
LOGS_FORMAT = ("%(asctime)s "
               "%(name)s "
               "%(process)d "
               "%(thread)d "
               "%(levelname)s "
               "%(message)s")

# The path to the log file for local logging.
LOG_FILE = "/tmp/trump-corrections.log"

class Logs:
    """A helper for logging locally or in the cloud."""

    def __init__(self, name, to_cloud=True):
      self.to_cloud = to_cloud
      if self.to_cloud:
          # Use the Stackdriver logging and error reporting clients.
          self.logger = logging.Client(use_gax=False).logger(name)
          self.error_client = error_reporting.Client()
      else:
          # Log to a local file.
          self.logger = getLogger(name)
          basicConfig(format=LOGS_FORMAT, level=NOTSET, filename=LOG_FILE)

    def debug(self, text):
        """Logs at the DEBUG level."""

        if self.to_cloud:
            self.logger.log_text(text, severity="DEBUG")
        else:
            self.logger.debug(text)

    def info(self, text):
        """Logs at the INFO level."""

        if self.to_cloud:
            self.logger.log_text(text, severity="INFO")
        else:
            self.logger.info(text)

    def warn(self, text):
        """Logs at the WARNING level."""

        if self.to_cloud:
            self.logger.log_text(text, severity="WARNING")
        else:
            self.logger.warning(text)

    def error(self, text):
        """Logs at the ERROR level."""

        if self.to_cloud:
            self.logger.log_text(text, severity="ERROR")
        else:
            self.logger.error(text)

    def catch(self, exception):
        """Logs an exception."""

        if self.to_cloud:
            self.error_client.report_exception()
            self.logger.log_text(str(exception), severity="CRITICAL")
        else:
            self.logger.critical(str(exception))

#
# Tests
#

import pytest


@pytest.fixture
def logs():
    # TODO: Test cloud logging.
    return Logs("test", to_cloud=False)


def get_last_log():
    log_file = open(LOG_FILE, "r")
    return log_file.readlines()[-1]


def test_debug(logs, capfd):
    logs.debug("debug")
    assert get_last_log().endswith(" DEBUG debug\n")


def test_info(logs, capfd):
    logs.info("info")
    assert get_last_log().endswith(" INFO info\n")

def test_warn(logs, capfd):
    logs.warn("warn")
    assert get_last_log().endswith(" WARNING warn\n")


def test_error(logs, capfd):
    logs.error("error")
    assert get_last_log().endswith(" ERROR error\n")


def test_catch(logs, capfd):
    try:
      raise Exception("exception")
    except Exception as exception:
      logs.catch(exception)
    assert get_last_log().endswith(" CRITICAL exception\n")
