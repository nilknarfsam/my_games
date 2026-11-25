"""Pure timing engine for the stopwatch application."""

from dataclasses import dataclass
from time import perf_counter
from typing import Callable


@dataclass(frozen=True)
class LapRecord:
    """Represents a single recorded lap."""

    index: int
    lap_seconds: float
    total_seconds: float


def format_time(seconds: float) -> str:
    """Format elapsed seconds as HH:MM:SS.cc (centiseconds)."""
    clamped = max(0.0, seconds)
    # Epsilon prevents binary float imprecision (e.g. 1.14 * 100 -> 113.99999999999999)
    total_centiseconds = int(clamped * 100 + 1e-9)
    centiseconds = total_centiseconds % 100
    total_seconds = total_centiseconds // 100
    secs = total_seconds % 60
    total_minutes = total_seconds // 60
    minutes = total_minutes % 60
    hours = total_minutes // 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"


class StopwatchEngine:
    """High-precision stopwatch state machine using a monotonic clock."""

    def __init__(self, clock: Callable[[], float] = perf_counter) -> None:
        self._clock = clock
        self._running = False
        self._start_timestamp = 0.0
        self._accumulated = 0.0
        self._last_lap_total = 0.0
        self._laps: list[LapRecord] = []

    @property
    def is_running(self) -> bool:
        """Return True when the stopwatch is actively counting."""
        return self._running

    @property
    def laps(self) -> tuple[LapRecord, ...]:
        """Return recorded laps in chronological order."""
        return tuple(self._laps)

    def elapsed_seconds(self) -> float:
        """Return total elapsed time in seconds."""
        if not self._running:
            return self._accumulated
        return self._accumulated + max(0.0, self._clock() - self._start_timestamp)

    def start(self) -> None:
        """Start or resume counting."""
        if self._running:
            return
        self._start_timestamp = self._clock()
        self._running = True

    def pause(self) -> None:
        """Pause counting and preserve accumulated time."""
        if not self._running:
            return
        self._accumulated = self.elapsed_seconds()
        self._running = False

    def toggle(self) -> bool:
        """Toggle between running and paused; returns the new running state."""
        if self._running:
            self.pause()
        else:
            self.start()
        return self._running

    def reset(self) -> None:
        """Stop the stopwatch and clear elapsed time and laps."""
        self._running = False
        self._start_timestamp = 0.0
        self._accumulated = 0.0
        self._last_lap_total = 0.0
        self._laps.clear()

    def lap(self) -> LapRecord:
        """Record a new lap and return it. Raises RuntimeError if not started."""
        total = self.elapsed_seconds()
        if not self._running and total == 0.0:
            raise RuntimeError("Não é possível registrar volta com o cronômetro zerado.")
        split = max(0.0, total - self._last_lap_total)
        self._last_lap_total = total
        record = LapRecord(
            index=len(self._laps) + 1,
            lap_seconds=split,
            total_seconds=total,
        )
        self._laps.append(record)
        return record
