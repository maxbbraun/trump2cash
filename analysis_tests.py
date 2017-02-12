# -*- coding: utf-8 -*-

from google.cloud.language.entity import Entity
from os import getenv
from pytest import fixture

from analysis import Analysis
from analysis import MID_TO_TICKER_QUERY
from twitter import Twitter


@fixture
def analysis():
    return Analysis(logs_to_cloud=False)


def get_tweet(tweet_id):
    """Looks up data for a single tweet."""

    twitter = Twitter(logs_to_cloud=False)
    return twitter.get_tweet(tweet_id)


def get_tweet_text(tweet_id):
    """Looks up the text for a single tweet."""

    tweet = get_tweet(tweet_id)
    analysis = Analysis(logs_to_cloud=False)
    return analysis.get_expanded_text(tweet)


def test_environment_variables():
    assert getenv("GOOGLE_APPLICATION_CREDENTIALS")


def test_get_company_data(analysis):
    assert analysis.get_company_data("/m/035nm") == [{
        "exchange": "New York Stock Exchange",
        "name": "General Motors",
        "ticker": "GM"}]
    assert analysis.get_company_data("/m/04n3_w4") == [{
        "exchange": "New York Stock Exchange",
        "name": "Fiat",
        "root": "Fiat Chrysler Automobiles",
        "ticker": "FCAU"}]
    assert analysis.get_company_data("/m/0d8c4") == [{
        "exchange": "New York Stock Exchange",
        "name": "Lockheed Martin",
        "ticker": "LMT"}]
    assert analysis.get_company_data("/m/0hkqn") == [{
        "exchange": "New York Stock Exchange",
        "name": "Lockheed Martin",
        "ticker": "LMT"}]
    assert analysis.get_company_data("/m/09jcvs") == [{
        "exchange": "NASDAQ",
        "name": "YouTube",
        "root": "Google",
        "ticker": "GOOG"}, {
        "exchange": "NASDAQ",
        "name": "YouTube",
        "root": "Google",
        "ticker": "GOOGL"}, {
        "exchange": "NASDAQ",
        "name": "YouTube",
        "root": "Alphabet Inc.",
        "ticker": "GOOG"}, {
        "exchange": "NASDAQ",
        "name": "YouTube",
        "root": "Alphabet Inc.",
        "ticker": "GOOGL"}]
    assert analysis.get_company_data("/m/045c7b") == [{
        "exchange": "NASDAQ",
        "name": "Google",
        "ticker": "GOOG"}, {
        "exchange": "NASDAQ",
        "name": "Google",
        "ticker": "GOOGL"}, {
        "exchange": "NASDAQ",
        "name": "Google",
        "root": "Alphabet Inc.",
        "ticker": "GOOG"}, {
        "exchange": "NASDAQ",
        "name": "Google",
        "root": "Alphabet Inc.",
        "ticker": "GOOGL"}]
    assert analysis.get_company_data("/m/01snr1") == [{
        "exchange": "New York Stock Exchange",
        "name": "Bayer",
        "root": "BlackRock",
        "ticker": "BLK"}, {
        "exchange": "New York Stock Exchange",
        "name": "Bayer",
        "root": "PNC Financial Services",
        "ticker": "PNC"}]
    assert analysis.get_company_data("/m/02zs4") == [{
        "exchange": "New York Stock Exchange",
        "name": "Ford",
        "ticker": "F"}]
    assert analysis.get_company_data("/m/0841v") == [{
        "exchange": "New York Stock Exchange",
        "name": "Walmart",
        "ticker": "WMT"}, {
        "exchange": "New York Stock Exchange",
        "name": "Walmart",
        "root": "State Street Corporation",
        "ticker": "STT"}]
    assert analysis.get_company_data("/m/07mb6") == [{
        "exchange": "New York Stock Exchange",
        "name": "Toyota",
        "ticker": "TM"}]
    assert analysis.get_company_data("/m/0178g") == [{
        "exchange": "New York Stock Exchange",
        "name": "Boeing",
        "ticker": "BA"}]
    assert analysis.get_company_data("/m/07_dc0") == [{
        "exchange": "New York Stock Exchange",
        "name": "Carrier Corporation",
        "root": "United Technologies Corporation",
        "ticker": "UTX"}]
    assert analysis.get_company_data("/m/01pkxd") == [{
        "exchange": "New York Stock Exchange",
        "name": "Macy's",
        "root": "Macy's, Inc.",
        "ticker": "M"}]
    assert analysis.get_company_data("/m/02rnkmh") == [{
        "exchange": "New York Stock Exchange",
        "name": "Keystone Pipeline",
        "root": "TransCanada Corporation",
        "ticker": "TRP"}]
    assert analysis.get_company_data("/m/0k9ts") == [{
        "exchange": "New York Stock Exchange",
        "name": "Delta Air Lines",
        "ticker": "DAL"}]
    assert analysis.get_company_data("/m/033yz") == [{
        "exchange": "New York Stock Exchange",
        "name": "Lockheed Martin Aeronautics",
        "root": "Lockheed Martin",
        "ticker": "LMT"}]
    assert analysis.get_company_data("/m/017b3j") is None
    assert analysis.get_company_data("/m/07k2d") is None
    assert analysis.get_company_data("/m/02z_b") is None
    assert analysis.get_company_data("/m/0d6lp") is None
    assert analysis.get_company_data("xyz") is None
    assert analysis.get_company_data("") is None


