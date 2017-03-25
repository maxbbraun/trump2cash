# -*- coding: utf-8 -*-

from ast import literal_eval
from google.cloud.language.entity import Entity
from os import getenv
from pytest import fixture

from analysis import Analysis
from analysis import MID_TO_TICKER_QUERY
from twitter import Twitter


@fixture
def analysis():
    return Analysis(logs_to_cloud=False)


def get_tweet(tweet_id):
    """Looks up data for a single tweet."""

    twitter = Twitter(logs_to_cloud=False)
    return twitter.get_tweet(tweet_id)


def get_tweet_text(tweet_id):
    """Looks up the text for a single tweet."""

    tweet = get_tweet(tweet_id)
    analysis = Analysis(logs_to_cloud=False)
    return analysis.get_expanded_text(tweet)


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
        "root": "Alphabet Inc.",
        "ticker": "GOOG"}, {
        "exchange": "NASDAQ",
        "name": "YouTube",
        "root": "Alphabet Inc.",
        "ticker": "GOOGL"}, {
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
        "ticker": "BLK"}, {
        "exchange": "New York Stock Exchange",
        "name": "Bayer",
        "root": "PNC Financial Services",
        "ticker": "PNC"}]
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
    assert analysis.get_company_data("/m/0k9ts") == [{
        "exchange": "New York Stock Exchange",
        "name": "Delta Air Lines",
        "ticker": "DAL"}]
    assert analysis.get_company_data("/m/033yz") == [{
        "exchange": "New York Stock Exchange",
        "name": "Lockheed Martin Aeronautics",
        "root": "Lockheed Martin",
        "ticker": "LMT"}]
    assert analysis.get_company_data("/m/017b3j") is None
    assert analysis.get_company_data("/m/07k2d") is None
    assert analysis.get_company_data("/m/02z_b") is None
    assert analysis.get_company_data("/m/0d6lp") is None
    assert analysis.get_company_data("xyz") is None
    assert analysis.get_company_data("") is None


