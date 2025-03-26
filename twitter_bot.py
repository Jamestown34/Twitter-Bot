import os
import json
import logging
import random
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from requests_oauthlib import OAuth1Session
import time
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Google Sheets Setup
SHEET_NAME = "TweetHistory"

def setup_google_sheets():
    """Sets up Google Sheets API authentication."""
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("google_sheets_key.json", [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ])
        client = gspread.authorize(creds)
        sheet = client.open(SHEET_NAME).sheet1
        return sheet
    except Exception as e:
        logging.error(f"Google Sheets setup failed: {e}")
        return None

def tweet_exists(sheet, tweet_text):
    """Checks if a tweet already exists in Google Sheets."""
    try:
        tweets = sheet.col_values(1)  # Assuming tweets are stored in the first column
        return tweet_text in tweets
    except Exception as e:
        logging.error(f"Error checking tweet existence: {e}")
        return False

def save_tweet(sheet, tweet_text):
    """Saves a new tweet to Google Sheets."""
    try:
        sheet.append_row([tweet_text, str(datetime.datetime.now())])
        logging.info("Tweet saved to Google Sheets.")
    except Exception as e:
        logging.error(f"Failed to save tweet: {e}")

# Twitter API Setup
def setup_twitter_oauth():
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

def post_tweet(oauth, sheet, tweet_text):
    if not oauth or not tweet_text:
        return
    
    if tweet_exists(sheet, tweet_text):
        logging.info("Tweet already posted, skipping.")
        return
    
    payload = {"text": tweet_text}
    
    try:
        response = oauth.post("https://api.twitter.com/2/tweets", json=payload)
        
        if response.status_code != 201:
            logging.error(f"Twitter API error: {response.status_code} {response.text}")
            return
        
        logging.info(f"Tweet posted: {tweet_text}")
        save_tweet(sheet, tweet_text)
    except Exception as e:
        logging.error(f"Twitter API error: {e}")

def main():
    oauth = setup_twitter_oauth()
    gemini_model = setup_gemini_api()
    sheet = setup_google_sheets()
    
    if oauth and gemini_model and sheet:
        niche_topics = [
            "AI Ethics and Bias", 
            "Data Visualization Best Practices",
            "SQL Tips for Data Analysts",
            "Machine Learning Model Optimization",
            "Big Data Trends",
            "Cloud Computing for AI",
            "Data Security and Privacy",
            "Real-world Applications of AI",
            "Prompt Engineering",
            "Feature Engineering in ML",
            "Python Libraries for Data Science"
        ]

        now = datetime.datetime.now()
        time_interval = datetime.timedelta(hours=6)

        for i in range(4):
            scheduled_time = now + (time_interval * i)
            time_to_wait = (scheduled_time - datetime.datetime.now()).total_seconds()
            if time_to_wait > 0:
                logging.info(f"Waiting {time_to_wait} seconds until next post at {scheduled_time}.")
                time.sleep(time_to_wait)
            
            selected_topic = random.choice(niche_topics)
            tweet_text = generate_tweet(gemini_model, selected_topic)
            if tweet_text:
                post_tweet(oauth, sheet, tweet_text)
            else:
                logging.error("Failed to generate tweet.")
    else:
        logging.error("Setup failed.")

if __name__ == "__main__":
    main()
