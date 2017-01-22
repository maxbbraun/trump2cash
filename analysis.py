# -*- coding: utf-8 -*-

from google.cloud import language
from google.cloud.language.entity import Entity
from google.cloud import logging
from requests import get

# The URL for a GET request to the Wikidata API via a SPARQL query to find
# stock ticker symbols. The parameter is the Freebase ID of the company.
WIKIDATA_TICKER_QUERY_URL = ('https://query.wikidata.org/sparql?query='
  'SELECT ?companyLabel ?ownerLabel ?ticker WHERE {'
  '  ?instance wdt:P646 "%s" .'  # Company with specified Freebase ID.
  '  ?instance wdt:P156* ?company .'  # Company may have restructured.
  '  ?company wdt:P127* ?owner .'  # Company may be a subsidiary.
  '  ?owner p:P414 ?exchange .'  # Company is traded on exchange.
  '  VALUES ?exchanges {wd:Q13677 wd:Q82059}'  # Whitelist is NYSE and NASDAQ.
  '  ?exchange ps:P414 ?exchanges .'  # Stock exchange is whitelisted.
  '  ?exchange pq:P249 ?ticker .'  # Get ticker symbol.
  '  SERVICE wikibase:label {'
  '    bd:serviceParam wikibase:language "en" .'  # Use English labels.
  '  }'
  '} GROUP BY ?companyLabel ?ownerLabel ?ticker'
  '&format=JSON')

# A helper for analyzing company data in text.
class Analysis:
  def __init__(self):
    self.logger = logging.Client().logger("analysis")
    self.gcnl_client = language.Client()

  # Look up stock ticker information for a company via its Freebase ID.
  def get_company_data(self, mid):
    response = get(WIKIDATA_TICKER_QUERY_URL % mid).json()
    self.logger.log_text("Wikidata response: %s" % response, severity="DEBUG")

    if not "results" in response:
      self.logger.log_text("No results in Wikidata response: %s" % response,
        severity="ERROR")
      return None

    results = response["results"]
    if not "bindings" in results:
      self.logger.log_text("No bindings in Wikidata results: %s" % results,
        severity="ERROR")
      return None

    bindings = results["bindings"]
    if not bindings:
      self.logger.log_text("Empty bindings in Wikidata results: %s" % results,
        severity="DEBUG")
      return []

    # Collect the data from the response.
    datas = []
    for binding in bindings:
      if "companyLabel" in binding:
        name = binding["companyLabel"]["value"]
      else:
        name = None

      if "ownerLabel" in binding:
        owner = binding["ownerLabel"]["value"]
      else:
        owner = None

      if "ticker" in binding:
        ticker = binding["ticker"]["value"]
      else:
        ticker = None

      data = {}
      data["name"] = name
      data["ticker"] = ticker
      if owner and owner != name:
        data["owner"] = owner
      datas.append(data)

    return datas

  # Finds mentions of companies in text.
  def find_companies(self, text):

    # Run entity detection.
    try:
      document = self.gcnl_client.document_from_text(text)
      entities = document.analyze_entities()
    except:
      self.logger.log_text("Failed to analyze entities in text: %s" % text,
        severity="ERROR")
      return []
    self.logger.log_text("Found entities: %s" % self.entities_tostring(
      entities), severity="DEBUG")

    # Collect all entities which are publicly traded companies, i.e. entities
    # which have a known stock ticker symbol.
    companies = []
    for entity in entities:

      # We are only interested in certain entity types, so skip anything else.
      if entity.entity_type not in ["ORGANIZATION", "OTHER", "UNKNOWN"]:
        self.logger.log_text("Skipping entity: %s" % self.entity_tostring(
          entity), severity="DEBUG")
        continue

      # Use the Freebase ID of the entity to find company data. Skip any entity
      # which doesn't have a Freebase ID.
      name = entity.name
      metadata = entity.metadata
      if not "mid" in metadata:
        self.logger.log_text("No MID found for entity: %s" % name,
          severity="DEBUG")
        continue
      mid = metadata["mid"]
      company_data = self.get_company_data(mid)

      # Skip any entity for which we can't find any company data.
      if not company_data:
        self.logger.log_text("No company data found for entity: %s (%s)" % (
          name, mid), severity="DEBUG")
        continue
      self.logger.log_text("Found company data: %s" % company_data,
        severity="DEBUG")

      for company in company_data:
        # Extract and add a sentiment score.
        sentiment = self.get_sentiment(text)
        self.logger.log_text("Using sentiment for company: %s %s" % (sentiment,
          company), severity="DEBUG")
        company["sentiment"] = sentiment

        # Add the company to the list unless we already have it.
        duplicate = False
        for existing in companies:
          if existing["ticker"] == company["ticker"]:
            duplicate = True
            break
        if not duplicate:
          companies.append(company)

    return companies

  # Converts a list of entities to a readable string.
  def entities_tostring(self, entities):
    tostrings = [self.entity_tostring(entity) for entity in entities]
    return "[%s]" % ", ".join(tostrings)

  # Converts one entity to a readable string.
  def entity_tostring(self, entity):
    return ('{name: "%s", '
      'entity_type: "%s", '
      'wikipedia_url: "%s", '
      'metadata: "%s", '
      'salience: "%s", '
      'mentions: %s}') % (
      entity.name,
      entity.entity_type,
      entity.wikipedia_url,
      entity.metadata,
      entity.salience,
      ", ".join(['"%s"' % mention for mention in entity.mentions]))

  # Extract a sentiment score [-1, 1] from the text.
  def get_sentiment(self, text):
    try:
      document = self.gcnl_client.document_from_text(text)
      sentiment = document.analyze_sentiment()
    except:
      self.logger.log_text("Failed to analyze sentiment in text: %s" % text,
        severity="ERROR")
      return 0
    
    self.logger.log_text(
      "Sentiment score and magnitude for text: %s %s \"%s\"" % (sentiment.score,
      sentiment.magnitude, text), severity="DEBUG")
    return sentiment.score

