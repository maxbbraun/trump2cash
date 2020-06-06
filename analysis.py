from backoff import expo
from backoff import on_exception
from google.cloud import language
from re import compile
from re import IGNORECASE
from requests import get
from requests.exceptions import HTTPError
from urllib.parse import quote_plus

from logs import Logs
from twitter import Twitter

from dotenv import load_dotenv
load_dotenv()

# The URL for a GET request to the Wikidata API. The string parameter is the
# SPARQL query.
WIKIDATA_QUERY_URL = "https://query.wikidata.org/sparql?query=%s&format=JSON"

# The HTTP headers with a User-Agent used for Wikidata requests.
WIKIDATA_QUERY_HEADERS = {
    "User-Agent": "Trump2Cash/1.0 (https://trump2cash.biz)"}

# A Wikidata SPARQL query to find stock ticker symbols and other information
# for a company. The string parameter is the Freebase ID of the company.
MID_TO_TICKER_QUERY = (
    'SELECT ?companyLabel ?rootLabel ?tickerLabel ?exchangeNameLabel'
    ' WHERE {'
    '  ?entity wdt:P646 "%s" .'  # Entity with specified Freebase ID.
    '  ?entity wdt:P176* ?manufacturer .'  # Entity may be product.
    '  ?manufacturer wdt:P1366* ?company .'  # Company may have restructured.
    '  { ?company p:P414 ?exchange } UNION'  # Company traded on exchange ...
    '  { ?company wdt:P127+ / wdt:P1366* ?root .'  # ... or company has owner.
    '    ?root p:P414 ?exchange } UNION'  # Owner traded on exchange or ...
    '  { ?company wdt:P749+ / wdt:P1366* ?root .'  # ... company has parent.
    '    ?root p:P414 ?exchange } .'  # Parent traded on exchange.
    '  VALUES ?exchanges { wd:Q13677 wd:Q82059 } .'  # Whitelist NYSE, NASDAQ.
    '  ?exchange ps:P414 ?exchanges .'  # Stock exchange is whitelisted.
    '  ?exchange pq:P249 ?ticker .'  # Get ticker symbol.
    '  ?exchange ps:P414 ?exchangeName .'  # Get name of exchange.
    '  FILTER NOT EXISTS { ?company wdt:P31 /'  # Exclude newspapers.
    '                               wdt:P279* wd:Q11032 } .'
    '  FILTER NOT EXISTS { ?company wdt:P31 /'  # Exclude news agencies.
    '                               wdt:P279* wd:Q192283 } .'
    '  FILTER NOT EXISTS { ?company wdt:P31 /'  # Exclude news magazines.
    '                               wdt:P279* wd:Q1684600 } .'
    '  FILTER NOT EXISTS { ?company wdt:P31 /'  # Exclude radio stations.
    '                               wdt:P279* wd:Q14350 } .'
    '  FILTER NOT EXISTS { ?company wdt:P31 /'  # Exclude TV stations.
    '                               wdt:P279* wd:Q1616075 } .'
    '  FILTER NOT EXISTS { ?company wdt:P31 /'  # Exclude TV channels.
    '                               wdt:P279* wd:Q2001305 } .'
    '  SERVICE wikibase:label {'
    '   bd:serviceParam wikibase:language "en" .'  # Use English labels.
    '  }'
    ' } GROUP BY ?companyLabel ?rootLabel ?tickerLabel ?exchangeNameLabel'
    ' ORDER BY ?companyLabel ?rootLabel ?tickerLabel ?exchangeNameLabel')