def test_entity_tostring(analysis):
    assert analysis.entity_tostring(Entity(
        name="General Motors",
        entity_type="ORGANIZATION",
        metadata={
            "mid": "/m/035nm",
            "wikipedia_url": "http://en.wikipedia.org/wiki/General_Motors"},
        salience=0.33838183,
        mentions=["General Motors"])) == (
            '{name: "General Motors",'
            ' entity_type: "ORGANIZATION",'
            ' wikipedia_url: "http://en.wikipedia.org/wiki/General_Motors",'
            ' metadata: {"mid": "/m/035nm"},'
            ' salience: 0.33838183,'
            ' mentions: ["General Motors"]}')
    assert analysis.entity_tostring(Entity(
        name="jobs",
        entity_type="OTHER",
        metadata={},
        salience=0.31634554,
        mentions=["jobs"])) == (
        '{name: "jobs",'
        ' entity_type: "OTHER",'
        ' wikipedia_url: None,'
        ' metadata: {},'
        ' salience: 0.31634554,'
        ' mentions: ["jobs"]}')


def test_entities_tostring(analysis):
    assert analysis.entities_tostring([Entity(
        name="General Motors",
        entity_type="ORGANIZATION",
        metadata={
            "mid": "/m/035nm",
            "wikipedia_url": "http://en.wikipedia.org/wiki/General_Motors"},
        salience=0.33838183,
        mentions=["General Motors"]), Entity(
        name="jobs",
        entity_type="OTHER",
        metadata={"wikipedia_url": None},
        salience=0.31634554,
        mentions=["jobs"])]) == (
        '[{name: "General Motors",'
        ' entity_type: "ORGANIZATION",'
        ' wikipedia_url: "http://en.wikipedia.org/wiki/General_Motors",'
        ' metadata: {"mid": "/m/035nm"},'
        ' salience: 0.33838183,'
        ' mentions: ["General Motors"]}, '
        '{name: "jobs",'
        ' entity_type: "OTHER",'
        ' wikipedia_url: None,'
        ' metadata: {},'
        ' salience: 0.31634554,'
        ' mentions: ["jobs"]}]')
    assert analysis.entities_tostring([]) == "[]"


