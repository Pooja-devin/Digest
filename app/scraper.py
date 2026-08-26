from html.parser import HTMLParser
from urllib.parse import urljoin

import feedparser
import httpx

from app.ai_extractor import extract_structured_opportunity
from app.database import Opportunity, insert_opportunity

FEEDS = [
    {"org": "Google", "url": "https://www.google.com/about/careers/applications/jobs/results?location=India&target_level=INTERN_AND_APPRENTICE", "category": "Internship"},
    {"org": "Internshala", "url": "https://internshala.com/internships/product-management-internship/", "category": "Internship"},
    {"org": "Google", "url": "https://blog.google/technology/developers/rss/", "category": "Tech Update"},
    {"org": "Microsoft", "url": "https://devblogs.microsoft.com/feed/", "category": "Tech Update"},
    {"org": "Hacker News", "url": "https://hnrss.org/jobs", "category": "Internship"},
]


class ListingParser(HTMLParser):
    """Extract useful links from career pages that do not expose RSS."""

    def __init__(self) -> None:
        super().__init__()
        self.listings: list[tuple[str, str]] = []
        self._href = ""
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._href = dict(attrs).get("href") or ""
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href:
            self._text.append(data.strip())

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href:
            title = " ".join(" ".join(self._text).split())
            if title and len(title) > 8:
                self.listings.append((title, self._href))
            self._href = ""
            self._text = []


def _entries(response: httpx.Response, source: dict[str, str]) -> list[dict[str, str]]:
    feed = feedparser.parse(response.content)
    if feed.entries:
        return [
            {"title": entry.get("title", ""), "content": entry.get("summary", entry.get("title", "")), "link": entry.get("link", "")}
            for entry in feed.entries[:5]
            if entry.get("link")
        ]

    parser = ListingParser()
    parser.feed(response.text)
    entries = []
    for title, link in parser.listings[:5]:
        entries.append({"title": title, "content": title, "link": urljoin(str(source["url"]), link)})
    return entries


def sync_feeds() -> int:
    inserted = 0
    headers = {"User-Agent": "Digest student opportunity scout/1.0"}
    with httpx.Client(timeout=15, follow_redirects=True, headers=headers) as client:
        for source in FEEDS:
            try:
                response = client.get(source["url"])
                response.raise_for_status()
                entries = _entries(response, source)
            except httpx.HTTPError as error:
                print(f"Error fetching {source['url']}: {error}")
                continue

            for entry in entries:
                content = entry["content"]
                link = entry["link"]
                data = {}
                try:
                    data = extract_structured_opportunity(content, link)
                except Exception as error:
                    print(f"AI extraction unavailable for {link}: {error}")
                try:
                    opp = Opportunity(
                        title=data.get("title") or entry["title"],
                        category=data.get("category") if data.get("category") in {"Internship", "Student Program", "Tech Update", "Hackathon"} else source["category"],
                        organization=data.get("organization") or source["org"],
                        eligibility=data.get("eligibility") or "Open for all students",
                        deadline=data.get("deadline") or "Rolling / Apply Soon",
                        apply_url=data.get("apply_url") or link,
                        summary=data.get("summary") or f"{entry['title']} is a current listing or update from {source['org']}. Check the source link for the latest details."
                    )
                    inserted += int(insert_opportunity(opp))
                except Exception as error:
                    print(f"Error processing {link}: {error}")
    return inserted