#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime
from pytz import timezone
from pytz import utc

from analysis import Analysis
from logs import Logs
from trading import Trading
from twitter import Twitter

# The IDs of all Trump tweets that mention companies.
TWEET_IDS = ["806134244384899072", "812061677160202240", "816260343391514624",
             "816324295781740544", "816635078067490816", "817071792711942145",
             "818460862675558400", "818461467766824961", "821415698278875137",
             "821697182235496450", "821703902940827648", "823950814163140609",
             "824055927200423936"]

# We're using NYSE and NASDAQ, which are both in the easters timezone.
MARKET_TIMEZONE = timezone("US/Eastern")

def convert_market_time(timestamp):
    """Converts a UTC timestamp to local market time."""

    market_time = timestamp.replace(tzinfo=utc).astimezone(MARKET_TIMEZONE)
    MARKET_TIMEZONE.normalize(market_time)
    return market_time

def get_market_status(timestamp):
    """Tries to infer the market status from a timestamp."""

    # Closed on weekends.
    if timestamp.weekday() in [5, 6]:
        return "closed"

    # TODO: Closed on holidays.
    # TODO: Support irregular hours.

    # Calculate the market hours for the given day. These are the same for NYSE
    # and NASDAQ and include TradeKing's extended hours.
    pre_time = timestamp.replace(hour=8)
    open_time = timestamp.replace(hour=9, minute=30)
    close_time = timestamp.replace(hour=16)
    after_time = timestamp.replace(hour=17)

    # Return the market status for each bucket.
    if timestamp >= pre_time and timestamp < open_time:
        return "pre"
    elif timestamp >= open_time and timestamp < close_time:
        return "open"
    elif timestamp >= close_time and timestamp < after_time:
        return "after"
    else:
        return "closed"

if __name__ == "__main__":
    logs = Logs(name="main", to_cloud=False)
    analysis = Analysis(logs_to_cloud=False)
    trading = Trading(logs_to_cloud=False)
    twitter = Twitter(logs_to_cloud=False)

    # Look up the metadata for the tweets.
    tweets = twitter.get_tweets(TWEET_IDS)

    events = []
    for tweet in tweets:
        event = {}

        timestamp = convert_market_time(tweet.created_at)
        text = tweet.text.encode("utf-8")
        event["timestamp"] = timestamp
        event["text"] = text
        event["link"] = "https://twitter.com/%s/status/%s" % (
            tweet.user.screen_name, tweet.id_str)

        # Extract the companies.
        companies = analysis.find_companies(text)

        strategies = []
        for company in companies:

            # What would have been the strategy?
            market_status = get_market_status(timestamp)
            strategy = trading.get_strategy(company, market_status)
            
            # What was the price at tweet and at EOD?
            # TODO

            strategies.append(strategy)

        event["strategies"] = strategies

        events.append(event)

    # Make sure the events are ordered by ascending timestatmp.
    events = sorted(events, key=lambda event: event["timestamp"])

    # Print out the formatted benchmark results.
    for event in events:
        print
        print event["timestamp"].strftime("%Y-%m-%d %a %H:%M:%S")
        print event["link"]
        print '"%s"' % event["text"]
        for strategy in event["strategies"]:
            print "$%s %s (%s)" % (strategy["ticker"], strategy["action"],
                                    strategy["reason"])
