import os
import json
import logging
import random
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from requests_oauthlib import OAuth1Session
import datetime
import schedule
import time
from sentence_transformers import SentenceTransformer, util
import torch

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Google Sheets Setup
def setup_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        credentials_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
        if not credentials_json:
            logging.error("GOOGLE_SHEETS_CREDENTIALS secret not found.")
            return None

        credentials_dict = json.loads(credentials_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
        client = gspread.authorize(creds)
        sheet_id = "1l6N6oZjRM7NPE3fRgBR2IFcD0oXxEQ7oBEdd5KCsKi4"
        sheet_name = "History"

        try:
            sheet = client.open_by_key(sheet_id).worksheet(sheet_name)
            logging.info("Google Sheets setup successful.")
            return sheet

        except gspread.exceptions.WorksheetNotFound:
            logging.error(f"Worksheet '{sheet_name}' not found.")
            return None

        except gspread.exceptions.SpreadsheetNotFound:
            logging.error(f"Spreadsheet with id '{sheet_id}' not found.")
            return None

        except Exception as e:
            logging.error(f"Error opening sheet or worksheet: {e}")
            return None

    except Exception as e:
        logging.error(f"Error setting up Google Sheets: {e}")
        return None

# Twitter Setup
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

# Gemini AI Setup
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

# Semantic Similarity Check
def is_semantically_similar(new_tweet, existing_tweets, similarity_threshold=0.9):
    if not existing_tweets:
        return False
    model = SentenceTransformer('all-mpnet-base-v2')
    new_embedding = model.encode(new_tweet, convert_to_tensor=True)
    existing_embeddings = model.encode(existing_tweets, convert_to_tensor=True)
    cosine_scores = util.cos_sim(new_embedding, existing_embeddings)
    return torch.any(cosine_scores > similarity_threshold).item()

# Generate Tweet
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
        logging.info(f"Generated tweet: {tweet_text}")
        return tweet_text
    except Exception as e:
        logging.error(f"Gemini API tweet generation failed: {e}")
        return None

# Post Tweet
def post_tweet(oauth, tweet_text):
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

# Scheduled Tweet Posting
def post_scheduled_tweet():
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

    # Setup APIs
    oauth = setup_twitter_oauth()
    gemini_model = setup_gemini_api()
    sheet = setup_google_sheets()

    if oauth and gemini_model and sheet:
        topic = random.choice(niche_topics)
        tweet_text = generate_tweet(gemini_model, topic)

        if tweet_text:
            existing_tweets = sheet.col_values(1)
            if is_semantically_similar(tweet_text, existing_tweets):
                logging.info("Tweet is too similar to previous tweets. Skipping...")
            else:
                post_tweet(oauth, tweet_text)
                save_tweet(sheet, tweet_text)

# Schedule Tweets Every 6 Hours (4 tweets per day)
schedule.every().day.at("06:00").do(post_scheduled_tweet)
schedule.every().day.at("12:00").do(post_scheduled_tweet)
schedule.every().day.at("18:00").do(post_scheduled_tweet)
schedule.every().day.at("00:00").do(post_scheduled_tweet)

# Run Scheduler
if __name__ == "__main__":
    logging.info("Tweet scheduling started.")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute
