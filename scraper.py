"""
Remote Tech Jobs for Nigerians — Scraper #1: We Work Remotely
----------------------------------------------------------------
Pulls remote programming jobs from WWR's public RSS feed, tags which
ones look Africa/Nigeria-eligible, and saves everything to jobs.json.

Run with:  py scraper.py
(or:       python scraper.py   on Mac/Linux)

Requires: requests, feedparser
Install with:  py -m pip install requests feedparser
"""

import json
import os
import re
from datetime import datetime, timezone

import feedparser

# ---- Config ---------------------------------------------------------

WWR_FEEDS = {
    "programming": "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "customer-support": "https://weworkremotely.com/categories/remote-customer-support-jobs.rss",
    "devops-sysadmin": "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
}

DATA_FILE = "jobs.json"

# Keywords that suggest a role is open to Africa/Nigeria (vs. "US only", "US timezones")
AFRICA_FRIENDLY_HINTS = [
    "anywhere", "worldwide", "global", "remote - global", "any location",
    "international", "emea", "africa",
]
AFRICA_UNFRIENDLY_HINTS = [
    "us only", "usa only", "united states only", "us-based", "us timezone",
    "north america only", "canada only", "uk only", "eu only", "eu-based",
]

# ---- Helpers ---------------------------------------------------------


def guess_africa_eligible(title: str, summary: str) -> str:
    """Very rough heuristic. Returns 'yes', 'no', or 'unclear'."""
    text = f"{title} {summary}".lower()
    if any(bad in text for bad in AFRICA_UNFRIENDLY_HINTS):
        return "no"
    if any(good in text for good in AFRICA_FRIENDLY_HINTS):
        return "yes"
    return "unclear"


def parse_company_and_title(entry_title: str):
    # WWR titles are usually formatted as "Company: Job Title"
    if ":" in entry_title:
        company, title = entry_title.split(":", 1)
        return company.strip(), title.strip()
    return "Unknown", entry_title.strip()


def clean_summary(raw_html: str) -> str:
    text = re.sub("<[^<]+?>", "", raw_html or "")
    return " ".join(text.split())[:400]


def load_existing_jobs():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_jobs(jobs):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)


# ---- Main scrape ------------------------------------------------------


def scrape():
    existing = load_existing_jobs()
    existing_urls = {job["url"] for job in existing}

    new_jobs = []
    total_seen = 0

    for source_tag, feed_url in WWR_FEEDS.items():
        feed = feedparser.parse(feed_url)

        if feed.bozo and not feed.entries:
            print(f"⚠️  Could not read feed: {source_tag} ({feed_url})")
            continue

        for entry in feed.entries:
            total_seen += 1
            url = entry.get("link", "").strip()
            if not url or url in existing_urls:
                continue

            company, title = parse_company_and_title(entry.get("title", ""))
            summary = clean_summary(entry.get("summary", ""))

            job = {
                "title": title,
                "company": company,
                "location_policy": "remote",
                "salary_range": None,  # WWR RSS rarely includes salary
                "url": url,
                "source": f"weworkremotely-{source_tag}",
                "date_posted": entry.get("published", datetime.now(timezone.utc).isoformat()),
                "africa_eligible": guess_africa_eligible(title, summary),
                "tags": [source_tag],
                "summary": summary,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            }

            new_jobs.append(job)
            existing_urls.add(url)

    all_jobs = existing + new_jobs
    save_jobs(all_jobs)

    print(f"Scraper ran. {total_seen} jobs seen across feeds.")
    print(f"{len(new_jobs)} new jobs added. {len(existing)} already stored.")
    print(f"Total jobs in {DATA_FILE}: {len(all_jobs)}")

    if new_jobs:
        print("\nSample of new jobs:")
        for job in new_jobs[:5]:
            print(f"  - [{job['africa_eligible']}] {job['company']}: {job['title']}")


if __name__ == "__main__":
    scrape()
