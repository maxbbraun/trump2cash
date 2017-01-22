# Trump Correction

TODO

(1) Trump (2) ??? (3) Profit

Google Cloud Platform
Compute Engine

analysis
trading
twitter

### Setting up auth

Authentication keys are read from shell environment variables. TODO

#### Twitter

TODO

``` shell
export TWITTER_CONSUMER_KEY="..."
export TWITTER_CONSUMER_SECRET="..."
```

 TODO

``` shell
export TWITTER_ACCESS_TOKEN="..."
export TWITTER_ACCESS_TOKEN_SECRET="..."
```

#### Google

TODO

``` shell
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials-file.json"
```

#### TradeKing

TODO

``` shell
export TRADEKING_CONSUMER_KEY="..."
export TRADEKING_CONSUMER_SECRET="..."
export TRADEKING_ACCESS_TOKEN="..."
export TRADEKING_ACCESS_TOKEN_SECRET="..."
```

``` shell
export TRADEKING_ACCOUNT_NUMBER="..."
```

### Running tests

The tests are written for [pytest](http://doc.pytest.org/en/latest/getting-started.html). Run them all using this command:

``` shell
$ pytest *.py --verbose
```

##License

Copyright 2017 Max Braun

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
