import os
import tweepy
import google.generativeai as genai
import random
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_twitter_api():
    """Sets up and returns the Twitter API client."""
    try:
        client = tweepy.Client(
            consumer_key=os.environ['TWITTER_API_KEY'],
            consumer_secret=os.environ['TWITTER_API_SECRET'],
            access_token=os.environ['TWITTER_ACCESS_TOKEN'],
            access_token_secret=os.environ['TWITTER_ACCESS_SECRET']
        )
        return client
    except KeyError as e:
        logging.error(f"Missing Twitter API keys: {e}")
        return None

def setup_gemini_api():
    """Configures and returns the Gemini AI model."""
    try:
        genai.configure(api_key=os.environ['GEMINI_API_KEY'])
        model = genai.GenerativeModel('gemini-pro') # Make sure this is a listed model.
        #List models for debugging
        for listed_model in genai.list_models():
            logging.info(f"Available Gemini model: {listed_model}")

        return model
    except KeyError as e:
        logging.error(f"Missing Gemini API key: {e}")
        return None
    except Exception as e:
        logging.error(f"Gemini API configuration failed: {e}")
        return None

def generate_tweet(gemini_model):
    """Generates a tweet using Gemini AI."""
    if not gemini_model:
        return None

    try:
        response = gemini_model.generate_content("Write a short, engaging tweet.")
        tweet_text = response.text
        return tweet_text
    except Exception as e:
        logging.error(f"Gemini API tweet generation failed: {e}")
        return None

def post_tweet(twitter_client, tweet_text):
    """Posts a tweet to Twitter."""
    if not twitter_client or not tweet_text:
        return

    try:
        twitter_client.create_tweet(text=tweet_text)
        logging.info(f"Tweet posted: {tweet_text}")
    except tweepy.errors.TweepyException as e:
        logging.error(f"Twitter API error: {e}")

def main():
    twitter_client = setup_twitter_api()
    gemini_model = setup_gemini_api()

    if twitter_client and gemini_model:
        tweet_text = generate_tweet(gemini_model)
        if tweet_text:
            post_tweet(twitter_client, tweet_text)
        else:
            logging.error("Failed to generate tweet.")
    else:
        logging.error("Twitter or Gemini API setup failed.")

if __name__ == "__main__":
    main()