def test_entity_tostring(analysis):
    assert analysis.entity_tostring(Entity(
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
    assert analysis.entity_tostring(Entity(
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
    assert analysis.entities_tostring([Entity(
        name="General Motors",
        entity_type="ORGANIZATION",
        metadata={
            "mid": "/m/035nm",
            "wikipedia_url": "http://en.wikipedia.org/wiki/General_Motors"},
        salience=0.33838183,
        mentions=["General Motors"]), Entity(
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


def test_get_sentiment(analysis):
    assert analysis.get_sentiment(get_tweet_text("806134244384899072")) < 0
    # assert analysis.get_sentiment(get_tweet_text("812061677160202240")) > 0
    assert analysis.get_sentiment(get_tweet_text("816260343391514624")) < 0
    assert analysis.get_sentiment(get_tweet_text("816324295781740544")) > 0
    assert analysis.get_sentiment(get_tweet_text("816635078067490816")) > 0
    assert analysis.get_sentiment(get_tweet_text("817071792711942145")) < 0
    assert analysis.get_sentiment(get_tweet_text("818460862675558400")) > 0
    assert analysis.get_sentiment(get_tweet_text("818461467766824961")) > 0
    assert analysis.get_sentiment(get_tweet_text("821415698278875137")) > 0
    # assert analysis.get_sentiment(get_tweet_text("821697182235496450")) > 0
    assert analysis.get_sentiment(get_tweet_text("821703902940827648")) > 0
    assert analysis.get_sentiment(get_tweet_text("803808454620094465")) > 0
    assert analysis.get_sentiment(get_tweet_text("621669173534584833")) < 0
    assert analysis.get_sentiment(get_tweet_text("664911913831301123")) < 0
    # assert analysis.get_sentiment(get_tweet_text("823950814163140609")) > 0
    assert analysis.get_sentiment(get_tweet_text("824055927200423936")) > 0
    assert analysis.get_sentiment(get_tweet_text("826041397232943104")) < 0
    assert analysis.get_sentiment(get_tweet_text("824765229527605248")) > 0
    assert analysis.get_sentiment(get_tweet_text("827874208021639168")) < 0
    assert analysis.get_sentiment(get_tweet_text("828642511698669569")) < 0
    assert analysis.get_sentiment(get_tweet_text("828793887275761665")) < 0
    assert analysis.get_sentiment(get_tweet_text("829410107406614534")) > 0
    assert analysis.get_sentiment(get_tweet_text("829356871848951809")) < 0
    # assert analysis.get_sentiment(get_tweet_text("808301935728230404")) < 0
    assert analysis.get_sentiment(get_tweet_text("845334323045765121")) > 0
    assert analysis.get_sentiment(None) == 0


def test_find_companies(analysis):
    assert analysis.find_companies(get_tweet("806134244384899072")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Boeing",
        "sentiment": -0.1,
        "ticker": "BA"}]
    assert analysis.find_companies(get_tweet("812061677160202240")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Lockheed Martin Aeronautics",
        "root": "Lockheed Martin",
        "sentiment": 0,  # -0.1,
        "ticker": "LMT"}, {
        "exchange": "New York Stock Exchange",
        "name": "Boeing",
        "sentiment": 0,  # 0.1,
        "ticker": "BA"}]
    assert analysis.find_companies(get_tweet("816260343391514624")) == [{
        "exchange": "New York Stock Exchange",
        "name": "General Motors",
        "sentiment": -0.1,
        "ticker": "GM"}]
    assert analysis.find_companies(get_tweet("816324295781740544")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Ford",
        "sentiment": 0.5,
        "ticker": "F"}]
    assert analysis.find_companies(get_tweet("816635078067490816")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Ford",
        "sentiment": 0.3,
        "ticker": "F"}]
    assert analysis.find_companies(get_tweet("817071792711942145")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Toyota",
        "sentiment": -0.2,
        "ticker": "TM"}]
    assert analysis.find_companies(get_tweet("818460862675558400")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Fiat",
        "root": "Fiat Chrysler Automobiles",
        "sentiment": 0.2,
        "ticker": "FCAU"}]
    assert analysis.find_companies(get_tweet("818461467766824961")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Ford",
        "sentiment": 0.3,
        "ticker": "F"}, {
        "exchange": "New York Stock Exchange",
        "name": "Fiat",
        "root": "Fiat Chrysler Automobiles",
        "sentiment": 0.3,
        "ticker": "FCAU"}]
    assert analysis.find_companies(get_tweet("821415698278875137")) == [{
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
    assert analysis.find_companies(get_tweet("821697182235496450")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Ford",
        "sentiment": -0.6,  # 0,
        "ticker": "F"}, {
        "exchange": "New York Stock Exchange",
        "name": "General Motors",
        "sentiment": -0.6,  # 0,
        "ticker": "GM"}, {
        "exchange": "New York Stock Exchange",
        "name": "Lockheed Martin",
        "sentiment": -0.6,  # 0,
        "ticker": "LMT"}]
    assert analysis.find_companies(get_tweet("821703902940827648")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Bayer",
        "sentiment": 0.4,
        "root": "BlackRock",
        "ticker": "BLK"}, {
        "exchange": "New York Stock Exchange",
        "name": "Bayer",
        "sentiment": 0.4,
        "root": "PNC Financial Services",
        "exchange": "New York Stock Exchange",
        "ticker": "PNC"}]
    # assert analysis.find_companies(get_tweet("803808454620094465")) == [{
    #     "exchange": "New York Stock Exchange",
    #     "name": "Carrier Corporation",
    #     "sentiment": 0.5,
    #     "root": "United Technologies Corporation",
    #     "ticker": "UTX"}]
    assert analysis.find_companies(get_tweet("621669173534584833")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Macy's",
        "root": "Macy's, Inc.",
        "sentiment": -0.5,
        "ticker": "M"}]
    assert analysis.find_companies(get_tweet("664911913831301123")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Macy's",
        "root": "Macy's, Inc.",
        "sentiment": -0.3,
        "ticker": "M"}]
    assert analysis.find_companies(get_tweet("823950814163140609")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Keystone Pipeline",
        "root": "TransCanada Corporation",
        "sentiment": 0,  # 0.1,
        "ticker": "TRP"}]
    assert analysis.find_companies(get_tweet("824055927200423936")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Ford",
        "sentiment": 0.5,
        "ticker": "F"}, {
        "exchange": "New York Stock Exchange",
        "name": "General Motors",
        "sentiment": 0.5,
        "ticker": "GM"}]
    assert analysis.find_companies(get_tweet("826041397232943104")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Delta Air Lines",
        "sentiment": -0.4,
        "ticker": "DAL"}]
    assert analysis.find_companies(get_tweet("824765229527605248")) == []
    assert analysis.find_companies(get_tweet("827874208021639168")) == []
    assert analysis.find_companies(get_tweet("828642511698669569")) == []
    assert analysis.find_companies(get_tweet("828793887275761665")) == []
    assert analysis.find_companies(get_tweet("829410107406614534")) == [{
        "exchange": "NASDAQ",
        "name": "Intel",
        "sentiment": 0.6,
        "ticker": "INTC"}]
    assert analysis.find_companies(get_tweet("829356871848951809")) == [{
        "exchange": "New York Stock Exchange",
        "name": "Nordstrom",
        "sentiment": -0.2,
        "ticker": "JWN"}]
    assert analysis.find_companies(get_tweet("845334323045765121")) == [{
        "exchange": "NASDAQ",
        "name": "Charter Communications",
        "sentiment": 0.6,
        "ticker": "CHTR"}, {
        "exchange": "New York Stock Exchange",
        "name": "Charter Communications",
        "root": "Berkshire Hathaway",
        "sentiment": 0.6,
        "ticker": "BRK.A"}, {
        "exchange": "New York Stock Exchange",
        "name": "Charter Communications",
        "root": "Berkshire Hathaway",
        "sentiment": 0.6,
        "ticker": "BRK.B"}]
    assert analysis.find_companies(None) is None


