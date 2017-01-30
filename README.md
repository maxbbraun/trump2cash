# Trump2Cash

This bot watches [Donald Trump's tweets](https://twitter.com/realDonaldTrump)
and waits for him to mention any publicly traded companies. When he does, it
uses sentiment analysis to determine whether his opinions are positive or
negative toward those companies. The bot then automatically executes trades on
the relevant stocks according to the expected market reaction. It also tweets
out a summary of its findings in real time at
[@Trump2Cash](https://twitter.com/Trump2Cash).

You can read more about the background story [here](https://medium.com/@maxbraun/this-machine-turns-trump-tweets-into-planned-parenthood-donations-928da9e433d2).

[![Sample tweet from @Trump2Cash](https://lh3.googleusercontent.com/QA1tS_Ia20VlImo4wB3sFIiZj2FH5JXEedlsVj6NEc3nBjn5VBjmkP0P7LgeK1IhmLZvfXQr59xxjjpHe_e8g0jCbyW65bvICf5iII7RrjXnW62uob9XuC-p0WZygmq_ZncJRF48GL4mKK8HEwRqz-IoQ8OQz4vM1Tl-eqx_1HLFjo1AzwpCgtNSBGPv7weSdP5DzKKCbEvnFIU15lq1a-5MmRv0cj1KhiCR3Vx28oa5BRUNgNumo6Y5MHtdgHHW6UGRlBY3UeyXH2ndoJZZPOpWw2cBNUYmRw4RBKnwUcnpk7ALhRydIX6rXWl6E9xmhAUkGxgUAdXm0xpDzZLctTOntKVef34uaPpNI4zq7fA44lqP-lj5VjcwivGhZWQRPYK0UAKU6OgOCf7tCxXjn0BRyAHvhXn94to_gQZeaEb71MOg2ml-_orUgXaSY1Z7gJZHGrC_gdQQu6kqvaZO-QKsT2r12F2OgI1JUXFt1NlEOxP3rGgRVbxED5de2cAWO8cO6H6stluv8WkjuM_13L_zPIKt_n7cdvvPveevpFkDDQ5ZvZ2dSFJd_GKhOCemR3-3KabhQhjkyh1Z5n-kzbLef2N32fI6UUeKTCXtgTeXjz53Wxm-R0BUKcbfFWcDl8kUZsFXFTLf6rfqwbeKJnnnhqC2Lzkhc83eQrmuVyg=w662-h451-no)](https://twitter.com/Trump2Cash/status/821415729329147904)

The code is written in Python and uses APIs from
[Twitter](https://dev.twitter.com/docs),
[Google](https://cloud.google.com/natural-language/), and
[TradeKing](https://developers.tradeking.com/) to do it's thing. It is built to
run in a [Compute Engine](https://cloud.google.com/compute/) instance. Follow
these steps to run the code yourself:

### 1. Create VM instance

Follow [these steps](https://cloud.google.com/compute/docs/quickstart-linux) to
create a Linux VM instance in Google Compute Engine and SSH into it for the
steps below.

### 2. Set up auth

The authentication keys for the different APIs are read from shell environment
variables. Each service has different steps to obtain them.

#### Twitter

Log in to your [Twitter](https://twitter.com/) account and
[create a new application](https://apps.twitter.com/app/new). Under the *Keys
and Access Tokens* tab for [your app](https://apps.twitter.com/) you'll find
the *Consumer Key* and *Consumer Secret*. Export both to environment variables:

```shell
export TWITTER_CONSUMER_KEY="<YOUR_CONSUMER_KEY>"
export TWITTER_CONSUMER_SECRET="<YOUR_CONSUMER_SECRET>"
```

If you want the tweets to come from the same account that owns the application,
simply use the *Access Token* and *Access Token Secret* on the same page. If
you want to tweet from a different account, follow the
[steps to obtain an access token](https://dev.twitter.com/oauth/overview). Then
export both to environment variables:

```shell
export TWITTER_ACCESS_TOKEN="<YOUR_ACCESS_TOKEN>"
export TWITTER_ACCESS_TOKEN_SECRET="<YOUR_ACCESS_TOKEN_SECRET>"
```

#### Google

Follow the [Google Application Default Credentials instructions](https://developers.google.com/identity/protocols/application-default-credentials#howtheywork)
to create, download, and export a service account key.

```shell
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials-file.json"
```

You also need to [enable the Cloud Natural Language API](https://cloud.google.com/natural-language/docs/getting-started#set_up_your_project)
for your Google Cloud Platform project.

#### TradeKing

Log in to your [TradeKing](https://www.tradeking.com/) account and
[create a new application](https://developers.tradeking.com/applications/CreateApplication).
Behind the *Details* button for
[your application](https://developers.tradeking.com/Applications) you'll find
the *Consumer Key*, *Consumer Secret*, *OAuth (Access) Token*, and *Oauth (Access)
Token Secret*. Export them all to environment variables:

```shell
export TRADEKING_CONSUMER_KEY="<YOUR_CONSUMER_KEY>"
export TRADEKING_CONSUMER_SECRET="<YOUR_CONSUMER_SECRET>"
export TRADEKING_ACCESS_TOKEN="<YOUR_ACCESS_TOKEN>"
export TRADEKING_ACCESS_TOKEN_SECRET="<YOUR_ACCESS_TOKEN_SECRET>"
```

Also export your TradeKing account number, which you'll find under
*[My Accounts](https://investor.tradeking.com/Modules/Dashboard/dashboard.php)*:

```shell
export TRADEKING_ACCOUNT_NUMBER="<YOUR_ACCOUNT_NUMBER>"
```

### 3. Install dependencies

There are a few library dependencies, which you can install using
[pip](https://pip.pypa.io/en/stable/quickstart/):

```shell
$ pip install -r requirements.txt
```

### 4. Run the tests

Verify that everything is working as intended by running the tests with
[pytest](http://doc.pytest.org/en/latest/getting-started.html) using this
command:

```shell
$ export USE_REAL_MONEY=NO && pytest *.py --verbose
```

### 5. Run the benchmark

The [benchmark report](benchmark.md) shows how the current implementation of the
analysis and trading algorithms would have performed against historical data.
You can run it again to benchmark any changes you may have made:

```shell
$ ./benchmark.py > benchmark.md
```

### 6. Start the bot

Enable real orders that use your money:

```shell
$ export USE_REAL_MONEY=YES
```

Have the code start running in the background with this command:

```shell
$ nohup ./main.py &
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
