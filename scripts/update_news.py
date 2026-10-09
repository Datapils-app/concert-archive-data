"""Collect Archive news and merge it into news.json.

Uses only the standard library. Source: Google News RSS searches. Only the
headline, source name, date and link are stored; the article text stays with
the publisher.
"""
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NEWS = ROOT / "news.json"
NEW_IMPORTANT = ROOT / "new_important.txt"

QUERIES = [
    '"Darius Keeler" OR "Danny Griffiths" Archive',
    'Archive band "Not In My Name"',
    'Archive trip hop band tour 2027',
]
MAX_AGE_DAYS = 120
MAX_ITEMS = 60

RELEVANT = re.compile(r"\bArchive\b", re.I)
BAND_HINT = re.compile(
    r"Keeler|Griffiths|Not In My Name|trip.?hop|Controlling Crowds|"
    r"Call to Arms|Lisa Mottram|Maria Q|Holly Martin|Axiom|Londinium",
    re.I,
)
IMPORTANT = re.compile(
    r"announce|new album|tour|tickets|new single|single|release|dates|title track",
    re.I,
)


def fetch(query: str) -> list[dict]:
    url = (
        "https://news.google.com/rss/search?q="
        + urllib.parse.quote(query)
        + "&hl=en&gl=NL&ceid=NL:en"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "concert-archive-news/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        root = ET.fromstring(r.read())
    out = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        source = (item.findtext("source") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = item.findtext("pubDate")
        if not (title and link and pub):
            continue
        if source and title.endswith(" - " + source):
            title = title[: -len(source) - 3].strip()
        out.append(
            {
                "title": title,
                "source": source,
                "link": link,
                "date": parsedate_to_datetime(pub).astimezone(timezone.utc),
            }
        )
    return out


def relevant(entry: dict) -> bool:
    t = entry["title"]
    return bool(RELEVANT.search(t) and BAND_HINT.search(t))


def make_id(entry: dict) -> str:
    return "auto-" + hashlib.sha1(entry["link"].encode()).hexdigest()[:12]


def main() -> int:
    data = json.loads(NEWS.read_text(encoding="utf-8"))
    items = data["items"]
    known = {i.get("id") for i in items}
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)

    found: dict[str, dict] = {}
    for q in QUERIES:
        try:
            for e in fetch(q):
                if e["date"] >= cutoff and relevant(e):
                    found[make_id(e)] = e
        except Exception as exc:  # one failing query must not stop the others
            print(f"query failed: {q!r}: {exc}", file=sys.stderr)

    added_important = []
    for nid, e in found.items():
        if nid in known:
            continue
        important = bool(IMPORTANT.search(e["title"]))
        src = e["source"] or "web"
        items.append(
            {
                "id": nid,
                "date": e["date"].strftime("%Y-%m-%d"),
                "title": {"nl": e["title"], "en": e["title"]},
                "text": {"nl": f"Bron: {src}", "en": f"Source: {src}"},
                "url": e["link"],
                "source": src,
                "important": important,
            }
        )
        if important:
            added_important.append(e["title"])

    items.sort(key=lambda i: i["date"], reverse=True)
    data["items"] = items[:MAX_ITEMS]
    data["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    NEWS.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if added_important:
        NEW_IMPORTANT.write_text("\n".join(added_important) + "\n", encoding="utf-8")
    elif NEW_IMPORTANT.exists():
        NEW_IMPORTANT.unlink()
    print(f"{len(found)} relevant, {len(added_important)} new important")
    return 0


if __name__ == "__main__":
    sys.exit(main())