class Analysis:
    """A helper for analyzing company data in text."""

    def __init__(self, logs_to_cloud):
        self.logs = Logs(name="analysis", to_cloud=logs_to_cloud)
        self.language_client = language.LanguageServiceClient()
        self.twitter = Twitter(logs_to_cloud=logs_to_cloud)

    def get_company_data(self, mid):
        """Looks up stock ticker information for a company via its Freebase ID.
        """

        query = MID_TO_TICKER_QUERY % mid
        try:
            bindings = self.make_wikidata_request(query)
        except HTTPError as e:
            self.logs.error("Wikidata request failed: %s" % e)
            bindings = None

        if not bindings:
            self.logs.debug("No company data found for MID: %s" % mid)
            return None

        # Collect the data from the response.
        datas = []
        for binding in bindings:
            try:
                name = binding["companyLabel"]["value"]
            except KeyError:
                name = None

            try:
                root = binding["rootLabel"]["value"]
            except KeyError:
                root = None

            try:
                ticker = binding["tickerLabel"]["value"]
            except KeyError:
                ticker = None

            try:
                exchange = binding["exchangeNameLabel"]["value"]
            except KeyError:
                exchange = None

            data = {"name": name,
                    "ticker": ticker,
                    "exchange": exchange}

            # Add the root if there is one.
            if root and root != name:
                data["root"] = root

            # Add to the list unless we already have the same entry.
            if data not in datas:
                self.logs.debug("Adding company data: %s" % data)
                datas.append(data)
            else:
                self.logs.warn("Skipping duplicate company data: %s" % data)

        return datas

    def find_companies(self, tweet):
        """Finds mentions of companies in a tweet."""

        if not tweet:
            self.logs.warn("No tweet to find companies.")
            return None

        # Use the text of the tweet with any mentions expanded to improve
        # entity detection.
        text = self.get_expanded_text(tweet)
        if not text:
            self.logs.error("Failed to get text from tweet: %s" % tweet)
            return None

        # Run entity detection.
        document = language.types.Document(
            content=text,
            type=language.enums.Document.Type.PLAIN_TEXT,
            language="en")
        entities = self.language_client.analyze_entities(document).entities
        self.logs.debug("Found entities: %s" %
                        self.entities_tostring(entities))

        # Collect all entities which are publicly traded companies, i.e.
        # entities which have a known stock ticker symbol.
        companies = []
        for entity in entities:

            # Use the Freebase ID of the entity to find company data. Skip any
            # entity which doesn't have a Freebase ID (unless we find one via
            # the Twitter handle).
            name = entity.name
            metadata = entity.metadata
            try:
                mid = metadata["mid"]
            except KeyError:
                self.logs.debug("No MID found for entity: %s" % name)
                continue

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
                self.logs.debug("Using sentiment for company: %f %s" %
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

    def get_expanded_text(self, tweet):
        """Retrieves the text from a tweet with any @mentions expanded to
        their full names.
        """

        if not tweet:
            self.logs.warn("No tweet to expand text.")
            return None

        try:
            text = self.twitter.get_tweet_text(tweet)
            mentions = tweet["entities"]["user_mentions"]
        except KeyError:
            self.logs.error("Malformed tweet: %s" % tweet)
            return None

        if not text:
            self.logs.warn("Empty text.")
            return None

        if not mentions:
            self.logs.debug("No mentions.")
            return text

        self.logs.debug("Using mentions: %s" % mentions)
        for mention in mentions:
            try:
                screen_name = "@%s" % mention["screen_name"]
                name = mention["name"]
            except KeyError:
                self.logs.warn("Malformed mention: %s" % mention)
                continue

            self.logs.debug("Expanding mention: %s %s" % (screen_name, name))
            pattern = compile(screen_name, IGNORECASE)
            text = pattern.sub(name, text)

        return text

    @on_exception(expo, HTTPError, max_tries=8)
    def make_wikidata_request(self, query):
        """Makes a request to the Wikidata SPARQL API."""

        query_url = WIKIDATA_QUERY_URL % quote_plus(query)
        self.logs.debug("Wikidata query: %s" % query_url)

        response = get(query_url, headers=WIKIDATA_QUERY_HEADERS)
        response.raise_for_status()

        try:
            response_json = response.json()
        except ValueError:
            self.logs.error("Failed to decode JSON response: %s" % response)
            return None
        self.logs.debug("Wikidata response: %s" % response_json)

        try:
            results = response_json["results"]
            bindings = results["bindings"]
        except KeyError:
            self.logs.error("Malformed Wikidata response: %s" % response_json)
            return None

        return bindings

    def entities_tostring(self, entities):
        """Converts a list of entities to a readable string."""

        tostrings = [self.entity_tostring(entity) for entity in entities]
        return "[%s]" % ", ".join(tostrings)

    def entity_tostring(self, entity):
        """Converts one entity to a readable string."""

        metadata = ", ".join(['"%s": "%s"' % (key, value) for
                              key, value in entity.metadata.items()])

        mentions = ", ".join(['"%s"' % mention for mention in entity.mentions])

        return ('{name: "%s",'
                ' type: "%s",'
                ' metadata: {%s},'
                ' salience: %s,'
                ' mentions: [%s]}') % (
            entity.name,
            entity.type,
            metadata,
            entity.salience,
            mentions)

    def get_sentiment(self, text):
        """Extracts a sentiment score [-1, 1] from text."""

        if not text:
            self.logs.warn("No sentiment for empty text.")
            return 0

        document = language.types.Document(
            content=text,
            type=language.enums.Document.Type.PLAIN_TEXT,
            language="en")
        sentiment = self.language_client.analyze_sentiment(
            document).document_sentiment

        self.logs.debug(
            "Sentiment score and magnitude for text: %f %f \"%s\"" %
            (sentiment.score, sentiment.magnitude, text))

        return sentiment.score