STREAMING_TWEET_LONG = literal_eval(
    u'{"contributors": None, "truncated": True, "text": "Today, I was thrilled'
    ' to announce a commitment of $25 BILLION &amp; 20K AMERICAN JOBS over the'
    ' next 4 years. THANK YOU\u2026 https://t.co/nWJ1hNmzoR", "is_quote_status'
    '": False, "in_reply_to_status_id": None, "id": 845334323045765121, "favor'
    'ite_count": 0, "source": "<a href=\\"http://twitter.com/download/iphone\\'
    '" rel=\\"nofollow\\">Twitter for iPhone</a>", "retweeted": False, "coordi'
    'nates": None, "timestamp_ms": "1490378382823", "entities": {"user_mention'
    's": [], "symbols": [], "hashtags": [], "urls": [{"url": "https://t.co/nWJ'
    '1hNmzoR", "indices": [120, 143], "expanded_url": "https://twitter.com/i/w'
    'eb/status/845334323045765121", "display_url": "twitter.com/i/web/status/8'
    '\u2026"}]}, "in_reply_to_screen_name": None, "id_str": "84533432304576512'
    '1", "display_text_range": [0, 140], "retweet_count": 0, "in_reply_to_user'
    '_id": None, "favorited": False, "user": {"follow_request_sent": None, "pr'
    'ofile_use_background_image": True, "default_profile_image": False, "id": '
    '25073877, "verified": True, "profile_image_url_https": "https://pbs.twimg'
    '.com/profile_images/1980294624/DJT_Headshot_V2_normal.jpg", "profile_side'
    'bar_fill_color": "C5CEC0", "profile_text_color": "333333", "followers_cou'
    'nt": 26964041, "profile_sidebar_border_color": "BDDCAD", "id_str": "25073'
    '877", "profile_background_color": "6D5C18", "listed_count": 67185, "profi'
    'le_background_image_url_https": "https://pbs.twimg.com/profile_background'
    '_images/530021613/trump_scotland__43_of_70_cc.jpg", "utc_offset": -14400,'
    ' "statuses_count": 34648, "description": "45th President of the United St'
    'ates of America", "friends_count": 43, "location": "Washington, DC", "pro'
    'file_link_color": "0D5B73", "profile_image_url": "http://pbs.twimg.com/pr'
    'ofile_images/1980294624/DJT_Headshot_V2_normal.jpg", "following": None, "'
    'geo_enabled": True, "profile_banner_url": "https://pbs.twimg.com/profile_'
    'banners/25073877/1489657715", "profile_background_image_url": "http://pbs'
    '.twimg.com/profile_background_images/530021613/trump_scotland__43_of_70_c'
    'c.jpg", "name": "Donald J. Trump", "lang": "en", "profile_background_tile'
    '": True, "favourites_count": 46, "screen_name": "realDonaldTrump", "notif'
    'ications": None, "url": None, "created_at": "Wed Mar 18 13:46:38 +0000 20'
    '09", "contributors_enabled": False, "time_zone": "Eastern Time (US & Cana'
    'da)", "protected": False, "default_profile": False, "is_translator": Fals'
    'e}, "geo": None, "in_reply_to_user_id_str": None, "possibly_sensitive": F'
    'alse, "lang": "en", "extended_tweet": {"display_text_range": [0, 142], "e'
    'ntities": {"user_mentions": [], "symbols": [], "hashtags": [], "urls": []'
    ', "media": [{"expanded_url": "https://twitter.com/realDonaldTrump/status/'
    '845334323045765121/video/1", "display_url": "pic.twitter.com/PLxUmXVl0h",'
    ' "url": "https://t.co/PLxUmXVl0h", "media_url_https": "https://pbs.twimg.'
    'com/ext_tw_video_thumb/845330366156210176/pu/img/NdRWqCDX-r734Vpd.jpg", "'
    'video_info": {"aspect_ratio": [16, 9], "duration_millis": 121367, "varian'
    'ts": [{"url": "https://video.twimg.com/ext_tw_video/845330366156210176/pu'
    '/vid/640x360/eu6vsoGqW43Cc64C.mp4", "bitrate": 832000, "content_type": "v'
    'ideo/mp4"}, {"url": "https://video.twimg.com/ext_tw_video/845330366156210'
    '176/pu/vid/320x180/QPwu682wzK5C4e0V.mp4", "bitrate": 320000, "content_typ'
    'e": "video/mp4"}, {"url": "https://video.twimg.com/ext_tw_video/845330366'
    '156210176/pu/pl/flkqzlPIkchbfIGZ.m3u8", "content_type": "application/x-mp'
    'egURL"}, {"url": "https://video.twimg.com/ext_tw_video/845330366156210176'
    '/pu/vid/1280x720/6l5bIhFXEih9is4L.mp4", "bitrate": 2176000, "content_type'
    '": "video/mp4"}]}, "id_str": "845330366156210176", "sizes": {"small": {"h'
    '": 191, "resize": "fit", "w": 340}, "large": {"h": 576, "resize": "fit", '
    '"w": 1024}, "medium": {"h": 338, "resize": "fit", "w": 600}, "thumb": {"h'
    '": 150, "resize": "crop", "w": 150}}, "indices": [143, 166], "type": "vid'
    'eo", "id": 845330366156210176, "media_url": "http://pbs.twimg.com/ext_tw_'
    'video_thumb/845330366156210176/pu/img/NdRWqCDX-r734Vpd.jpg"}]}, "extended'
    '_entities": {"media": [{"expanded_url": "https://twitter.com/realDonaldTr'
    'ump/status/845334323045765121/video/1", "display_url": "pic.twitter.com/P'
    'LxUmXVl0h", "url": "https://t.co/PLxUmXVl0h", "media_url_https": "https:/'
    '/pbs.twimg.com/ext_tw_video_thumb/845330366156210176/pu/img/NdRWqCDX-r734'
    'Vpd.jpg", "video_info": {"aspect_ratio": [16, 9], "duration_millis": 1213'
    '67, "variants": [{"url": "https://video.twimg.com/ext_tw_video/8453303661'
    '56210176/pu/vid/640x360/eu6vsoGqW43Cc64C.mp4", "bitrate": 832000, "conten'
    't_type": "video/mp4"}, {"url": "https://video.twimg.com/ext_tw_video/8453'
    '30366156210176/pu/vid/320x180/QPwu682wzK5C4e0V.mp4", "bitrate": 320000, "'
    'content_type": "video/mp4"}, {"url": "https://video.twimg.com/ext_tw_vide'
    'o/845330366156210176/pu/pl/flkqzlPIkchbfIGZ.m3u8", "content_type": "appli'
    'cation/x-mpegURL"}, {"url": "https://video.twimg.com/ext_tw_video/8453303'
    '66156210176/pu/vid/1280x720/6l5bIhFXEih9is4L.mp4", "bitrate": 2176000, "c'
    'ontent_type": "video/mp4"}]}, "id_str": "845330366156210176", "sizes": {"'
    'small": {"h": 191, "resize": "fit", "w": 340}, "large": {"h": 576, "resiz'
    'e": "fit", "w": 1024}, "medium": {"h": 338, "resize": "fit", "w": 600}, "'
    'thumb": {"h": 150, "resize": "crop", "w": 150}}, "indices": [143, 166], "'
    'type": "video", "id": 845330366156210176, "media_url": "http://pbs.twimg.'
    'com/ext_tw_video_thumb/845330366156210176/pu/img/NdRWqCDX-r734Vpd.jpg"}]}'
    ', "full_text": "Today, I was thrilled to announce a commitment of $25 BIL'
    'LION &amp; 20K AMERICAN JOBS over the next 4 years. THANK YOU Charter Com'
    'munications! https://t.co/PLxUmXVl0h"}, "created_at": "Fri Mar 24 17:59:4'
    '2 +0000 2017", "filter_level": "low", "in_reply_to_status_id_str": None, '
    '"place": None}')
