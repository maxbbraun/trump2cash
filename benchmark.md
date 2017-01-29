## Benchmark Report

This breakdown of the analysis results and market performance validates the current implementation against historical data.

Use this command to regenerate the benchmark report after changes to the algorithm or data:
```shell
$ ./benchmark.py > benchmark.md
```

### Events overview

Here's each tweet with the results of its analysis and individual market performance.

##### [2016-12-06 (Tue) 08:52:35](https://twitter.com/realDonaldTrump/status/806134244384899072)

> Boeing is building a brand new 747 Air Force One for future presidents, but costs are out of control, more than $4 billion. Cancel order!

*Strategy*

Company | Root | Sentiment | Strategy | Reason
--------|------|-----------|----------|-------
Boeing | - | -0.1 :thumbsdown: | bear | negative sentiment

*Performance*

Ticker | Exchange | Price @ tweet | Price EOD | Return
-------|----------|---------------|-----------|-------
BA | New York Stock Exchange | $152.16 | $152.30 | -0.092%

##### [2016-12-22 (Thu) 17:26:05](https://twitter.com/realDonaldTrump/status/812061677160202240)

> Based on the tremendous cost and cost overruns of the Lockheed Martin F-35, I have asked Boeing to price-out a comparable F-18 Super Hornet!

*Strategy*

Company | Root | Sentiment | Strategy | Reason
--------|------|-----------|----------|-------
Boeing | - | 0 :neutral_face: | hold | market closed

*Performance*

Ticker | Exchange | Price @ tweet | Price EOD | Return
-------|----------|---------------|-----------|-------
BA | New York Stock Exchange | $158.11 | $157.92 | 0.000%

##### [2017-01-03 (Tue) 07:30:05](https://twitter.com/realDonaldTrump/status/816260343391514624)

> General Motors is sending Mexican made model of Chevy Cruze to U.S. car dealers-tax free across border. Make in U.S.A.or pay big border tax!

*Strategy*

Company | Root | Sentiment | Strategy | Reason
--------|------|-----------|----------|-------
General Motors | - | -0.1 :thumbsdown: | hold | market closed

*Performance*

Ticker | Exchange | Price @ tweet | Price EOD | Return
-------|----------|---------------|-----------|-------
GM | New York Stock Exchange | $34.84 | $35.15 | 0.000%

##### [2017-01-03 (Tue) 11:44:13](https://twitter.com/realDonaldTrump/status/816324295781740544)

> "@DanScavino: Ford to scrap Mexico plant, invest in Michigan due to Trump policies"
https://t.co/137nUo03Gl

*Strategy*

Company | Root | Sentiment | Strategy | Reason
--------|------|-----------|----------|-------
Ford | - | 0.3 :thumbsup: | bull | positive sentiment

*Performance*

Ticker | Exchange | Price @ tweet | Price EOD | Return
-------|----------|---------------|-----------|-------
F | New York Stock Exchange | $12.41 | $12.59 | 1.450%

##### [2017-01-04 (Wed) 08:19:09](https://twitter.com/realDonaldTrump/status/816635078067490816)

> Thank you to Ford for scrapping a new plant in Mexico and creating 700 new jobs in the U.S. This is just the beginning - much more to follow

*Strategy*

Company | Root | Sentiment | Strategy | Reason
--------|------|-----------|----------|-------
Ford | - | 0.3 :thumbsup: | bull | positive sentiment

*Performance*

Ticker | Exchange | Price @ tweet | Price EOD | Return
-------|----------|---------------|-----------|-------
F | New York Stock Exchange | $12.59 | $13.17 | 4.607%

##### [2017-01-05 (Thu) 13:14:30](https://twitter.com/realDonaldTrump/status/817071792711942145)

> Toyota Motor said will build a new plant in Baja, Mexico, to build Corolla cars for U.S. NO WAY! Build plant in U.S. or pay big border tax.

*Strategy*

Company | Root | Sentiment | Strategy | Reason
--------|------|-----------|----------|-------
Toyota | - | -0.2 :thumbsdown: | bear | negative sentiment

*Performance*

Ticker | Exchange | Price @ tweet | Price EOD | Return
-------|----------|---------------|-----------|-------
TM | New York Stock Exchange | $121.12 | $120.44 | 0.565%

##### [2017-01-09 (Mon) 09:14:10](https://twitter.com/realDonaldTrump/status/818460862675558400)

> It's finally happening - Fiat Chrysler just announced plans to invest $1BILLION in Michigan and Ohio plants, adding 2000 jobs. This after...

*Strategy*

Company | Root | Sentiment | Strategy | Reason
--------|------|-----------|----------|-------
Fiat | Fiat Chrysler Automobiles | 0.2 :thumbsup: | bull | positive sentiment

*Performance*

Ticker | Exchange | Price @ tweet | Price EOD | Return
-------|----------|---------------|-----------|-------
FCAU | New York Stock Exchange | $10.55 | $10.57 | 0.190%

##### [2017-01-09 (Mon) 09:16:34](https://twitter.com/realDonaldTrump/status/818461467766824961)

> Ford said last week that it will expand in Michigan and U.S. instead of building a BILLION dollar plant in Mexico. Thank you Ford &amp; Fiat C!

*Strategy*

Company | Root | Sentiment | Strategy | Reason
--------|------|-----------|----------|-------
Ford | - | 0.3 :thumbsup: | bull | positive sentiment
Fiat | Fiat Chrysler Automobiles | 0.3 :thumbsup: | bull | positive sentiment

*Performance*

Ticker | Exchange | Price @ tweet | Price EOD | Return
-------|----------|---------------|-----------|-------
F | New York Stock Exchange | $12.82 | $12.64 | -1.404%
FCAU | New York Stock Exchange | $10.57 | $10.57 | 0.000%