def test_get_sentiment(analysis):
    assert analysis.get_sentiment(get_tweet_text("806134244384899072")) < 0
    # assert analysis.get_sentiment(get_tweet_text("812061677160202240")) > 0
    assert analysis.get_sentiment(get_tweet_text("816260343391514624")) < 0
    assert analysis.get_sentiment(get_tweet_text("816324295781740544")) > 0
    assert analysis.get_sentiment(get_tweet_text("816635078067490816")) > 0
    assert analysis.get_sentiment(get_tweet_text("817071792711942145")) < 0
    assert analysis.get_sentiment(get_tweet_text("818460862675558400")) > 0
    assert analysis.get_sentiment(get_tweet_text("818461467766824961")) > 0
    assert analysis.get_sentiment(get_tweet_text("821415698278875137")) > 0
    # assert analysis.get_sentiment(get_tweet_text("821697182235496450")) > 0
    assert analysis.get_sentiment(get_tweet_text("821703902940827648")) > 0
    assert analysis.get_sentiment(get_tweet_text("803808454620094465")) > 0
    assert analysis.get_sentiment(get_tweet_text("621669173534584833")) < 0
    assert analysis.get_sentiment(get_tweet_text("664911913831301123")) < 0
    # assert analysis.get_sentiment(get_tweet_text("823950814163140609")) > 0
    assert analysis.get_sentiment(get_tweet_text("824055927200423936")) > 0
    assert analysis.get_sentiment(get_tweet_text("826041397232943104")) < 0
    assert analysis.get_sentiment(get_tweet_text("824765229527605248")) > 0
    assert analysis.get_sentiment(get_tweet_text("827874208021639168")) < 0
    assert analysis.get_sentiment(get_tweet_text("828642511698669569")) < 0
    assert analysis.get_sentiment(get_tweet_text("828793887275761665")) < 0
    assert analysis.get_sentiment(get_tweet_text("829410107406614534")) > 0
    assert analysis.get_sentiment(get_tweet_text("829356871848951809")) < 0
    # assert analysis.get_sentiment(get_tweet_text("808301935728230404")) < 0
    assert analysis.get_sentiment(None) == 0


