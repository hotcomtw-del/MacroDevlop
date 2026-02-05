#!/usr/bin/env python3
"""Finance & politics news collector using RSS/Atom feeds."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from typing import Iterable
from urllib.error import URLError
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


REGION_KEYWORDS: dict[str, tuple[str, ...]] = {
    "美國": ("US", "U.S.", "United States", "America", "American", "Fed", "Federal Reserve", "Biden", "Trump", "Congress"),
    "歐洲": ("Europe", "European", "EU", "ECB", "UK", "Britain", "France", "Germany", "Italy", "Spain", "NATO"),
    "日本": ("Japan", "Japanese", "Tokyo", "BOJ", "Bank of Japan", "Yen"),
    "台灣": ("Taiwan", "Taipei", "TSMC"),
    "中國": ("China", "Chinese", "Beijing", "Shanghai", "PBOC"),
}

TOPIC_KEYWORDS: dict[str, tuple[str, ...]] = {
    "財政政策": ("budget", "fiscal", "tax", "taxes", "spending", "debt", "deficit", "treasury"),
    "經濟政策": ("interest rate", "rates", "inflation", "monetary", "central bank", "stimulus", "policy"),
    "政治動態": ("election", "vote", "parliament", "government", "cabinet", "president", "prime minister", "policy"),
    "產業消息": ("earnings", "stocks", "markets", "industry", "company", "shares", "profit", "supply chain"),
}


@dataclass
class FeedSource:
    name: str
    category: str
    url: str


DEFAULT_SOURCES: list[FeedSource] = [
    FeedSource("Reuters World Politics", "politics", "https://feeds.reuters.com/Reuters/worldNews"),
    FeedSource("Reuters Business", "finance", "https://feeds.reuters.com/reuters/businessNews"),
    FeedSource("BBC Politics", "politics", "http://feeds.bbci.co.uk/news/politics/rss.xml"),
    FeedSource("BBC Business", "finance", "http://feeds.bbci.co.uk/news/business/rss.xml"),
    FeedSource("NPR Politics", "politics", "https://feeds.npr.org/1014/rss.xml"),
    FeedSource("NPR Business", "finance", "https://feeds.npr.org/1006/rss.xml"),
    FeedSource("The Economist", "finance", "https://www.economist.com/finance-and-economics/rss.xml"),
    FeedSource("The Economist Politics", "politics", "https://www.economist.com/weeklyedition/rss.xml"),
    FeedSource("Financial Times", "finance", "https://www.ft.com/?format=rss"),
    FeedSource("Wall Street Journal", "finance", "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"),
]


@dataclass
class NewsItem:
    source: str
    category: str
    region: str
    topic: str
    title: str
    link: str
    published: str | None


def fetch_feed(url: str, timeout: int = 15) -> str:
    request = Request(url, headers={"User-Agent": "MacroDevlop-NewsCollector/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="ignore")


def _strip_namespace(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def parse_feed(xml_text: str) -> Iterable[dict[str, str | None]]:
    root = ET.fromstring(xml_text)
    root_tag = _strip_namespace(root.tag)

    if root_tag == "rss" or root_tag == "rdf":
        channel = root.find("channel")
        if channel is None:
            return []
        items = []
        for item in channel.findall("item"):
            items.append(
                {
                    "title": _get_text(item, "title"),
                    "link": _get_text(item, "link"),
                    "published": _get_text(item, "pubDate") or _get_text(item, "date"),
                }
            )
        return items

    if root_tag == "feed":
        items = []
        for entry in root.findall("{http://www.w3.org/2005/Atom}entry") or root.findall("entry"):
            link = ""
            for link_el in entry.findall("{http://www.w3.org/2005/Atom}link") or entry.findall("link"):
                if link_el.get("rel") in (None, "alternate"):
                    link = link_el.get("href", "")
                    if link:
                        break
            items.append(
                {
                    "title": _get_text(entry, "title"),
                    "link": link,
                    "published": _get_text(entry, "updated") or _get_text(entry, "published"),
                }
            )
        return items

    return []


def _get_text(parent: ET.Element, tag: str) -> str:
    for child in parent:
        if _strip_namespace(child.tag) == tag:
            return (child.text or "").strip()
    return ""


def classify_region(text: str) -> str:
    lowered = text.lower()
    for region, keywords in REGION_KEYWORDS.items():
        if any(keyword.lower() in lowered for keyword in keywords):
            return region
    return "其他地區"


def classify_topic(text: str) -> str:
    lowered = text.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(keyword.lower() in lowered for keyword in keywords):
            return topic
    return "產業消息"


def collect_news(sources: list[FeedSource], limit: int | None = None) -> list[NewsItem]:
    collected: list[NewsItem] = []
    for source in sources:
        try:
            xml_text = fetch_feed(source.url)
            entries = parse_feed(xml_text)
        except (URLError, ET.ParseError) as exc:
            print(f"Warning: failed to fetch {source.name}: {exc}", file=sys.stderr)
            continue

        for entry in entries:
            if not entry.get("title") or not entry.get("link"):
                continue
            title = entry["title"]
            region = classify_region(title)
            topic = classify_topic(title)
            collected.append(
                NewsItem(
                    source=source.name,
                    category=source.category,
                    region=region,
                    topic=topic,
                    title=title,
                    link=entry["link"],
                    published=entry.get("published"),
                )
            )
            if limit is not None and len(collected) >= limit:
                return collected

    return collected


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect finance and politics news via RSS feeds.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of items to collect.")
    parser.add_argument("--output", default="news.json", help="Output JSON file path.")
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.0,
        help="Seconds to sleep between feed requests (default: 0).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    start = time.time()
    items: list[NewsItem] = []
    for idx, source in enumerate(DEFAULT_SOURCES):
        items.extend(collect_news([source], limit=args.limit))
        if args.limit is not None and len(items) >= args.limit:
            items = items[: args.limit]
            break
        if args.sleep and idx < len(DEFAULT_SOURCES) - 1:
            time.sleep(args.sleep)

    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start)),
        "count": len(items),
        "items": [item.__dict__ for item in items],
    }
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)

    print(f"Collected {len(items)} items -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
