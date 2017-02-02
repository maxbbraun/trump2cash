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
LOG_FILE = "/tmp/trump2cash.log"


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
            self.safe_cloud_log(text, severity="DEBUG")
        else:
            self.logger.debug(text)

    def info(self, text):
        """Logs at the INFO level."""

        if self.to_cloud:
            self.safe_cloud_log(text, severity="INFO")
        else:
            self.logger.info(text)

    def warn(self, text):
        """Logs at the WARNING level."""

        if self.to_cloud:
            self.safe_cloud_log(text, severity="WARNING")
        else:
            self.logger.warning(text)

    def error(self, text):
        """Logs at the ERROR level."""

        if self.to_cloud:
            self.safe_cloud_log(text, severity="ERROR")
        else:
            self.logger.error(text)

    def catch(self, exception):
        """Logs an exception."""

        if self.to_cloud:
            self.error_client.report_exception()
            self.safe_cloud_log(str(exception), severity="CRITICAL")
        else:
            self.logger.critical(str(exception))

    def safe_cloud_log(self, text, severity):
        """Logs to the cloud and catches exceptions if the upload fails."""

        # TODO: Implement retry logic with exponential backoff.
        try:
            self.logger.log_text(text, severity=severity)
        except BaseException as exception:
            # Note that these calls will attempt new logs, but without the
            # exception catch to avoid recursion for permanent failures.
            self.error_client.report_exception()
            self.logger.log_text(str(exception), severity="CRITICAL")
            self.logger.log_text("Skipped log: %s" % text, severity="ERROR")
