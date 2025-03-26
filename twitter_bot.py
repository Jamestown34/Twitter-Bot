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
        return model
    except KeyError as e:
        logging.error(f"Missing Gemini API key: {e}")
        return None
    except Exception as e:
        logging.error(f"Gemini API configuration failed: {e}")
        return None

def generate_tweet(gemini_model, topic):
    """Generates a tweet using Gemini AI, based on a given topic."""
    if not gemini_model:
        return None
    
    tweet_styles = [
        "Share an insightful fact about {topic}. Keep it concise and engaging.",
        "Write a thought-provoking question about {topic} to spark discussion.",
        "Post a quick tip or hack related to {topic}.",
        "Create a short and witty take on {topic}.",
        "Write a motivational quote related to {topic}."
    ]
    
    selected_style = random.choice(tweet_styles).format(topic=topic)
    
    try:
        response = gemini_model.generate_content(selected_style)
        tweet_text = response.text
        
        # Append relevant hashtags
        hashtags = {
            "AI Ethics and Bias": "#AI #Ethics #MachineLearning",
            "Data Visualization Best Practices": "#DataViz #Analytics #Visualization",
            "SQL Tips for Data Analysts": "#SQL #DataAnalytics #TechTips",
            "Machine Learning Model Optimization": "#ML #AI #DeepLearning",
            "Big Data Trends": "#BigData #AI #DataScience"
        }
        tweet_text += f" {hashtags.get(topic, '#Tech #AI')}"
        
        logging.info(f"Generated tweet: {tweet_text}")
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
        niche_topics = [
            "AI Ethics and Bias", 
            "Data Visualization Best Practices",
            "SQL Tips for Data Analysts",
            "Machine Learning Model Optimization",
            "Big Data Trends",
            "Cloud Computing for AI",
            "Data Security and Privacy",
            "Real-world Applications of AI",
            "Feature Engineering in ML",
            "Python Libraries for Data Science"
        ]

        now = datetime.datetime.now()
        time_interval = datetime.timedelta(hours=6)  # Post every 6 hours

        for i in range(4):  # Post 4 times a day
            scheduled_time = now + (time_interval * i)
            time_to_wait = (scheduled_time - datetime.datetime.now()).total_seconds()
            if time_to_wait > 0:
                logging.info(f"Waiting for {time_to_wait} seconds until next post at {scheduled_time}.")
                time.sleep(time_to_wait)
            
            selected_topic = random.choice(niche_topics)
            tweet_text = generate_tweet(gemini_model, selected_topic)
            if tweet_text:
                post_tweet(oauth, tweet_text)
            else:
                logging.error("Failed to generate tweet.")
    else:
        logging.error("Twitter or Gemini API setup failed.")

if __name__ == "__main__":
    main()
