import requests
import sys
import os
import json
import re

API_KEY=os.environ.get("TWITTER_API_KEY")

SEARCH_URL="https://api.twitterapi.io/twitter/tweet/advanced_search"

def _get_tweets(query,cursor=""):
    headers={
        'X-API-Key':API_KEY
    }

    params={
            "query":query,
            "cursor":cursor
            }

    res=requests.get(SEARCH_URL,headers=headers,params=params)
    return res.json()


def get_tweets(query,n=1):
    """
    Docstring for _get_tweets_rec
    
    :param query: Description
    :param n: count of recursive cursor
    """
    cursor=""
    last_tweet_id=None
    def is_last_tweet(tweets):
        if tweets:
            if tweets[-1]["id"] == last_tweet_id:
                return True
        return False
    for _ in range(n):
        res=_get_tweets(query,cursor=cursor)
        cursor=res["next_cursor"]
        for tweet in res["tweets"]:
            yield tweet
        if is_last_tweet(res["tweets"]):
            return
        if res["tweets"]:
            last_tweet_id=res["tweets"][-1]["id"]
        if not cursor:
            return
        

def get_tweets_by_userid(userid,n=1):
    query=f"from:{userid}"
    return get_tweets(query,n=n)

def is_image(media_data):
    media_type = media_data.get('type') or ''
    return media_type in ['photo', 'image']

def _get_media_urls_by_userid(userid,min_=10):
    count=0
    for tweet in get_tweets_by_userid(userid,n=10**32):
        media=tweet.get("extendedEntities")
        if not media:
            continue
        for media_item in filter(is_image,media.get("media") or []):
            imgurl=media_item.get("media_url_https")
            yield {
                "tweet":tweet,
                "media":media_item,
                "imgurl":imgurl
            }
            count+=1
        if count >= min_:    #min_にたいした返却
            return

def get_mediaid_by_imgurl(imgurl):
    #https://pbs.twimg.com/media/GaN5fQUbUAExiPX.jpg
    a=re.search("media/([a-zA-Z0-9]+)\.jpe?g",imgurl)
    if not a:
        return None
    return a.group(1)

if __name__ == "__main__":
    userid="@kamisama_info_"
    userid="@artemis_shiori"
    n=50
    for imgurl in _get_media_urls_by_userid(userid,min_=n):
        print(imgurl)