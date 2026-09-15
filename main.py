"""Entry point: schedules scraping+classification+alerts and periodic reports.

Run:
    python main.py

Stop with Ctrl+C. Designed to run continuously (e.g. under systemd, tmux, or a
Docker container) since it uses an in-process scheduler loop.
"""
import logging
import time

import schedule

import config
import db
import x_scraper
import ai_classifier
import telegram_notifier
import reporter

logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("main")


def scrape_classify_alert_job() -> None:
    """Full 5-minute cycle: scrape new tweets, classify them, alert on useful ones."""
    try:
        x_scraper.scrape_and_store()
    except Exception:
        log.exception("Scrape step failed.")
        return

    try:
        pending = db.get_unclassified_tweets(limit=200)
        for tweet in pending:
            result = ai_classifier.classify_tweet(tweet["text"])
            db.mark_classified(
                tweet["tweet_id"], result["useful"], result["category"], result["reasoning"]
            )
        if pending:
            log.info("Classified %d tweet(s).", len(pending))
    except Exception:
        log.exception("Classification step failed.")

    try:
        to_send = db.get_useful_unsent_tweets(limit=100)
        for tweet in to_send:
            if telegram_notifier.send_alert_tweet(tweet):
                db.mark_sent_to_telegram(tweet["tweet_id"])
        if to_send:
            log.info("Sent %d useful tweet alert(s) to Telegram.", len(to_send))
    except Exception:
        log.exception("Telegram alert step failed.")


def report_job() -> None:
    try:
        reporter.generate_and_send_report()
    except Exception:
        log.exception("Report generation/send failed.")


def main() -> None:
    problems = config.validate()
    if problems:
        log.error("Configuration problems found:")
        for p in problems:
            log.error("  - %s", p)
        log.error("Fix your .env file (see .env.example) and re-run.")
        return

    db.init_db()
    log.info(
        "Tracking accounts=%s keywords=%s | scrape every %dm | report every %dm",
        config.X_TRACK_ACCOUNTS,
        config.X_TRACK_KEYWORDS,
        config.SCRAPE_INTERVAL_MINUTES,
        config.REPORT_INTERVAL_MINUTES,
    )

    # Run once immediately on startup, then on schedule.
    scrape_classify_alert_job()

    schedule.every(config.SCRAPE_INTERVAL_MINUTES).minutes.do(scrape_classify_alert_job)
    schedule.every(config.REPORT_INTERVAL_MINUTES).minutes.do(report_job)

    log.info("Scheduler started. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(5)


if __name__ == "__main__":
    main()
