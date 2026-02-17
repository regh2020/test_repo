from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATABASE_PATH = DATA_DIR / "academic_events.db"

USER_AGENT = "AcademicEventsRegistry/0.1 (research-tool)"
FETCH_TIMEOUT_SECONDS = 30
MAX_FETCH_RETRIES = 3

DEFAULT_REFRESH_INTERVAL_HOURS = 24
