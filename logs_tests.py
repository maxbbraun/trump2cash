from pytest import fixture

from logs import Logs
from logs import LOG_FILE


@fixture
def logs():
    # TODO: Test cloud logging.
    return Logs('test', to_cloud=False)


def get_last_logs(lines=1):
    log_file = open(LOG_FILE, 'r')
    try:
        last_logs = log_file.readlines()[-lines:]
    finally:
        log_file.close()
    return ''.join(last_logs)


def test_debug(logs, capfd):
    logs.debug('debug')
    assert get_last_logs().endswith(' DEBUG debug\n')


def test_info(logs, capfd):
    logs.info('info')
    assert get_last_logs().endswith(' INFO info\n')


def test_warn(logs, capfd):
    logs.warn('warn')
    assert get_last_logs().endswith(' WARNING warn\n')


def test_error(logs, capfd):
    logs.error('error')
    assert get_last_logs().endswith(' ERROR error\n')


def test_catch(logs, capfd):
    try:
        raise Exception('exception')
    except Exception:
        logs.catch()
    assert get_last_logs(4).endswith(
        'logs_tests.py", line 44, in test_catch\n    raise Exception(\'excepti'
        'on\')\nException: exception\n')
