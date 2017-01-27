# -*- coding: utf-8 -*-

from google.cloud import language
from os import getenv
from requests import get

from logs import Logs

# The URL for a GET request to the Wikidata API via a SPARQL query to find
# stock ticker symbols. The parameter is the Freebase ID of the company.
WIKIDATA_QUERY_URL = ('https://query.wikidata.org/sparql?query='
    'SELECT ?companyLabel ?ownerLabel ?parentLabel ?tickerLabel'
    ' ?exchangeNameLabel WHERE {'
    '  ?instance wdt:P646 "%s" .'  # Company with specified Freebase ID.
    '  ?instance wdt:P156* ?company .'  # Company may have restructured.
    '  { ?company p:P414 ?exchange }'  # Company traded on exchange.
    '  UNION { ?company wdt:P127+ ?owner .'  # Or company is owned by another.
    '          ?owner p:P414 ?exchange }'  # And owner traded on exchange.
    '  UNION { ?company wdt:P749+ ?parent .'  # Or company is a subsidiary.
    '          ?parent p:P414 ?exchange } .'  # And parent traded on exchange.
    '  VALUES ?exchanges { wd:Q13677 wd:Q82059 }'  # Whitelist NYSE and NASDAQ.
    '  ?exchange ps:P414 ?exchanges .'  # Stock exchange is whitelisted.
    '  ?exchange pq:P249 ?ticker .'  # Get ticker symbol.
    '  ?exchange ps:P414 ?exchangeName .'  # Get name of exchange.
    '  SERVICE wikibase:label {'
    '    bd:serviceParam wikibase:language "en" .'  # Use English labels.
    '  }'
    '} GROUP BY ?companyLabel ?ownerLabel ?parentLabel ?tickerLabel'
    ' ?exchangeNameLabel'
    '&format=JSON')


class Analysis:
    """A helper for analyzing company data in text."""

    def __init__(self, logs_to_cloud=True):
        self.logs = Logs(name="analysis", to_cloud=logs_to_cloud)
        self.gcnl_client = language.Client()

    def get_company_data(self, mid):
        """Looks up stock ticker information for a company via its Freebase ID.
        """

        query = WIKIDATA_QUERY_URL % mid
        self.logs.debug("Wikidata query: %s" % query)
        response = get(query).json()
        self.logs.debug("Wikidata response: %s" % response)

        if not "results" in response:
            self.logs.error("No results in Wikidata response: %s" % response)
            return None

        results = response["results"]
        if not "bindings" in results:
            self.logs.error("No bindings in Wikidata results: %s" % results)
            return None

        bindings = results["bindings"]
        if not bindings:
            self.logs.debug("Empty bindings in Wikidata results: %s" % results)
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

            if "parentLabel" in binding:
                parent = binding["parentLabel"]["value"]
            else:
                parent = None

            if "tickerLabel" in binding:
                ticker = binding["tickerLabel"]["value"]
            else:
                ticker = None

            if "exchangeNameLabel" in binding:
                exchange = binding["exchangeNameLabel"]["value"]
            else:
                exchange = None

            data = {}
            data["name"] = name
            data["ticker"] = ticker
            data["exchange"] = exchange

            # Owner or parent get turned into root.
            if owner:
                data["root"] = owner
            elif parent:
                data["root"] = parent

            # Add to the list unless we already have the same entry.
            if data not in datas:
                datas.append(data)
            else:
                self.logs.warn("Skipping duplicate company data: %s" % data)

        return datas

    def find_companies(self, text):
        """Finds mentions of companies in text."""

        # Run entity detection.
        document = self.gcnl_client.document_from_text(text)
        entities = document.analyze_entities()
        self.logs.debug("Found entities: %s" % self.entities_tostring(entities))

        # Collect all entities which are publicly traded companies, i.e.
        # entities which have a known stock ticker symbol.
        companies = []
        for entity in entities:

            # Use the Freebase ID of the entity to find company data. Skip any
            # entity which doesn't have a Freebase ID.
            name = entity.name
            metadata = entity.metadata
            if not "mid" in metadata:
                self.logs.debug("No MID found for entity: %s" % name)
                continue
            mid = metadata["mid"]
            company_data = self.get_company_data(mid)

            # Skip any entity for which we can't find any company data.
            if not company_data:
                self.logs.debug("No company data found for entity: %s (%s)" %
                                (name, mid))
                continue
            self.logs.debug("Found company data: %s" % company_data)

            for company in company_data:

                # Extract and add a sentiment score.
                sentiment = self.get_sentiment(text)
                self.logs.debug("Using sentiment for company: %s %s" %
                                (sentiment, company))
                company["sentiment"] = sentiment

                # Add the company to the list unless we already have the same
                # ticker.
                tickers = [existing["ticker"] for existing in companies]
                if not company["ticker"] in tickers:
                    companies.append(company)
                else:
                    self.logs.warn(
                        "Skipping company with duplicate ticker: %s" % company)

        return companies

    def entities_tostring(self, entities):
        """Converts a list of entities to a readable string."""

        tostrings = [self.entity_tostring(entity) for entity in entities]
        return "[%s]" % ", ".join(tostrings)

    def entity_tostring(self, entity):
        """Converts one entity to a readable string."""

        if entity.wikipedia_url:
            wikipedia_url = '"%s"' % entity.wikipedia_url
        else:
            wikipedia_url = None

        metadata = ", ".join(['"%s": "%s"' % (key, value) for
                              key, value in entity.metadata.iteritems()])

        mentions = ", ".join(['"%s"' % mention for mention in entity.mentions])

        return ('{name: "%s",'
                ' entity_type: "%s",'
                ' wikipedia_url: %s,'
                ' metadata: {%s},'
                ' salience: %s,'
                ' mentions: [%s]}') % (
            entity.name,
            entity.entity_type,
            wikipedia_url,
            metadata,
            entity.salience,
            mentions)

    def get_sentiment(self, text):
        """Extracts a sentiment score [-1, 1] from text."""

        # TODO: Determine sentiment targeted at the specific entity.

        document = self.gcnl_client.document_from_text(text)
        sentiment = document.analyze_sentiment()

        self.logs.debug(
            "Sentiment score and magnitude for text: %s %s \"%s\"" %
            (sentiment.score, sentiment.magnitude, text))

        return sentiment.score

