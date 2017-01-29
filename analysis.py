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

    def __init__(self, logs_to_cloud):
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