def test_find_companies(analysis):
    assert analysis.find_companies(get_tweet("806134244384899072")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Boeing",
        "sentiment": -0.1,
        "ticker": "BA"}]
    assert analysis.find_companies(get_tweet("812061677160202240")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Lockheed Martin Aeronautics",
        "root": "Lockheed Martin",
        "sentiment": 0,  # -0.1,
        "ticker": "LMT"}, {
        "exchange": "New York Stock Exchange",
        "name": "Boeing",
        "sentiment": 0,  # 0.1,
        "ticker": "BA"}]
    assert analysis.find_companies(get_tweet("816260343391514624")) == [{
        "exchange": "New York Stock Exchange",
        "name": "General Motors",
        "sentiment": -0.1,
        "ticker": "GM"}]
    assert analysis.find_companies(get_tweet("816324295781740544")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Ford",
        "sentiment": 0.5,
        "ticker": "F"}]
    assert analysis.find_companies(get_tweet("816635078067490816")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Ford",
        "sentiment": 0.3,
        "ticker": "F"}]
    assert analysis.find_companies(get_tweet("817071792711942145")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Toyota",
        "sentiment": -0.2,
        "ticker": "TM"}]
    assert analysis.find_companies(get_tweet("818460862675558400")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Fiat",
        "root": "Fiat Chrysler Automobiles",
        "sentiment": 0.2,
        "ticker": "FCAU"}]
    assert analysis.find_companies(get_tweet("818461467766824961")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Ford",
        "sentiment": 0.3,
        "ticker": "F"}, {
        "exchange": "New York Stock Exchange",
        "name": "Fiat",
        "root": "Fiat Chrysler Automobiles",
        "sentiment": 0.3,
        "ticker": "FCAU"}]
    assert analysis.find_companies(get_tweet("821415698278875137")) == [{
        "exchange": "New York Stock Exchange",
        "name": "General Motors",
        "sentiment": 0.4,
        "ticker": "GM"}, {
        "exchange": "New York Stock Exchange",
        "name": "Walmart",
        "sentiment": 0.4,
        "ticker": "WMT"}, {
        "exchange": "New York Stock Exchange",
        "name": "Walmart",
        "root": "State Street Corporation",
        "sentiment": 0.4,
        "ticker": "STT"}]
    assert analysis.find_companies(get_tweet("821697182235496450")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Ford",
        "sentiment": -0.6,  # 0,
        "ticker": "F"}, {
        "exchange": "New York Stock Exchange",
        "name": "General Motors",
        "sentiment": -0.6,  # 0,
        "ticker": "GM"}, {
        "exchange": "New York Stock Exchange",
        "name": "Lockheed Martin",
        "sentiment": -0.6,  # 0,
        "ticker": "LMT"}]
    assert analysis.find_companies(get_tweet("821703902940827648")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Bayer",
        "sentiment": 0.4,
        "root": "BlackRock",
        "ticker": "BLK"}, {
        "exchange": "New York Stock Exchange",
        "name": "Bayer",
        "sentiment": 0.4,
        "root": "PNC Financial Services",
        "exchange": "New York Stock Exchange",
        "ticker": "PNC"}]
    # assert analysis.find_companies(get_tweet("803808454620094465")) == [{
    #     "exchange": "New York Stock Exchange",
    #     "name": "Carrier Corporation",
    #     "sentiment": 0.5,
    #     "root": "United Technologies Corporation",
    #     "ticker": "UTX"}]
    assert analysis.find_companies(get_tweet("621669173534584833")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Macy's",
        "root": "Macy's, Inc.",
        "sentiment": -0.5,
        "ticker": "M"}]
    assert analysis.find_companies(get_tweet("664911913831301123")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Macy's",
        "root": "Macy's, Inc.",
        "sentiment": -0.3,
        "ticker": "M"}]
    assert analysis.find_companies(get_tweet("823950814163140609")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Keystone Pipeline",
        "root": "TransCanada Corporation",
        "sentiment": -0.1,  # 0.1,
        "ticker": "TRP"}]
    assert analysis.find_companies(get_tweet("824055927200423936")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Ford",
        "sentiment": 0.5,
        "ticker": "F"}, {
        "exchange": "New York Stock Exchange",
        "name": "General Motors",
        "sentiment": 0.5,
        "ticker": "GM"}]
    assert analysis.find_companies(get_tweet("826041397232943104")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Delta Air Lines",
        "sentiment": -0.4,
        "ticker": "DAL"}]
    assert analysis.find_companies(get_tweet("824765229527605248")) == []
    assert analysis.find_companies(get_tweet("827874208021639168")) == []
    assert analysis.find_companies(get_tweet("828642511698669569")) == []
    assert analysis.find_companies(get_tweet("828793887275761665")) == []
    assert analysis.find_companies(get_tweet("829410107406614534")) == [{
        "exchange": "NASDAQ",
        "name": "Intel",
        "sentiment": 0.8,
        "ticker": "INTC"}]
    assert analysis.find_companies(get_tweet("829356871848951809")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Nordstrom",
        "sentiment": -0.2,
        "ticker": "JWN"}]
    assert analysis.find_companies(None) is None


def test_get_expanded_text(analysis):
    assert analysis.get_expanded_text(get_tweet("829410107406614534")) == (
        u"Thank you Brian Krzanich, CEO of Intel. A great investment ($7 BILLI"
        u"ON) in American INNOVATION and JOBS!\u2026 https://t.co/oicfDsPKHQ")
    assert analysis.get_expanded_text(get_tweet("828574430800539648")) == (
        "Any negative polls are fake news, just like the CNN, ABC, NBC polls i"
        "n the election. Sorry, people want border security and extreme vettin"
        "g.")
    assert analysis.get_expanded_text(get_tweet("828642511698669569")) == (
        "The failing The New York Times writes total fiction concerning me. Th"
        "ey have gotten it wrong for two years, and now are making up stories "
        "&amp; sources!")
    assert analysis.get_expanded_text(None) is None


def test_make_wikidata_request(analysis):
    assert analysis.make_wikidata_request(
        MID_TO_TICKER_QUERY % "/m/02y1vz") == [{
            "companyLabel": {
                "type": "literal",
                "value": "Facebook",
                "xml:lang": "en"},
            "rootLabel": {
                "type": "literal",
                "value": "Facebook Inc.",
                "xml:lang": "en"},
            "exchangeNameLabel": {
                "type": "literal",
                "value": "NASDAQ",
                "xml:lang": "en"},
            "tickerLabel": {
                "type": "literal",
                "value": "FB"}}]
    assert analysis.make_wikidata_request("") is None
