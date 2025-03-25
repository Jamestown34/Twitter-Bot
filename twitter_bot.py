import os
import json
import logging
import random
import google.generativeai as genai
from requests_oauthlib import OAuth1Session
import time
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_twitter_oauth():
    """Sets up and returns the Twitter OAuth 1.0a session."""
    consumer_key = os.environ.get("TWITTER_API_KEY")
    consumer_secret = os.environ.get("TWITTER_API_SECRET")
    access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.environ.get("TWITTER_ACCESS_SECRET")

    if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
        logging.error("Missing Twitter API credentials.")
        return None

    return OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret,
    )

def setup_gemini_api():
    """Configures and returns the Gemini AI model."""
    try:
        genai.configure(api_key=os.environ['GEMINI_API_KEY'])
        model = genai.GenerativeModel('models/gemini-1.5-pro-latest')

        #Debugging. List models.
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
    """Generates a tweet using Gemini AI, with niche randomization."""
    if not gemini_model:
        return None

    niche_topics = [
        "datascience",
        "data analytics",
        "AI/ML",
        "funnel engineering",
        "prompt engineering"
    ]

    selected_topic = random.choice(niche_topics)
    prompt = f"Write a short, engaging tweet about {selected_topic}, like a human without any (---) characters."

    try:
        response = gemini_model.generate_content(prompt)
        tweet_text = response.text
        logging.info(f"Generated tweet: {tweet_text}") #verification logging
        return tweet_text
    except Exception as e:
        logging.error(f"Gemini API tweet generation failed: {e}")
        return None

def post_tweet(oauth, tweet_text):
    """Posts a tweet to Twitter using OAuth 1.0a."""
    if not oauth or not tweet_text:
        return

    payload = {"text": tweet_text}

    try:
        response = oauth.post("https://api.twitter.com/2/tweets", json=payload)

        if response.status_code != 201:
            logging.error(f"Twitter API error: {response.status_code} {response.text}")
            return
        logging.info(f"Tweet posted: {tweet_text}")
    except Exception as e:
        logging.error(f"Twitter API error: {e}")

def main():
    oauth = setup_twitter_oauth()
    gemini_model = setup_gemini_api()

    if oauth and gemini_model:
        for _ in range(6):  # Post 6 times a day
            tweet_text = generate_tweet(gemini_model)
            if tweet_text:
                post_tweet(oauth, tweet_text)
            else:
                logging.error("Failed to generate tweet.")

            # Calculate random delay (up to 4 hours)
            delay_seconds = random.randint(0, 4 * 3600)  # 4 hours in seconds
            logging.info(f"Waiting for {delay_seconds} seconds before next post. Delay: {delay_seconds} seconds")
            time.sleep(delay_seconds)
    else:
        logging.error("Twitter or Gemini API setup failed.")

if __name__ == "__main__":
    main()
