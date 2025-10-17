import time
from datetime import datetime
from types import TracebackType
from zoneinfo import ZoneInfo


def get_utc_now() -> datetime:
    """Get the current UTC time.

    Returns
    -------
        datetime: Current UTC time.

    """
    return datetime.now(tz=ZoneInfo("UTC"))


class Stopwatch:
    """A simple stopwatch to measure elapsed time and laps in nanoseconds.

    Precision: +/- 500ns
    """

    MICRO = 1_000
    MILLI = MICRO * 1_000
    SECOND = MILLI * 1_000

    def __init__(self) -> None:
        self._start_at = 0
        self._end_at = 0

    @property
    def elapsed_ns(self) -> int:
        return self._end_at - self._start_at

    @property
    def elapsed_ms(self) -> float:
        return self.elapsed_ns / self.MILLI

    @property
    def elapsed_sec(self) -> float:
        return self.elapsed_ns / self.SECOND

    async def __aenter__(self) -> None:
        self._start_at = time.monotonic_ns()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self._end_at = time.monotonic_ns()
