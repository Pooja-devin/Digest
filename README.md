# Digest

Digest is a Streamlit opportunity scout for engineering students. It seeds flagship programs, imports selected tech and jobs RSS feeds, uses Gemini to normalize unstructured entries, and provides a database-grounded chat assistant.

## Setup

```bash
pip install streamlit google-genai feedparser python-dotenv pydantic httpx
```

Create `.env` in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
```

The dashboard works without a key for seeded data and feed syncing; Gemini is required for AI extraction and chat responses.

## Run

```bash
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

`digest.db` is created automatically. Seed records use unique `apply_url` values, so startup is idempotent and duplicate feed entries are ignored.