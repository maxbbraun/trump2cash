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
        'name': 'Boeing',
        'sentiment': -0.1,
        'ticker': 'BA'}],
        'https://twitter.com/realDonaldTrump/status/806134244384899072') == (
        'Boeing \U0001f44e $BA\n'
        'https://twitter.com/realDonaldTrump/status/806134244384899072')
    assert twitter.make_tweet_text([{
        'name': 'Ford',
        'sentiment': 0.3,
        'ticker': 'F'}, {
        'name': 'Fiat',
        'root': 'Fiat Chrysler Automobiles',
        'sentiment': 0.3,
        'ticker': 'FCAU'}],
        'https://twitter.com/realDonaldTrump/status/818461467766824961') == (
        'Ford \U0001f44d $F\n'
        'Fiat \U0001f44d $FCAU\n'
        'https://twitter.com/realDonaldTrump/status/818461467766824961')
    assert twitter.make_tweet_text([{
        'name': 'Lockheed Martin',
        'sentiment': -0.1,
        'ticker': 'LMT'}, {
        'name': 'Boeing',
        'sentiment': 0.1,
        'ticker': 'BA'}],
        'https://twitter.com/realDonaldTrump/status/812061677160202240') == (
        'Lockheed Martin \U0001f44e $LMT\n'
        'Boeing \U0001f44d $BA\n'
        'https://twitter.com/realDonaldTrump/status/812061677160202240')
    assert twitter.make_tweet_text([{
        'name': 'General Motors',
        'sentiment': 0,
        'ticker': 'GM'}],
        'https://twitter.com/realDonaldTrump/status/821697182235496450') == (
        'General Motors ¯\\_(\u30c4)_/¯ $GM\n'
        'https://twitter.com/realDonaldTrump/status/821697182235496450')
    assert twitter.make_tweet_text([{
        'ticker': 'XOM',
        'name': 'ExxonMobil',
        'sentiment': 0.5,
        'exchange': 'New York Stock Exchange'}, {
        'root': 'BlackRock',
        'ticker': 'BLK',
        'name': 'ExxonMobil',
        'sentiment': 0.5,
        'exchange': 'New York Stock Exchange'}, {
        'root': 'PNC Financial Services',
        'ticker': 'PNC',
        'name': 'ExxonMobil',
        'sentiment': 0.5,
        'exchange': 'New York Stock Exchange'}, {
        'root': 'State Street Corporation',
        'ticker': 'STT',
        'name': 'ExxonMobil',
        'sentiment': 0.5,
        'exchange': 'New York Stock Exchange'}],
        'https://twitter.com/realDonaldTrump/status/838862131852369922') == (
        'ExxonMobil \U0001f44d $XOM $BLK $PNC $STT\n'
        'https://twitter.com/realDonaldTrump/status/838862131852369922')
    assert twitter.make_tweet_text([{
        'ticker': 'GM',
        'name': 'General Motors',
        'sentiment': 0.4,
        'exchange': 'New York Stock Exchange'}, {
        'ticker': 'WMT',
        'name': 'Walmart',
        'sentiment': 0.4,
        'exchange': 'New York Stock Exchange'}, {
        'root': 'State Street Corporation',
        'ticker': 'STT',
        'name': 'Walmart',
        'sentiment': 0.4,
        'exchange': 'New York Stock Exchange'}],
        'https://twitter.com/realDonaldTrump/status/821415698278875137') == (
        'General Motors \U0001f44d $GM\n'
        'Walmart \U0001f44d $WMT $STT\n'
        'https://twitter.com/realDonaldTrump/status/821415698278875137')
    assert twitter.make_tweet_text([{
        'ticker': chr(i - 32),
        'name': chr(i),
        'sentiment': 0} for i in range(97, 123)],
        'https://twitter.com/realDonaldTrump/status/0') == (
        'a ¯\\_(\u30c4)_/¯ $A\n'
        'b ¯\\_(\u30c4)_/¯ $B\n'
        'c ¯\\_(\u30c4)_/¯ $C\n'
        'd ¯\\_(\u30c4)_/¯ $D\n'
        'e ¯\\_(\u30c4)_/¯ $E\n'
        'f ¯\\_(\u30c4)_/¯ $F\n'
        'g ¯\\\u2026\n'
        'https://twitter.com/realDonaldTrump/status/0')


def test_get_sentiment_emoji(twitter):
    assert twitter.get_sentiment_emoji(0.5) == '\U0001f44d'
    assert twitter.get_sentiment_emoji(-0.5) == '\U0001f44e'
    assert twitter.get_sentiment_emoji(0) == '¯\\_(\u30c4)_/¯'
    assert twitter.get_sentiment_emoji(None) == '¯\\_(\u30c4)_/¯'


# def test_get_tweet_trump(twitter):
#     tweet = twitter.get_tweet('845334323045765121')
#     assert tweet['full_text'] == (
#         'Today, I was thrilled to announce a commitment of $25 BILLION &amp; 2'
#         '0K AMERICAN JOBS over the next 4 years. THANK YOU Charter Communicati'
#         'ons! https://t.co/PLxUmXVl0h')
#     assert tweet['id_str'] == '845334323045765121'
#     assert tweet['user']['id_str'] == '25073877'
#     assert tweet['user']['screen_name'] == 'realDonaldTrump'
#     assert tweet['created_at'] == 'Fri Mar 24 17:59:42 +0000 2017'


def test_get_tweet_musk(twitter):
    tweet = twitter.get_tweet('1357241340313141249')
    assert tweet['full_text'] == 'Dogecoin is the people’s crypto'
    assert tweet['id_str'] == '1357241340313141249'
    assert tweet['user']['id_str'] == '44196397'
    assert tweet['user']['screen_name'] == 'elonmusk'
    assert tweet['created_at'] == 'Thu Feb 04 08:15:26 +0000 2021'


# def test_get_tweet_link_trump(twitter):
#     tweet = twitter.get_tweet('828574430800539648')
#     assert twitter.get_tweet_link(tweet) == (
#         'https://twitter.com/realDonaldTrump/status/828574430800539648')


def test_get_tweet_link_musk(twitter):
    tweet = twitter.get_tweet('1357241340313141249')
    assert twitter.get_tweet_link(tweet) == (
        'https://twitter.com/elonmusk/status/1357241340313141249')
