# Trump2Cash

This bot watches [Donald Trump's tweets](https://twitter.com/realDonaldTrump)
and waits for him to mention any publicly traded companies. When he does, it
uses sentiment analysis to determine whether his opinions are positive or
negative toward those companies. The bot then automatically executes trades on
the relevant stocks according to the expected market reaction. It also tweets
out a summary of its findings in real time at
[@Trump2Cash](https://twitter.com/Trump2Cash).

You can read more about the background story [here](https://medium.com/@maxbraun/this-machine-turns-trump-tweets-into-planned-parenthood-donations-928da9e433d2).

[![Sample tweet from @Trump2Cash](https://lh3.googleusercontent.com/2y495BxzL8X61_mCJTrqH6SGZeP0PQjLWiL0DXRvehQMykGR-iqwxTHI5vbK0JlW1fEKOB4pZ7R96DYWM2AqmKZzEdTA5D-JyIR-c5LT1q0F8wf6fOeyQgOiNw_2SYOR0plRR9XAjdlVKLrUQZ4kD3N7qlfTw-cWCzMB2rHocU4xqPlODrjjCtItWHnJ7s6Vvo1QDA6GiS-tULwrOBnqunqdvspyVGBGDKuqQDMA27V5--cYnAgz4791osHzmhr0cWO2xaNiqYGEy9aczjgfMLT4XHaawZVk7Fxm2kzHgg9fFb2WAanYS8hRXOglpqm_XfRH4NGarTbYO0-Lk4AOKrhzLsOpXNBEDsHMV6uQam6N8Y9u6hlgEVBXCKgtZaCdE3jV-cg_8Fe0m_HIQ1u76pQKFbDJ69rdW3Ejj6_Rkj7xr6WcbFwqkxUuEDeMlmT4NIUsYtCqctD_15XcOgU6uNn-1XC7jlmcaQCo6THJ2Le5H5s-vj60_P_RqGE1jg-Gm3A_YkTnDtXIIHmpnoRigEP0iHt5QrNeErNTmvl9Tjugp3AP5AZdw8aZ5a9ilAsubpdRraG4FudyFJnGPe14WqgNL36SiRHS5YbcKuXsf-cDqiq8m5KF4M9k9KDTs1AB4EHnYD9hqc8hQkk_tId9qRO0f24-Jx1GSfqF3ILmlhc=w662-h382-no)](https://twitter.com/Trump2Cash/status/821415729329147904)

The code is written in Python and uses APIs from
[Twitter](https://dev.twitter.com/docs),
[Google](https://cloud.google.com/natural-language/), and
[TradeKing](https://developers.tradeking.com/) to do it's thing. It is built to
run in a [Compute Engine](https://cloud.google.com/compute/) instance. Follow
these steps to run the code yourself:

### 1. Create VM instance

Check out the [quickstart](https://cloud.google.com/compute/docs/quickstart-linux)
to create a Cloud Platform project and a Linux VM instance with Compute Engine.
Then SSH into it for the steps below.

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