STREAMING_TWEET_SHORT = literal_eval(
    u'{"contributors": None, "truncated": False, "text": "ObamaCare will explo'
    'de and we will all get together and piece together a great healthcare pla'
    'n for THE PEOPLE. Do not worry!", "is_quote_status": False, "in_reply_to_'
    'status_id": None, "id": 845645916732358656, "favorite_count": 0, "source"'
    ': "<a href=\\"http://twitter.com/download/android\\" rel=\\"nofollow\\">T'
    'witter for Android</a>", "retweeted": False, "coordinates": None, "timest'
    'amp_ms": "1490452672547", "entities": {"user_mentions": [], "symbols": []'
    ', "hashtags": [], "urls": []}, "in_reply_to_screen_name": None, "id_str":'
    ' "845645916732358656", "retweet_count": 0, "in_reply_to_user_id": None, "'
    'favorited": False, "user": {"follow_request_sent": None, "profile_use_bac'
    'kground_image": True, "default_profile_image": False, "id": 25073877, "ve'
    'rified": True, "profile_image_url_https": "https://pbs.twimg.com/profile_'
    'images/1980294624/DJT_Headshot_V2_normal.jpg", "profile_sidebar_fill_colo'
    'r": "C5CEC0", "profile_text_color": "333333", "followers_count": 27003111'
    ', "profile_sidebar_border_color": "BDDCAD", "id_str": "25073877", "profil'
    'e_background_color": "6D5C18", "listed_count": 67477, "profile_background'
    '_image_url_https": "https://pbs.twimg.com/profile_background_images/53002'
    '1613/trump_scotland__43_of_70_cc.jpg", "utc_offset": -14400, "statuses_co'
    'unt": 34649, "description": "45th President of the United States of Ameri'
    'ca", "friends_count": 43, "location": "Washington, DC", "profile_link_col'
    'or": "0D5B73", "profile_image_url": "http://pbs.twimg.com/profile_images/'
    '1980294624/DJT_Headshot_V2_normal.jpg", "following": None, "geo_enabled":'
    ' True, "profile_banner_url": "https://pbs.twimg.com/profile_banners/25073'
    '877/1489657715", "profile_background_image_url": "http://pbs.twimg.com/pr'
    'ofile_background_images/530021613/trump_scotland__43_of_70_cc.jpg", "name'
    '": "Donald J. Trump", "lang": "en", "profile_background_tile": True, "fav'
    'ourites_count": 46, "screen_name": "realDonaldTrump", "notifications": No'
    'ne, "url": None, "created_at": "Wed Mar 18 13:46:38 +0000 2009", "contrib'
    'utors_enabled": False, "time_zone": "Eastern Time (US & Canada)", "protec'
    'ted": False, "default_profile": False, "is_translator": False}, "geo": No'
    'ne, "in_reply_to_user_id_str": None, "lang": "en", "created_at": "Sat Mar'
    ' 25 14:37:52 +0000 2017", "filter_level": "low", "in_reply_to_status_id_s'
    'tr": None, "place": None}')


