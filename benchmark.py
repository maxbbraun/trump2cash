#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import timedelta

from analysis import Analysis
from trading import Trading
from twitter import Twitter

# TODO: Consider older tweets: 621669173534584833, 664911913831301123,
#       672926510924374016, 803808454620094465
# The IDs of all Trump tweets that mention companies.
TWEET_IDS = ["806134244384899072", "812061677160202240", "816260343391514624",
             "816324295781740544", "816635078067490816", "817071792711942145",
             "818460862675558400", "818461467766824961", "821415698278875137",
             "821697182235496450", "821703902940827648", "823950814163140609",
             "824055927200423936", "826041397232943104"]

# The initial amount in dollars for the fund simulation.
FUND_DOLLARS = 10000

# The fee in dollars per trade.
TRADE_FEE = 4.95

def ratio_to_return(ratio):
    """Converts a ratio to a readable percentage return."""

    return "%.3f%%" % (100 * (ratio - 1))

def format_dollar(amount):
    """Converts a dollar amount into a readable string."""

    return "${:,.2f}".format(amount)

def format_timestamp(timestamp, weekday=False):
    """Converts a timestamp into a readable string."""

    date_format = "%-m/%-d %Y %-I:%M %p"
    if weekday:
        date_format += " (%A)"
    return timestamp.strftime(date_format)

def get_ratio(strategy):
    """Calculates the profit ratio of a strategy."""

    price_at = strategy["price_at"]
    price_eod = strategy["price_eod"]
    if price_at and price_eod:
        action = strategy["action"]
        if action == "bull":
            return price_eod / price_at
        elif action == "bear":
            return price_at / price_eod
        else:
            return 1.0
    else:
        return 1.0

def get_sentiment_emoji(sentiment):
    """Returns an emoji representing the sentiment score."""

    if sentiment == 0:
        return ":neutral_face:"
    elif sentiment > 0:
        return ":thumbsup:"
    else:  # sentiment < 0:
        return ":thumbsdown:"

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

# TODO: Refactor trading so this logic can live there.
def should_trade(strategy, date, previous_date):
    """Determines whether a trade is happening for the strategy."""

    # We invest the whole value, so we can only trade once a day.
    if (previous_date and previous_date.year == date.year
        and previous_date.month == date.month
        and previous_date.day == date.day):
        return False

    # The strategy needs to be active.
    if strategy["action"] == "hold":
        return False

    return True

if __name__ == "__main__":
    analysis = Analysis(logs_to_cloud=False)
    trading = Trading(logs_to_cloud=False)
    twitter = Twitter(logs_to_cloud=False)

    # Look up the metadata for the tweets.
    tweets = twitter.get_tweets(TWEET_IDS)

    events = []
    for tweet in tweets:
        event = {}

        timestamp = trading.utc_to_market_time(tweet.created_at)
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
            price = trading.get_historical_prices(
                company["ticker"], timestamp)
            if price:
                strategy["price_at"] = price["at"]
                strategy["price_eod"] = price["eod"]
            else:
                strategy["price_at"] = None
                strategy["price_eod"] = None

            strategies.append(strategy)

        event["strategies"] = strategies

        events.append(event)

    #if not events:
    #    return

    # Make sure the events are ordered by ascending timestatmp.
    events = sorted(events, key=lambda event: event["timestamp"])

    # Print out the formatted benchmark results as markdown.
    print "## Benchmark Report"
    print
    print ("This breakdown of the analysis results and market performance valid"
           "ates the current implementation against historical data.")
    print
    print ("Use this command to regenerate the benchmark report after changes t"
           "o the algorithm or data:")
    print "```shell"
    print "$ ./benchmark.py > benchmark.md"
    print "```"

    print
    print "### Events overview"
    print
    print ("Here's each tweet with the results of its analysis and individual m"
           "arket performance.")

    for event in events:
        timestamp = format_timestamp(event["timestamp"], weekday=True)
        print
        print "##### [%s](%s)" % (timestamp, event["link"])
        print
        print "> %s" % event["text"]
        print

        strategies = event["strategies"]
        if strategies:
            print "*Strategy*"
            print
            print "Company | Root | Sentiment | Strategy | Reason"
            print "--------|------|-----------|----------|-------"

            for strategy in strategies:
                root = "-" if "root" not in strategy else strategy["root"]
                sentiment = strategy["sentiment"]
                sentiment_emoji = get_sentiment_emoji(sentiment)
                print "%s | %s | %s %s | %s | %s" % (strategy["name"], root,
                    sentiment, sentiment_emoji, strategy["action"],
                    strategy["reason"])

            print
            print "*Performance*"
            print
            print "Ticker | Exchange | Price @ tweet | Price EOD | Return"
            print "-------|----------|---------------|-----------|-------"

            for strategy in strategies:
                price_at = strategy["price_at"]
                price_eod = strategy["price_eod"]
                if price_at and price_eod:
                    price_at_str = format_dollar(price_at)
                    price_eod_str = format_dollar(price_eod)
                else:
                    price_at_str = "-"
                    price_eod_str = "-"
                ratio = get_ratio(strategy)
                total_return = ratio_to_return(ratio)
                print "%s | %s | %s | %s | %s" % (strategy["ticker"],
                    strategy["exchange"], price_at_str, price_eod_str,
                    total_return)
        else:
            print "*(No companies)*"

    print
    print "### Fund simulation"
    print
    print ("This is how an initial investment of %s would have grown, including"
           " [TradeKing's fees](https://www.tradeking.com/rates) of %s per trad"
           "e.") % (format_dollar(FUND_DOLLARS), format_dollar(TRADE_FEE))
    print
    print "Time | Trade | Value | Return | Annualized"
    print "-----|-------|-------|--------|-----------"
    start_date = events[0]["timestamp"]
    value = FUND_DOLLARS
    print "*Initial* | - | *%s* | - | -" % format_dollar(value)

    previous_date = None
    for event in events:
        date = event["timestamp"]

        # TODO: Properly handle multiple trades (split budget).
        strategies = event["strategies"]
        for strategy in strategies:
            trade = should_trade(strategy, date, previous_date)
            if trade:
                value -= TRADE_FEE
                ratio = get_ratio(strategy)
                value *= ratio
                previous_date = date

            total_ratio = value / FUND_DOLLARS
            total_return = ratio_to_return(total_ratio)
            if date != start_date:
                days = (date - start_date).days
                annualized_return = ratio_to_return(
                    pow(total_ratio, 365.0 / days))
            else:
                annualized_return = "-"

            date_str = format_timestamp(date)
            trade_str = "%s %s" % (strategy["ticker"],
                get_sentiment_emoji(strategy["sentiment"]))

            if trade:
                date_str = "**%s**" % date_str
                trade_str = "**%s**" % trade_str

            print "%s | %s | %s | %s | %s" % (date_str, trade_str,
                format_dollar(value), total_return, annualized_return)
