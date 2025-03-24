import os
import tweepy
import google.generativeai as genai
import random
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_twitter_api():
    """Sets up and returns the Tweepy API client."""
    try:
        auth = tweepy.OAuth1UserHandler(
            os.environ['TWITTER_API_KEY'],
            os.environ['TWITTER_API_SECRET'],
            os.environ['TWITTER_ACCESS_TOKEN'],
            os.environ['TWITTER_ACCESS_SECRET']
        )
        return tweepy.API(auth)
    except KeyError as e:
        logging.error(f"Missing environment variable: {e}")
        return None
    except tweepy.TweepyException as e:
        logging.error(f"Twitter API authentication failed: {e}")
        return None

def setup_gemini_api():
    """Configures and returns the Gemini AI model."""
    try:
        genai.configure(api_key=os.environ['GEMINI_API_KEY'])
        return genai.GenerativeModel("gemini-pro")
    except KeyError as e:
        logging.error(f"Missing Gemini API key: {e}")
        return None
    except Exception as e:
        logging.error(f"Gemini API configuration failed: {e}")
        return None

def generate_tweet(model):
    """Generates a tweet using Gemini AI."""
    if not model:
        return None

    topics = ["Data Science", "AI/ML", "Prompt Engineering", "Funnel Engineering", "Data Analytics"]
    prompt = f"""
    Write a Twitter post about {random.choice(topics)}.
    Avoid phrases like 'As an AI' or '--'.
    Write in an engaging and human-like way, as if an expert is sharing their thoughts.
    Keep it short and impactful.
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logging.error(f"Gemini API tweet generation failed: {e}")
        return None

def post_tweet(api, model):
    """Posts a tweet to Twitter."""
    if not api:
        return
    tweet = generate_tweet(model)
    if tweet:
        try:
            api.update_status(tweet)
            logging.info(f"Tweeted: {tweet}")
        except tweepy.TweepyException as e:
            logging.error(f"Twitter API tweet posting failed: {e}")

def like_tweets(api):
    """Likes tweets with relevant hashtags."""
    if not api:
        return
    hashtags = ["#DataScience", "#MachineLearning", "#AI", "#Analytics", "#FunnelEngineering"]
    for hashtag in hashtags:
        try:
            for tweet in tweepy.Cursor(api.search_tweets, q=hashtag, lang="en").items(5):
                try:
                    api.create_favorite(tweet.id)
                    logging.info(f"Liked: {tweet.text}")
                    time.sleep(5) #Adding a delay to avoid rate limits.
                except tweepy.TweepyException as e:
                    logging.error(f"Error liking tweet: {e}")
        except tweepy.TweepyException as e:
            logging.error(f"Error searching for tweets: {e}")

def retweet_tweets(api):
    """Retweets relevant posts."""
    if not api:
        return
    hashtags = ["#DataScience", "#MachineLearning", "#AI", "#Analytics", "#FunnelEngineering"]
    for hashtag in hashtags:
        try:
            for tweet in tweepy.Cursor(api.search_tweets, q=hashtag, lang="en").items(2):
                try:
                    api.retweet(tweet.id)
                    logging.info(f"Retweeted: {tweet.text}")
                    time.sleep(5) #Adding a delay to avoid rate limits.
                except tweepy.TweepyException as e:
                    logging.error(f"Error retweeting: {e}")
        except tweepy.TweepyException as e:
            logging.error(f"Error searching for tweets: {e}")

def reply_to_tweets(api, model):
    """Replies to tweets with human-like responses."""
    if not api or not model:
        return
    hashtags = ["#DataScience", "#AI", "#ML", "#Analytics"]
    for hashtag in hashtags:
        try:
            for tweet in tweepy.Cursor(api.search_tweets, q=hashtag, lang="en").items(2):
                try:
                    user = tweet.user.screen_name
                    prompt = f"""
                    Write a natural, engaging, and insightful reply to this tweet:
                    '{tweet.text}'
                    Do not say 'As an AI' or use '--'. Keep it short and conversational.
                    """
                    response = model.generate_content(prompt).text.strip()
                    api.update_status(f"@{user} {response}", in_reply_to_status_id=tweet.id)
                    logging.info(f"Replied to @{user}: {response}")
                    time.sleep(5) #Adding a delay to avoid rate limits.
                except tweepy.TweepyException as e:
                    logging.error(f"Error replying: {e}")
                except Exception as e:
                    logging.error(f"Gemini API reply failed: {e}")
        except tweepy.TweepyException as e:
            logging.error(f"Error searching for tweets: {e}")

# GitHub Actions entry point
def main():
    """Main function to run the Twitter bot."""
    api = setup_twitter_api()
    model = setup_gemini_api()

    if api and model:
        function_to_run = os.environ.get('BOT_FUNCTION') #gets the function name from the github action env.

        if function_to_run == 'post_tweet':
            post_tweet(api, model)
        elif function_to_run == 'like_tweets':
            like_tweets(api)
        elif function_to_run == 'retweet_tweets':
            retweet_tweets(api)
        elif function_to_run == 'reply_to_tweets':
            reply_to_tweets(api, model)
        else:
            logging.error("Invalid BOT_FUNCTION environment variable.")
    else:
        logging.error("API setup failed. Bot will not run.")

if __name__ == "__main__":
    main()
