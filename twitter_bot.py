import os
import tweepy
import google.generativeai as genai
import schedule
import time
import random
from dotenv import load_dotenv

# Load API keys from .env
load_dotenv()

TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Authenticate Twitter API
auth = tweepy.OAuth1UserHandler(
    TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET
)
api = tweepy.API(auth)

# Authenticate Gemini AI
genai.configure(api_key=GEMINI_API_KEY)

# Function to generate a tweet using Gemini AI
def generate_tweet():
    topics = [
        "Data Science", "AI/ML", "Prompt Engineering",
        "Funnel Engineering", "Data Analytics"
    ]
    prompt = f"""
    Write a Twitter post about {random.choice(topics)}. 
    Avoid phrases like 'As an AI' or '--'. 
    Write in an engaging and human-like way, as if an expert is sharing their thoughts.
    Keep it short and impactful.
    """
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)
    return response.text.strip()

# Function to post a tweet
def post_tweet():
    tweet = generate_tweet()
    api.update_status(tweet)
    print(f"Tweeted: {tweet}")

# Function to like tweets with relevant hashtags
def like_tweets():
    hashtags = ["#DataScience", "#MachineLearning", "#AI", "#Analytics", "#FunnelEngineering"]
    for hashtag in hashtags:
        for tweet in tweepy.Cursor(api.search_tweets, q=hashtag, lang="en").items(5):
            try:
                tweet.favorite()
                print(f"Liked: {tweet.text}")
            except Exception as e:
                print(f"Error liking tweet: {e}")

# Function to retweet relevant posts
def retweet_tweets():
    hashtags = ["#DataScience", "#MachineLearning", "#AI", "#Analytics", "#FunnelEngineering"]
    for hashtag in hashtags:
        for tweet in tweepy.Cursor(api.search_tweets, q=hashtag, lang="en").items(2):
            try:
                tweet.retweet()
                print(f"Retweeted: {tweet.text}")
            except Exception as e:
                print(f"Error retweeting: {e}")

# Function to reply to tweets with human-like responses
def reply_to_tweets():
    hashtags = ["#DataScience", "#AI", "#ML", "#Analytics"]
    for hashtag in hashtags:
        for tweet in tweepy.Cursor(api.search_tweets, q=hashtag, lang="en").items(2):
            try:
                user = tweet.user.screen_name
                prompt = f"""
                Write a natural, engaging, and insightful reply to this tweet: 
                '{tweet.text}'
                Do not say 'As an AI' or use '--'. Keep it short and conversational.
                """
                response = genai.GenerativeModel("gemini-pro").generate_content(prompt).text.strip()
                api.update_status(f"@{user} {response}", in_reply_to_status_id=tweet.id)
                print(f"Replied to @{user}: {response}")
            except Exception as e:
                print(f"Error replying: {e}")

# Schedule tasks
schedule.every().day.at("09:00").do(post_tweet)
schedule.every().hour.do(like_tweets)
schedule.every().day.at("12:00").do(retweet_tweets)
schedule.every().day.at("18:00").do(reply_to_tweets)

# Run bot continuously
while True:
    schedule.run_pending()
    time.sleep(60)