def test_get_expanded_text(analysis):
    assert analysis.get_expanded_text(get_tweet("829410107406614534")) == (
        u"Thank you Brian Krzanich, CEO of Intel. A great investment ($7 BILLI"
        u"ON) in American INNOVATION and JOBS! #AmericaFirst\U0001f1fa"
        u"\U0001f1f8 https://t.co/76lAiSSQ1l")
    assert analysis.get_expanded_text(get_tweet("828574430800539648")) == (
        "Any negative polls are fake news, just like the CNN, ABC, NBC polls i"
        "n the election. Sorry, people want border security and extreme vettin"
        "g.")
    assert analysis.get_expanded_text(get_tweet("828642511698669569")) == (
        "The failing The New York Times writes total fiction concerning me. Th"
        "ey have gotten it wrong for two years, and now are making up stories "
        "&amp; sources!")
    assert analysis.get_expanded_text(get_tweet("845334323045765121")) == (
        "Today, I was thrilled to announce a commitment of $25 BILLION &amp; 2"
        "0K AMERICAN JOBS over the next 4 years. THANK YOU Charter Communicati"
        "ons! https://t.co/PLxUmXVl0h")
    assert analysis.get_expanded_text(STREAMING_TWEET_LONG) == (
        "Today, I was thrilled to announce a commitment of $25 BILLION &amp; 2"
        "0K AMERICAN JOBS over the next 4 years. THANK YOU Charter Communicati"
        "ons! https://t.co/PLxUmXVl0h")
    assert analysis.get_expanded_text(get_tweet("845645916732358656")) == (
        "ObamaCare will explode and we will all get together and piece togethe"
        "r a great healthcare plan for THE PEOPLE. Do not worry!")
    assert analysis.get_expanded_text(STREAMING_TWEET_SHORT) == (
        "ObamaCare will explode and we will all get together and piece togethe"
        "r a great healthcare plan for THE PEOPLE. Do not worry!")
    assert analysis.get_expanded_text(None) is None


def test_make_wikidata_request(analysis):
    assert analysis.make_wikidata_request(
        MID_TO_TICKER_QUERY % "/m/02y1vz") == [{
            "companyLabel": {
                "type": "literal",
                "value": "Facebook",
                "xml:lang": "en"},
            "rootLabel": {
                "type": "literal",
                "value": "Facebook Inc.",
                "xml:lang": "en"},
            "exchangeNameLabel": {
                "type": "literal",
                "value": "NASDAQ",
                "xml:lang": "en"},
            "tickerLabel": {
                "type": "literal",
                "value": "FB"}}]
    assert analysis.make_wikidata_request("") is None
