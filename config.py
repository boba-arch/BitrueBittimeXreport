"""Central configuration, loaded from environment variables / .env file."""
import os
from dotenv import load_dotenv

load_dotenv()


def _split_csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


# --- X (Twitter) API ---
X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN", "")

# --- Anthropic API ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_CLASSIFY_MODEL = os.getenv("ANTHROPIC_CLASSIFY_MODEL", "claude-haiku-4-5-20251001")
ANTHROPIC_REPORT_MODEL = os.getenv("ANTHROPIC_REPORT_MODEL", "claude-sonnet-5")

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ALERT_CHAT_ID = os.getenv("TELEGRAM_ALERT_CHAT_ID", "")
TELEGRAM_REPORT_CHAT_ID = os.getenv("TELEGRAM_REPORT_CHAT_ID", "") or TELEGRAM_ALERT_CHAT_ID

# --- Monitoring targets ---
X_TRACK_ACCOUNTS = _split_csv(os.getenv("X_TRACK_ACCOUNTS", "BitrueOfficial,bittimeexchange"))
X_TRACK_KEYWORDS = _split_csv(os.getenv("X_TRACK_KEYWORDS", "Bitrue,Bittime"))

# --- Timing ---
SCRAPE_INTERVAL_MINUTES = int(os.getenv("SCRAPE_INTERVAL_MINUTES", "5"))
REPORT_INTERVAL_MINUTES = int(os.getenv("REPORT_INTERVAL_MINUTES", "60"))

# --- Misc ---
DB_PATH = os.getenv("DB_PATH", "data/tweets.db")
REPORTS_DIR = os.getenv("REPORTS_DIR", "reports")
DEBUG = os.getenv("DEBUG", "0") == "1"


def build_search_query() -> str:
    """Build the X API v2 recent-search query string.

    Matches mentions of any tracked account (@handle) OR any tracked keyword,
    and excludes retweets (pure reposts add noise without new text).
    """
    account_terms = [f"@{acct}" for acct in X_TRACK_ACCOUNTS]
    keyword_terms = [f'"{kw}"' for kw in X_TRACK_KEYWORDS]
    all_terms = account_terms + keyword_terms
    return f"({' OR '.join(all_terms)}) -is:retweet"


def validate() -> list[str]:
    """Return a list of human-readable problems with the current config."""
    problems = []
    if not X_BEARER_TOKEN:
        problems.append("X_BEARER_TOKEN is not set")
    if not ANTHROPIC_API_KEY:
        problems.append("ANTHROPIC_API_KEY is not set")
    if not TELEGRAM_BOT_TOKEN:
        problems.append("TELEGRAM_BOT_TOKEN is not set")
    if not TELEGRAM_ALERT_CHAT_ID:
        problems.append("TELEGRAM_ALERT_CHAT_ID is not set")
    if not X_TRACK_ACCOUNTS and not X_TRACK_KEYWORDS:
        problems.append("No accounts or keywords configured to track")
    return problems
