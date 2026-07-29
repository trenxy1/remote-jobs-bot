"""
Remote Tech Jobs for Nigerians — Telegram Bot
-------------------------------------------------
Serves job listings scraped by scraper.py (stored in jobs.json on GitHub)
via simple Telegram commands: /start, /jobs, /latest

Reads BOT_TOKEN from an environment variable — NEVER hardcode it.
On Railway: set TELEGRAM_BOT_TOKEN in the project's Variables tab.
"""

import os
import json
import requests
import telebot

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN environment variable")

# Raw GitHub URL to jobs.json — update the username/repo if different
JOBS_URL = "https://raw.githubusercontent.com/trenxy1/remote-jobs-bot/main/jobs.json"

MAX_JOBS_SHOWN = 8

bot = telebot.TeleBot(BOT_TOKEN)


def fetch_jobs():
    try:
        resp = requests.get(JOBS_URL, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error fetching jobs: {e}")
        return []


def format_job(job: dict) -> str:
    tag = {"yes": "🌍 Africa-friendly", "no": "🚫 Likely US/EU only", "unclear": "❓ Unclear eligibility"}
    eligibility = tag.get(job.get("africa_eligible"), "❓ Unclear eligibility")
    return (
        f"*{job.get('company', 'Unknown')}* — {job.get('title', 'Untitled role')}\n"
        f"{eligibility}\n"
        f"{job.get('url', '')}"
    )


@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "👋 Welcome! I track fresh remote tech jobs and flag which ones are likely open to applicants in Nigeria/Africa.\n\n"
        "Commands:\n"
        "/jobs — see the latest listings\n"
        "/latest — same as /jobs\n",
    )


@bot.message_handler(commands=["jobs", "latest"])
def jobs(message):
    all_jobs = fetch_jobs()
    if not all_jobs:
        bot.reply_to(message, "No jobs found yet — the scraper may not have run. Check back soon.")
        return

    # Most recently scraped first, prioritize africa_eligible == "yes"
    sorted_jobs = sorted(
        all_jobs,
        key=lambda j: (j.get("africa_eligible") != "yes", j.get("scraped_at", "")),
        reverse=False,
    )

    bot.reply_to(message, f"Found {len(all_jobs)} jobs total. Showing top {MAX_JOBS_SHOWN}:")
    for job in sorted_jobs[:MAX_JOBS_SHOWN]:
        bot.send_message(message.chat.id, format_job(job), parse_mode="Markdown", disable_web_page_preview=True)


if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
