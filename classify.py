import time
import json
import pandas as pd


def classify_batch(rows_df, client, model="gemini-flash-lite-latest"):
    items_text = ""
    for i, (idx, row) in enumerate(rows_df.iterrows()):
        items_text += f"\n{i}. \"{row['text']}\"\n"

    prompt = f"""Classify each of the following {len(rows_df)} pieces of user feedback into structured JSON.

For each item, return an object with these exact fields:
- index: the item number (matching the number before each item below)
- category: one of [bug, feature_request, complaint, praise, question, other]
- sentiment: one of [positive, negative, neutral, mixed]
- urgency: one of [low, medium, high]
- summary: a single sentence summarizing the core point

Respond with ONLY a valid JSON array of {len(rows_df)} objects, no markdown formatting, no explanation, no extra text before or after.

Items:
{items_text}
"""
    response = client.models.generate_content(model=model, contents=prompt)
    return response.text

ALLOWED_CATEGORIES = {"bug", "feature_request", "complaint", "praise", "question", "other"}
ALLOWED_SENTIMENTS = {"positive", "negative", "neutral", "mixed"}
ALLOWED_URGENCY = {"low", "medium", "high"}

def normalize_item(item):
    category = item.get('category', 'other')
    if category not in ALLOWED_CATEGORIES:
        category = 'other'

    sentiment = item.get('sentiment', 'neutral')
    if sentiment not in ALLOWED_SENTIMENTS:
        sentiment = 'neutral'

    urgency = item.get('urgency', 'low')
    if urgency not in ALLOWED_URGENCY:
        urgency = 'low'

    return category, sentiment, urgency

def parse_batch_result(raw_text):
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    try:
        return json.loads(cleaned), None
    except json.JSONDecodeError as e:
        return None, str(e)

def classify_batch_with_retry(batch, client, max_retries=3):
    for attempt in range(max_retries):
        try:
            return classify_batch(batch, client)
        except Exception as e:
            if "429" in str(e):
                wait = 15 * (attempt + 1)
                time.sleep(wait)
            else:
                raise
    raise Exception("Max retries hit")


def classify_all(combined_df, client, batch_size=20, progress_callback=None):
    all_results = []
    failed_batches = []
    num_batches = (len(combined_df) + batch_size - 1) // batch_size

    for batch_num in range(num_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(combined_df))
        batch = combined_df.iloc[start_idx:end_idx].reset_index(drop=True)

        if progress_callback:
            progress_callback(batch_num + 1, num_batches)

        try:
            raw = classify_batch_with_retry(batch, client)
            parsed, error = parse_batch_result(raw)

            if parsed is None:
                failed_batches.append(batch_num)
                continue

            for item in parsed:
                local_idx = item['index']
                original_row = batch.iloc[local_idx]
                category, sentiment, urgency = normalize_item(item)
                all_results.append({
                    'id': original_row['id'],
                    'source': original_row['source'],
                    'text': original_row['text'],
                    'rating': original_row['rating'],
                    'category': category,
                    'sentiment': sentiment,
                    'urgency': urgency,
                    'summary': item.get('summary')
                })

        except Exception as e:
            print(f"Batch {batch_num} failed with error: {e}")
            failed_batches.append(batch_num)

        if batch_num < num_batches - 1:
            time.sleep(10)

    return pd.DataFrame(all_results), failed_batches