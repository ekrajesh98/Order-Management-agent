from datetime import datetime
from zoneinfo import ZoneInfo


def get_utc_now() -> datetime:
    """Get the current UTC time.

    Returns
    -------
        datetime: Current UTC time.

    """
    return datetime.now(tz=ZoneInfo("UTC"))
