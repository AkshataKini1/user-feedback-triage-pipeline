import requests
import pandas as pd
import time
import json
import html
import re

# --- App configs: package names / IDs / search terms per app ---
APP_CONFIGS = {
    "Claude": {
        "google_play_id": "com.anthropic.claude",
        "apple_app_id": "6473753684",
        "hn_query": "Claude Anthropic"
    },
    "ChatGPT": {
        "google_play_id": "com.openai.chatgpt",
        "apple_app_id": "6448311069",
        "hn_query": "ChatGPT OpenAI app"
    },
    "Gemini": {
        "google_play_id": "com.google.android.apps.bard",
        "apple_app_id": "6477489729",
        "hn_query": "Gemini Google app"
    }
}


def clean_html(text):
    text = html.unescape(text)
    text = re.sub('<[^<]+?>', '', text)
    return text.strip()


def fetch_google_play(package_name, count=50):
    from google_play_scraper import reviews, Sort
    result, _ = reviews(package_name, lang='en', country='us', sort=Sort.NEWEST, count=count)
    df = pd.DataFrame(result)[['reviewId', 'content', 'score']]
    df.rename(columns={'reviewId': 'id', 'content': 'text', 'score': 'rating'}, inplace=True)
    df['rating'] = df['rating'].astype(str)
    df['source'] = 'google_play'
    return df[['id', 'source', 'text', 'rating']]


def fetch_hacker_news(query, hits=50):
    url = "https://hn.algolia.com/api/v1/search"
    params = {"query": query, "tags": "comment", "hitsPerPage": hits}
    response = requests.get(url, params=params)
    data = response.json()
    posts = []
    for hit in data['hits']:
        text = hit.get('comment_text', '')
        posts.append({
            'id': hit['objectID'],
            'source': 'hacker_news',
            'text': clean_html(text) if text else '',
            'rating': str(hit.get('points', 0))
        })
    return pd.DataFrame(posts)


def fetch_apple_app_store(app_id):
    url = f"https://itunes.apple.com/rss/customerreviews/id={app_id}/sortBy=mostRecent/json"
    response = requests.get(url)
    data = response.json()
    entries = data.get('feed', {}).get('entry', [])
    reviews_list = []
    for i, entry in enumerate(entries):
        text = entry.get('content', {}).get('label', '')
        rating = entry.get('im:rating', {}).get('label', '')
        if not text:
            continue
        reviews_list.append({
            'id': f"{i}_apple",
            'source': 'apple_app_store',
            'text': text,
            'rating': str(rating)
        })
    return pd.DataFrame(reviews_list)


def fetch_all_sources(app_name):
    config = APP_CONFIGS[app_name]
    gp = fetch_google_play(config['google_play_id'])
    hn = fetch_hacker_news(config['hn_query'])
    ap = fetch_apple_app_store(config['apple_app_id'])

    combined = pd.concat([gp, hn, ap], ignore_index=True)
    combined = combined[combined['text'].str.strip().str.len() > 5].reset_index(drop=True)
    return combined