#
# Tests
#

import pytest

@pytest.fixture
def analysis():
  return Analysis()

def test_get_company_data(analysis):
  assert analysis.get_company_data("/m/035nm") == [{
    "name": "General Motors",
    "ticker": "GM"}]
  assert analysis.get_company_data("/m/04n3_w4") == [{
    "name": "Fiat",
    "owner": "Fiat Chrysler Automobiles",
    "ticker": "FCAU"}]
  assert analysis.get_company_data("/m/0d8c4") == [{
    "name": "Lockheed Martin",
    "ticker": "LMT"}]
  assert analysis.get_company_data("/m/0hkqn") == [{
    "name": "Lockheed Martin",
    "ticker": "LMT"}]
  assert analysis.get_company_data("/m/09jcvs") == [{
    "name": "YouTube",
    "owner": "Google",
    "ticker": "GOOG"}, {
    "name": "YouTube",
    "owner": "Google",
    "ticker": "GOOGL"}]
  assert analysis.get_company_data("/m/045c7b") == [{
    "name": "Google",
    "ticker": "GOOG"}, {
    "name": "Google",
    "ticker": "GOOGL"}]
  assert analysis.get_company_data("/m/01snr1") == [{
    "name": "Bayer",
    "owner": "BlackRock",
    "ticker": "BLK"}, {
    "name": "Bayer",
    "owner": "PNC Financial Services",
    "ticker": "PNC"}]
  assert analysis.get_company_data("/m/02zs4") == [{
    "name": "Ford",
    "ticker": "F"}]
  assert analysis.get_company_data("/m/0841v") == [{
    "name": "Walmart",
    "ticker": "WMT"}, {
    "name": "Walmart",
    "owner": "State Street Corporation",
    "ticker": "STT"}]
  assert analysis.get_company_data("/m/07mb6") == [{
    "name": "Toyota",
    "ticker": "TM"}]
  assert analysis.get_company_data("/m/0178g") == [{
    "name": "Boeing",
    "ticker": "BA"}]
  assert analysis.get_company_data("/m/07_dc0") == [{
    "name": "Carrier Corporation",
    "owner": "United Technologies Corporation",
    "ticker": "UTX"}]
  assert analysis.get_company_data("/m/0d6lp") == []
  assert analysis.get_company_data("xyz") == []
  assert analysis.get_company_data("") == []

TEXT_1 = ("Boeing is building a brand new 747 Air Force One for future presiden"
          "ts, but costs are out of control, more than $4 billion. Cancel order"
          "!")
TEXT_2 = ("Based on the tremendous cost and cost overruns of the Lockheed Marti"
          "n F-35, I have asked Boeing to price-out a comparable F-18 Super Hor"
          "net!")
TEXT_3 = ("General Motors is sending Mexican made model of Chevy Cruze to U.S. "
          "car dealers-tax free across border. Make in U.S.A.or pay big border "
          "tax!")
TEXT_4 = ('"@DanScavino: Ford to scrap Mexico plant, invest in Michigan due to '
          'Trump policies" http://www.foxnews.com/politics/2017/01/03/ford-to-s'
          'crap-mexico-plant-invest-in-michigan-due-to-trump-policies.html')
TEXT_5 = ("Thank you to Ford for scrapping a new plant in Mexico and creating 7"
          "00 new jobs in the U.S. This is just the beginning - much more to fo"
          "llow")
