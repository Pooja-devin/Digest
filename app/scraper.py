import feedparser
import httpx
from app.ai_extractor import extract_structured_opportunity
from app.database import Opportunity, insert_opportunity

FEEDS = [
    {"org": "Google", "url": "https://blog.google/technology/developers/rss/"},
    {"org": "Microsoft", "url": "https://devblogs.microsoft.com/feed/"},
    {"org": "HackerNews", "url": "https://hnrss.org/jobs"}
]

def sync_feeds() -> int:
    inserted = 0
    for source in FEEDS:
        try:
            response = httpx.get(source["url"], timeout=15, follow_redirects=True)
            response.raise_for_status()
            feed = feedparser.parse(response.content)
        except httpx.HTTPError as error:
            print(f"Error fetching {source['url']}: {error}")
            continue
        for entry in feed.entries[:3]:
            content = entry.get("summary", entry.get("title", ""))
            link = entry.get("link", "")
            try:
                data = extract_structured_opportunity(content, link)
                opp = Opportunity(
                    title=data.get("title", entry.title),
                    category=data.get("category", "Tech Update"),
                    organization=data.get("organization", source["org"]),
                    eligibility=data.get("eligibility", "General"),
                    deadline=data.get("deadline", "N/A"),
                    apply_url=data.get("apply_url", link),
                    summary=data.get("summary", "")
                )
                inserted += int(insert_opportunity(opp))
            except Exception as e:
                print(f"Error processing {link}: {e}")
    return inserted