import streamlit as st
import pandas as pd
from google import genai
from pipeline import fetch_all_sources, APP_CONFIGS
from classify import classify_all

st.set_page_config(page_title="Feedback Triage Pipeline", layout="wide")

st.title("📋 User Feedback Triage Pipeline")
st.caption("Pulls real reviews/discussions for an AI app and classifies them by category, sentiment, and urgency.")

# --- Sidebar controls ---
app_name = st.sidebar.selectbox("Choose an app", list(APP_CONFIGS.keys()))
api_key = st.sidebar.text_input("Gemini API Key", type="password")
run_button = st.sidebar.button("Run Triage", type="primary")

if run_button:
    if not api_key:
        st.error("Please enter your Gemini API key in the sidebar.")
        st.stop()

    client = genai.Client(api_key=api_key)

    # --- Fetch step ---
    with st.spinner(f"Fetching real reviews for {app_name}..."):
        combined_df = fetch_all_sources(app_name)
    st.success(f"Fetched {len(combined_df)} items from Google Play, Apple App Store, and Hacker News.")

    # --- Classify step ---
    progress_bar = st.progress(0, text="Classifying...")

    def update_progress(current, total):
        progress_bar.progress(current / total, text=f"Classifying batch {current}/{total}...")

    final_df, failed_batches = classify_all(combined_df, client, batch_size=20, progress_callback=update_progress)
    progress_bar.empty()

    if failed_batches:
        st.warning(f"{len(failed_batches)} batch(es) failed to classify and were skipped.")

    st.success(f"Classified {len(final_df)}/{len(combined_df)} items.")

    # --- Results ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total items", len(final_df))
    col2.metric("High urgency", len(final_df[final_df['urgency'] == 'high']))
    col3.metric("Bugs reported", len(final_df[final_df['category'] == 'bug']))

    tab1, tab2, tab3 = st.tabs(["🔥 Priority Items", "📊 Breakdown", "📄 All Data"])

    with tab1:
        st.subheader("High-urgency bugs & complaints")
        priority = final_df[
            (final_df['urgency'] == 'high') &
            (final_df['category'].isin(['bug', 'complaint']))
        ][['source', 'category', 'sentiment', 'summary']]
        st.dataframe(priority, use_container_width=True)

    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            st.bar_chart(final_df['category'].value_counts())
        with c2:
            st.bar_chart(final_df['urgency'].value_counts())

    with tab3:
        st.dataframe(final_df, use_container_width=True)
        st.download_button(
            "Download as CSV",
            final_df.to_csv(index=False),
            file_name=f"{app_name}_feedback_triage.csv"
        )
else:
    st.info("👈 Choose an app, enter your Gemini API key, and click 'Run Triage' to begin.")