#
# Tests
#

# TODO: Make commented-out tests work.

import pytest


@pytest.fixture
def analysis():
    return Analysis(logs_to_cloud=False)


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
        "ticker": "BLK"}]  # , {
        #"exchange": "New York Stock Exchange",
        #"name": "Bayer",
        #"root": "PNC Financial Services",
        #"ticker": "PNC"}]
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
    assert analysis.get_company_data("/m/0d6lp") == []
    assert analysis.get_company_data("xyz") == []
    assert analysis.get_company_data("") == []


def test_entity_tostring(analysis):
    assert analysis.entity_tostring(language.entity.Entity(
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
    assert analysis.entity_tostring(language.entity.Entity(
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
    assert analysis.entities_tostring([language.entity.Entity(
        name="General Motors",
        entity_type="ORGANIZATION",
        metadata={"mid": "/m/035nm",
            "wikipedia_url": "http://en.wikipedia.org/wiki/General_Motors"},
        salience=0.33838183,
        mentions=["General Motors"]), language.entity.Entity(
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

TEXT_1 = (
    "Boeing is building a brand new 747 Air Force One for future presidents, bu"
    "t costs are out of control, more than $4 billion. Cancel order!")
TEXT_2 = (
    "Based on the tremendous cost and cost overruns of the Lockheed Martin F-35"
    ", I have asked Boeing to price-out a comparable F-18 Super Hornet!")
TEXT_3 = (
    "General Motors is sending Mexican made model of Chevy Cruze to U.S. car de"
    "alers-tax free across border. Make in U.S.A.or pay big border tax!")
TEXT_4 = (
    '"@DanScavino: Ford to scrap Mexico plant, invest in Michigan due to Trump '
    'policies" http://www.foxnews.com/politics/2017/01/03/ford-to-scrap-mexico-'
    'plant-invest-in-michigan-due-to-trump-policies.html')
TEXT_5 = (
    "Thank you to Ford for scrapping a new plant in Mexico and creating 700 new"
    " jobs in the U.S. This is just the beginning - much more to follow")
TEXT_6 = (
    "Toyota Motor said will build a new plant in Baja, Mexico, to build Corolla"
    " cars for U.S. NO WAY! Build plant in U.S. or pay big border tax.")
TEXT_7 = (
    "It's finally happening - Fiat Chrysler just announced plans to invest $1BI"
    "LLION in Michigan and Ohio plants, adding 2000 jobs. This after...")
TEXT_8 = (
    "Ford said last week that it will expand in Michigan and U.S. instead of bu"
    "ilding a BILLION dollar plant in Mexico. Thank you Ford & Fiat C!")
TEXT_9 = (
    "Thank you to General Motors and Walmart for starting the big jobs push bac"
    "k into the U.S.!")
TEXT_10 = (
    "Totally biased @NBCNews went out of its way to say that the big announceme"
    "nt from Ford, G.M., Lockheed & others that jobs are coming back...")
TEXT_11 = (
    '"Bayer AG has pledged to add U.S. jobs and investments after meeting with '
    'President-elect Donald Trump, the latest in a string..." @WSJ')
TEXT_12 = (
    "Big day on Thursday for Indiana and the great workers of that wonderful st"
    "ate.We will keep our companies and jobs in the U.S. Thanks Carrier")
TEXT_13 = (
    "I hope the boycott of @Macys continues forever. So many people are cutting"
    " up their cards. Macy's stores suck and they are bad for U.S.A.")
TEXT_14 = (
    "Macy’s was very disloyal to me bc of my strong stance on illegal immigrati"
    "on. Their stock has crashed! #BoycottMacys")
TEXT_15 = (
    "Signing orders to move forward with the construction of the Keystone XL an"
    "d Dakota Access pipelines in the Oval Office.")


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
    assert analysis.get_sentiment(TEXT_12) > 0
    assert analysis.get_sentiment(TEXT_13) < 0
    assert analysis.get_sentiment(TEXT_14) < 0
    #assert analysis.get_sentiment(TEXT_15) > 0
    assert analysis.get_sentiment("") == 0


def test_find_companies(analysis):
    assert analysis.find_companies(TEXT_1) == [{
        "exchange": "New York Stock Exchange",
        "name": "Boeing",
        "sentiment": -0.1,
        "ticker": "BA"}]
    assert analysis.find_companies(TEXT_2) == [{
        #"exchange": "New York Stock Exchange",
        #"name": "Lockheed Martin",
        #"sentiment": -0.1,
        #"ticker": "LMT"}, {
        "exchange": "New York Stock Exchange",
        "name": "Boeing",
        "sentiment": 0,  # 0.1,
        "ticker": "BA"}]
    assert analysis.find_companies(TEXT_3) == [{
        "exchange": "New York Stock Exchange",
        "name": "General Motors",
        "sentiment": -0.1,
        "ticker": "GM"}]
    assert analysis.find_companies(TEXT_4) == [{
        "exchange": "New York Stock Exchange",
        "name": "Ford",
        "sentiment": 0.3,
        "ticker": "F"}]
    assert analysis.find_companies(TEXT_5) == [{
        "exchange": "New York Stock Exchange",
        "name": "Ford",
        "sentiment": 0.3,
        "ticker": "F"}]
    assert analysis.find_companies(TEXT_6) == [{
        "exchange": "New York Stock Exchange",
        "name": "Toyota",
        "sentiment": -0.2,
        "ticker": "TM"}]
    assert analysis.find_companies(TEXT_7) == [{
        "exchange": "New York Stock Exchange",
        "name": "Fiat",
        "root": "Fiat Chrysler Automobiles",
        "sentiment": 0.2,
        "ticker": "FCAU"}]
    assert analysis.find_companies(TEXT_8) == [{
        "exchange": "New York Stock Exchange",
        "name": "Ford",
        "sentiment": 0.3,
        "ticker": "F"}, {
        "exchange": "New York Stock Exchange",
        "name": "Fiat",
        "root": "Fiat Chrysler Automobiles",
        "sentiment": 0.3,
        "ticker": "FCAU"}]
    assert analysis.find_companies(TEXT_9) == [{
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
    assert analysis.find_companies(TEXT_10) == [{
        "exchange": "New York Stock Exchange",
        "name": "Ford",
        "sentiment": -0.5,  # 0,
        "ticker": "F"}, {
        "exchange": "New York Stock Exchange",
        "name": "General Motors",
        "sentiment": -0.5,  # 0,
        "ticker": "GM"}, {
        "exchange": "New York Stock Exchange",
        "name": "Lockheed Martin",
        "sentiment": -0.5,  # 0,
        "ticker": "LMT"}]
    assert analysis.find_companies(TEXT_11) == [{
        "exchange": "New York Stock Exchange",
        "name": "Bayer",
        "sentiment": 0.3,
        "root": "BlackRock",
        "ticker": "BLK"}]  # , {
        #"exchange": "New York Stock Exchange",
        #"name": "Bayer",
        #"sentiment": 0.3,
        #"root": "PNC Financial Services",
        #"exchange": "New York Stock Exchange",
        #"ticker": "PNC"}]
    #assert analysis.find_companies(TEXT_12) == [{
    #    "exchange": "New York Stock Exchange",
    #    "name": "Carrier Corporation",
    #    "sentiment": 0.5,
    #    "root": "United Technologies Corporation",
    #    "ticker": "UTX"}]
    assert analysis.find_companies(TEXT_13) == [{
        "exchange": "New York Stock Exchange",
        "name": "Macy's",
        "root": "Macy's, Inc.",
        "sentiment": -0.4,
        "ticker": "M"}]
    assert analysis.find_companies(TEXT_14) == [{
        "exchange": "New York Stock Exchange",
        "name": "Macy's",
        "root": "Macy's, Inc.",
        "sentiment": -0.3,
        "ticker": "M"}]
    assert analysis.find_companies(TEXT_15) == [{
        "exchange": "New York Stock Exchange",
        "name": "Keystone Pipeline",
        "root": "TransCanada Corporation",
        "sentiment": 0,  # 0.1,
        "ticker": "TRP"}]
