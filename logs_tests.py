# -*- coding: utf-8 -*-

from pytest import fixture

from logs import Logs
from logs import LOG_FILE


@fixture
def logs():
    # TODO: Test cloud logging.
    return Logs("test", to_cloud=False)


def get_last_log():
    log_file = open(LOG_FILE, "r")
    try:
        last_log = log_file.readlines()[-1]
    finally:
        log_file.close()
    return last_log


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
