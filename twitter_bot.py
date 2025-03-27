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
        sheet = client.open_by_key("1l6N6oZjRM7NPE3fRgBR2IFcD0oXxEQ7oBEdd5KCsKi4").worksheet("History")
        logging.info("Google Sheets setup successful.")
        return sheet
    except Exception as e:
        logging.error(f"Error setting up Google Sheets: {e}")
        return None

def check_existing_tweet(sheet, tweet_text):
    existing_tweets = sheet.col_values(1)
    return tweet_text in existing_tweets

def save_tweet(sheet, tweet_text):
    logging.info(f"Attempting to save tweet: {tweet_text}")
    print("save_tweet function called")
    if sheet is not None:
        print(f"sheet object is: {sheet}")
        try:
            sheet.append_row([tweet_text, str(datetime.datetime.now())])
            logging.info("Tweet saved to sheet.")
        except Exception as e:
            logging.error(f"Error saving tweet to sheet: {e}")
            print(f"Error saving tweet to sheet: {e}")
    else:
        logging.error("Google sheet object is none, unable to save tweet.")
        print("Google sheet object is none")

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

def generate_hashtags(gemini_model, tweet_text):
    if not gemini_model:
        return ""
    prompt = f"Generate 3 relevant hashtags for the following tweet: '{tweet_text}'"
    try:
        response = gemini_model.generate_content(prompt)
        hashtags = response.text.replace("#", "").split()
        hashtags = " #"+" #".join(hashtags)
        return hashtags
    except Exception as e:
        logging.error(f"Gemini API hashtag generation failed: {e}")
        return ""

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
        hashtags = generate_hashtags(gemini_model, tweet_text)
        tweet_text += f" {hashtags}"
        logging.info(f"Generated tweet: {tweet_text}")
        return tweet_text
    except Exception as e:
        logging.error(f"Gemini API tweet generation failed: {e}")
        return None

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
            "prompt Engineering",
            "Feature Engineering in ML",
            "Python Libraries for Data Science"
        ]

        now = datetime.datetime.now()
        time_interval = datetime.timedelta(hours=6)

        for i in range(4):
            scheduled_time = now + (time_interval * i)
            time_to_wait = (scheduled_time - datetime.datetime.now()).total_seconds()
            if time_to_wait > 0:
                logging.info(f"Waiting for {time_to_wait} seconds until next post at {scheduled_time}.")
                time.sleep(time_to_wait)

            selected_topic = random.choice(niche_topics)
            tweet_text = generate_tweet(gemini_model, selected_topic)

            if tweet_text:
                existing_tweets = sheet.col_values(1)
                if not is_semantically_similar(tweet_text, existing_tweets):
                    post_tweet(oauth, tweet_text)
                    save_tweet(sheet, tweet_text)
                    time.sleep(15)
                else:
                    logging.info("Semantically similar tweet already exists, generating a new one.")
            else:
                logging.error("Failed to generate tweet.")
    else:
        logging.error("Twitter, Gemini API, or Google Sheets setup failed.")

if __name__ == "__main__":
    main()
