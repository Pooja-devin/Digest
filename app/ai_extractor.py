import json
import os
from typing import Optional

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()


def get_client() -> Optional[genai.Client]:
    api_key = os.getenv("GEMINI_API_KEY")
    return genai.Client(api_key=api_key) if api_key else None

SYSTEM_PROMPT = """
You are the parsing engine for 'Digest', a student-focused tech scout.
Analyze the raw web feed or career listing and return only valid, parseable JSON.
Do not include Markdown fences, commentary, or any text outside the JSON object.
Use exactly this schema:
{
    "title": "Clear, concise opportunity or announcement title",
    "category": "Internship | Student Program | Tech Update | Hackathon",
    "organization": "Company or organization name",
    "eligibility": "Target batches, academic criteria, or Open for all students",
    "deadline": "Exact date, or Rolling / Apply Soon",
    "apply_url": "Direct URL link",
    "summary": "At most 2 concise sentences explaining what this is and why it matters to a tech student."
}
Never invent missing deadlines, eligibility details, or URLs. Use the supplied source URL when it is
the direct application or announcement link; otherwise preserve it as the fallback application URL.
"""

def extract_structured_opportunity(raw_text: str, link: str) -> dict:
    client = get_client()
    if client is None:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    prompt = f"{SYSTEM_PROMPT}\n\nLink: {link}\nContent: {raw_text}"
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    data = json.loads(response.text)
    data["apply_url"] = data.get("apply_url") or link
    return data