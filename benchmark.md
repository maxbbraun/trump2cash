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
BA | New York Stock Exchange | $152.16 | $152.24 | -0.053%

##### [2016-12-22 (Thu) 17:26:05](https://twitter.com/realDonaldTrump/status/812061677160202240)

> Based on the tremendous cost and cost overruns of the Lockheed Martin F-35, I have asked Boeing to price-out a comparable F-18 Super Hornet!

*Strategy*

Company | Root | Sentiment | Strategy | Reason
--------|------|-----------|----------|-------
Boeing | - | 0 :neutral_face: | hold | market closed

*Performance*

Ticker | Exchange | Price @ tweet | Price EOD | Return
-------|----------|---------------|-----------|-------
BA | New York Stock Exchange | $157.46 | $157.81 | 0.000%

##### [2017-01-03 (Tue) 07:30:05](https://twitter.com/realDonaldTrump/status/816260343391514624)

> General Motors is sending Mexican made model of Chevy Cruze to U.S. car dealers-tax free across border. Make in U.S.A.or pay big border tax!

*Strategy*

Company | Root | Sentiment | Strategy | Reason
--------|------|-----------|----------|-------
General Motors | - | -0.1 :thumbsdown: | hold | market closed

*Performance*

Ticker | Exchange | Price @ tweet | Price EOD | Return
-------|----------|---------------|-----------|-------
GM | New York Stock Exchange | - | - | 0.000%

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
F | New York Stock Exchange | $12.41 | $12.59 | 1.410%

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
TM | New York Stock Exchange | $120.37 | $120.44 | -0.058%

##### [2017-01-09 (Mon) 09:14:10](https://twitter.com/realDonaldTrump/status/818460862675558400)

> It's finally happening - Fiat Chrysler just announced plans to invest $1BILLION in Michigan and Ohio plants, adding 2000 jobs. This after...

*Strategy*

Company | Root | Sentiment | Strategy | Reason
--------|------|-----------|----------|-------
Fiat | Fiat Chrysler Automobiles | 0.2 :thumbsup: | bull | positive sentiment

*Performance*

Ticker | Exchange | Price @ tweet | Price EOD | Return
-------|----------|---------------|-----------|-------
FCAU | New York Stock Exchange | $10.42 | $10.57 | 1.440%

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
F | New York Stock Exchange | $12.76 | $12.63 | -1.019%
FCAU | New York Stock Exchange | $10.42 | $10.57 | 1.440%

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
GM | New York Stock Exchange | $37.57 | $37.31 | -0.692%
WMT | New York Stock Exchange | $68.57 | $68.42 | -0.219%
STT | New York Stock Exchange | $81.16 | $80.20 | -1.183%

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
F | New York Stock Exchange | $12.61 | $12.41 | 0.000%
GM | New York Stock Exchange | $37.31 | $37.47 | 0.000%
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
BLK | New York Stock Exchange | $374.80 | $378.00 | 0.854%

##### [2017-01-24 (Tue) 12:49:17](https://twitter.com/realDonaldTrump/status/823950814163140609)

> Signing orders to move forward with the construction of the Keystone XL and Dakota Access pipelines in the Oval Off… https://t.co/aOxmfO0vOK

*Strategy*

Company | Root | Sentiment | Strategy | Reason
--------|------|-----------|----------|-------
Keystone Pipeline | TransCanada Corporation | -0.1 :thumbsdown: | bear | negative sentiment

*Performance*

Ticker | Exchange | Price @ tweet | Price EOD | Return
-------|----------|---------------|-----------|-------
TRP | New York Stock Exchange | $48.93 | $48.84 | 0.176%

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
F | New York Stock Exchange | $12.61 | $12.79 | 0.000%
GM | New York Stock Exchange | $37.00 | $38.28 | 0.000%

### Fund simulation

This is how an initial investment of $10,000.00 would have grown, including [TradeKing's fees](https://www.tradeking.com/rates) of $4.95 per trade.

Date | Value | Return | Annualized
-----|-------|--------|-----------
*Initial* | *$10,000.00* | - | -
2016-12-06 | $9,989.80 | -0.102% | -
2016-12-22 | $9,989.80 | -0.102% | -2.302%
2017-01-03 | $9,989.80 | -0.102% | -1.370%
2017-01-03 | $10,125.59 | 1.256% | 17.668%
2017-01-04 | $10,586.88 | 5.869% | 110.315%
2017-01-05 | $10,575.78 | 5.758% | 97.607%
2017-01-09 | $10,723.00 | 7.230% | 111.571%
2017-01-09 | $10,608.86 | 6.089% | 88.608%
2017-01-09 | $10,756.56 | 7.566% | 118.787%
2017-01-17 | $10,677.20 | 6.772% | 76.729%
2017-01-17 | $10,648.90 | 6.489% | 72.700%
2017-01-17 | $10,518.05 | 5.181% | 55.106%
2017-01-18 | $10,518.05 | 5.181% | 55.106%
2017-01-18 | $10,518.05 | 5.181% | 55.106%
2017-01-18 | $10,518.05 | 5.181% | 55.106%
2017-01-18 | $10,602.86 | 6.029% | 66.318%
2017-01-24 | $10,616.59 | 6.166% | 56.158%
2017-01-24 | $10,616.59 | 6.166% | 56.158%
2017-01-24 | $10,616.59 | 6.166% | 56.158%