TEXT_6 = ("Toyota Motor said will build a new plant in Baja, Mexico, to build C"
          "orolla cars for U.S. NO WAY! Build plant in U.S. or pay big border t"
          "ax.")
TEXT_7 = ("It's finally happening - Fiat Chrysler just announced plans to inves"
          "t $1BILLION in Michigan and Ohio plants, adding 2000 jobs. This afte"
          "r...")
TEXT_8 = ("Ford said last week that it will expand in Michigan and U.S. instead"
          " of building a BILLION dollar plant in Mexico. Thank you Ford & Fiat"
          " C!")
TEXT_9 = ("Thank you to General Motors and Walmart for starting the big jobs pu"
          "sh back into the U.S.!")
TEXT_10 = ("Totally biased @NBCNews went out of its way to say that the big ann"
           "ouncement from Ford, G.M., Lockheed & others that jobs are coming b"
           "ack...")
TEXT_11 = ('"Bayer AG has pledged to add U.S. jobs and investments after meetin'
           'g with President-elect Donald Trump, the latest in a string..." @WS'
           'J')

# TODO: Make commented-out ones work.
def test_get_sentiment(analysis):
  assert analysis.get_sentiment(TEXT_1) < 0
  #assert analysis.get_sentiment(TEXT_2) < 0
  assert analysis.get_sentiment(TEXT_3) < 0
  assert analysis.get_sentiment(TEXT_4) > 0
  assert analysis.get_sentiment(TEXT_5) > 0
  assert analysis.get_sentiment(TEXT_6) < 0
  assert analysis.get_sentiment(TEXT_7) > 0
  assert analysis.get_sentiment(TEXT_8) > 0
  assert analysis.get_sentiment(TEXT_9) > 0
  #assert analysis.get_sentiment(TEXT_10) > 0
  assert analysis.get_sentiment(TEXT_11) > 0
  assert analysis.get_sentiment("") == 0

# TODO: Make commented-out ones work.
def test_find_companies(analysis):
  assert analysis.find_companies(TEXT_1) == [{
    "name": "Boeing",
    "sentiment": -0.1,
    "ticker": "BA"}]
  #assert analysis.find_companies(TEXT_2) == [{
  #  "name": "Lockheed Martin",
  #  "sentiment": -0.1,
  #  "ticker": "LMT"}, {
  #  "name": "Boeing",
  #  "sentiment": 0.1,
  #  "ticker": "BA"}]
  assert analysis.find_companies(TEXT_3) == [{
    "name": "General Motors",
    "sentiment": -0.1,
    "ticker": "GM"}]
  assert analysis.find_companies(TEXT_4) == [{
    "name": "Ford",
    "sentiment": 0.3,
    "ticker": "F"}]
  assert analysis.find_companies(TEXT_5) == [{
    "name": "Ford",
    "sentiment": 0.3,
    "ticker": "F"}]
  assert analysis.find_companies(TEXT_6) == [{
    "name": "Toyota",
    "sentiment": -0.2,
    "ticker": "TM"}]
  assert analysis.find_companies(TEXT_7) == [{
    "name": "Fiat",
    "owner": "Fiat Chrysler Automobiles",
    "sentiment": 0.2,
    "ticker": "FCAU"}]
  assert analysis.find_companies(TEXT_8) == [{
    "name": "Ford",
    "sentiment": 0.3,
    "ticker": "F"}, {
    "name": "Fiat",
    "owner": "Fiat Chrysler Automobiles",
    "sentiment": 0.3,
    "ticker": "FCAU"}]
  assert analysis.find_companies(TEXT_9) == [{
    "name": "General Motors",
    "sentiment": 0.4,
    "ticker": "GM"}, {
    "name": "Walmart",
    "sentiment": 0.4,
    "ticker": "WMT"}, {
    "name": "Walmart",
    "owner": "State Street Corporation",
    "sentiment": 0.4,
    "ticker": "STT"}]
  #assert analysis.find_companies(TEXT_10) == [{
  #  "name": "Ford",
  #  "sentiment": 0,
  #  "ticker": "F"}, {
  #  "name": "General Motors",
  #  "sentiment": 0,
  #  "ticker": "GM"}, {
  #  "name": "Lockheed Martin",
  #  "sentiment": 0,
  #  "ticker": "LMT"}]
  assert analysis.find_companies(TEXT_11) == [{
    "name": "Bayer",
    "sentiment": 0.3,
    "owner": "BlackRock",
    "ticker": "BLK"}, {
    "name": "Bayer",
    "sentiment": 0.3,
    "owner": "PNC Financial Services",
    "ticker": "PNC"}]