##### [2017-01-17 (Tue) 12:55:38](https://twitter.com/realDonaldTrump/status/821415698278875137)

> Thank you to General Motors and Walmart for starting the big jobs push back into the U.S.!

*Strategy*

Company | Root | Sentiment | Strategy | Reason
--------|------|-----------|----------|-------
General Motors | - | 0.4 :thumbsup: | bull | positive sentiment
Walmart | - | 0.4 :thumbsup: | bull | positive sentiment
Walmart | State Street Corporation | 0.4 :thumbsup: | bull | positive sentiment

*Performance*

Ticker | Exchange | Price @ tweet | Price EOD | Return
-------|----------|---------------|-----------|-------
GM | New York Stock Exchange | $37.54 | $37.31 | -0.613%
WMT | New York Stock Exchange | $68.53 | $68.50 | -0.044%
STT | New York Stock Exchange | $81.19 | $80.20 | -1.219%

##### [2017-01-18 (Wed) 07:34:09](https://twitter.com/realDonaldTrump/status/821697182235496450)

> Totally biased @NBCNews went out of its way to say that the big announcement from Ford, G.M., Lockheed &amp; others that jobs are coming back...

*Strategy*

Company | Root | Sentiment | Strategy | Reason
--------|------|-----------|----------|-------
Ford | - | -0.5 :thumbsdown: | hold | market closed
General Motors | - | -0.5 :thumbsdown: | hold | market closed
Lockheed Martin | - | -0.5 :thumbsdown: | hold | market closed

*Performance*

Ticker | Exchange | Price @ tweet | Price EOD | Return
-------|----------|---------------|-----------|-------
F | New York Stock Exchange | $12.60 | $12.42 | 0.000%
GM | New York Stock Exchange | $37.31 | $37.40 | 0.000%
LMT | New York Stock Exchange | $254.12 | $254.07 | 0.000%

##### [2017-01-18 (Wed) 08:00:51](https://twitter.com/realDonaldTrump/status/821703902940827648)

> "Bayer AG has pledged to add U.S. jobs and investments after meeting with President-elect Donald Trump, the latest in a string..." @WSJ

*Strategy*

Company | Root | Sentiment | Strategy | Reason
--------|------|-----------|----------|-------
Bayer | BlackRock | 0.3 :thumbsup: | bull | positive sentiment

*Performance*

Ticker | Exchange | Price @ tweet | Price EOD | Return
-------|----------|---------------|-----------|-------
BLK | New York Stock Exchange | $374.80 | $378.02 | 0.859%

##### [2017-01-24 (Tue) 12:49:17](https://twitter.com/realDonaldTrump/status/823950814163140609)

> Signing orders to move forward with the construction of the Keystone XL and Dakota Access pipelines in the Oval Off… https://t.co/aOxmfO0vOK

*Strategy*

Company | Root | Sentiment | Strategy | Reason
--------|------|-----------|----------|-------
Keystone Pipeline | TransCanada Corporation | -0.1 :thumbsdown: | bear | negative sentiment

*Performance*

Ticker | Exchange | Price @ tweet | Price EOD | Return
-------|----------|---------------|-----------|-------
TRP | New York Stock Exchange | $48.93 | $48.87 | 0.123%

##### [2017-01-24 (Tue) 19:46:57](https://twitter.com/realDonaldTrump/status/824055927200423936)

> Great meeting with Ford CEO Mark Fields and General Motors CEO Mary Barra at the @WhiteHouse today. https://t.co/T0eIgO6LP8

*Strategy*

Company | Root | Sentiment | Strategy | Reason
--------|------|-----------|----------|-------
Ford | - | 0.5 :thumbsup: | hold | market closed
General Motors | - | 0.5 :thumbsup: | hold | market closed

*Performance*

Ticker | Exchange | Price @ tweet | Price EOD | Return
-------|----------|---------------|-----------|-------
F | New York Stock Exchange | $12.60 | $12.79 | 0.000%
GM | New York Stock Exchange | $37.60 | $38.28 | 0.000%

### Fund simulation

This is how an initial investment of $10,000.00 would have grown, including [TradeKing's fees](https://www.tradeking.com/rates) of $4.95 per trade.

Date | Value | Return | Annualized
-----|-------|--------|-----------
*Initial* | *$10,000.00* | - | -
2016-12-06 | $9,985.86 | -0.141% | -
2016-12-22 | $9,985.86 | -0.141% | -3.176%
2017-01-03 | $9,985.86 | -0.141% | -1.894%
2017-01-03 | $10,125.68 | 1.257% | 17.681%
2017-01-04 | $10,586.97 | 5.870% | 110.339%
2017-01-05 | $10,641.77 | 6.418% | 113.142%
2017-01-09 | $10,656.98 | 6.570% | 97.999%
2017-01-09 | $10,502.47 | 5.025% | 69.267%
2017-01-09 | $10,497.52 | 4.975% | 68.412%
2017-01-17 | $10,428.29 | 4.283% | 43.973%
2017-01-17 | $10,418.78 | 4.188% | 42.835%
2017-01-17 | $10,286.84 | 2.868% | 27.861%
2017-01-18 | $10,286.84 | 2.868% | 27.861%
2017-01-18 | $10,286.84 | 2.868% | 27.861%
2017-01-18 | $10,286.84 | 2.868% | 27.861%
2017-01-18 | $10,370.23 | 3.702% | 37.154%
2017-01-24 | $10,378.00 | 3.780% | 31.835%
2017-01-24 | $10,378.00 | 3.780% | 31.835%
2017-01-24 | $10,378.00 | 3.780% | 31.835%
