# User Feedback Triage Pipeline

Real-time feedback triage for AI apps. Aggregates reviews and discussions from three live sources (Google Play, Apple App Store, Hacker News), classifies them with an LLM, and surfaces what needs attention first.

**🔗 Live demo:** https://user-feedback-triage-pipeline-mbkyaeqefkrdzu9sjxqx8e.streamlit.app/

## What it does

Product feedback is scattered across app stores, forums, and support channels — nobody has time to read all of it manually. This tool:

1. Pulls real, live user feedback for a chosen AI app (Claude, ChatGPT, or Gemini) from three sources: Google Play reviews, Apple App Store reviews, and Hacker News discussions
2. Classifies each item using an LLM (Google Gemini Flash-Lite) into category, sentiment, and urgency, with a one-line summary
3. Surfaces a prioritized list of high-urgency bugs and complaints — the items worth looking at first

## How to run it

1. Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com)
2. Visit the [live app](https://user-feedback-triage-pipeline-mbkyaeqefkrdzu9sjxqx8e.streamlit.app/)
3. Paste your API key in the sidebar, choose an app, click "Run Triage"

To run locally instead:
```bash
git clone https://github.com/AkshataKini1/user-feedback-triage-pipeline
cd user-feedback-triage-pipeline
pip install -r requirements.txt
streamlit run app.py
```

## Architecture

- `pipeline.py` — fetches and normalizes data from all three sources
- `classify.py` — batches items, calls the Gemini API, parses and validates results
- `app.py` — Streamlit UI

## Known limitations

- No automated tests
- Google Play package names / Apple App IDs are hardcoded for 3 apps, not dynamically resolved from any app name

## Possible next steps

- Let users type any app name instead of choosing from a fixed dropdown
- Add a slider to control how many reviews are pulled per source