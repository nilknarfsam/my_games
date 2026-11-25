"""Unit tests for the stopwatch timing engine."""

import unittest

from stopwatch_engine import StopwatchEngine, format_time


class FakeClock:
    def __init__(self, initial: float = 0.0) -> None:
        self.now = initial

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class TestFormatTime(unittest.TestCase):
    def test_zero_and_negative_values(self) -> None:
        self.assertEqual(format_time(0.0), "00:00:00.00")
        self.assertEqual(format_time(-5.25), "00:00:00.00")

    def test_hours_minutes_seconds_centiseconds(self) -> None:
        # 1h 02m 03.45s = 3723.45s
        self.assertEqual(format_time(3723.45), "01:02:03.45")
        self.assertEqual(format_time(1.14), "00:00:01.14")


class TestStopwatchEngine(unittest.TestCase):
    def test_initial_state(self) -> None:
        engine = StopwatchEngine(clock=FakeClock(100.0))
        self.assertFalse(engine.is_running)
        self.assertEqual(engine.elapsed_seconds(), 0.0)
        self.assertEqual(engine.laps, ())

    def test_start_pause_resume_and_reset(self) -> None:
        clock = FakeClock(10.0)
        engine = StopwatchEngine(clock=clock)

        engine.start()
        self.assertTrue(engine.is_running)
        clock.advance(2.5)
        self.assertAlmostEqual(engine.elapsed_seconds(), 2.5)

        engine.pause()
        self.assertFalse(engine.is_running)
        clock.advance(5.0)
        self.assertAlmostEqual(engine.elapsed_seconds(), 2.5)

        engine.start()
        clock.advance(1.25)
        self.assertAlmostEqual(engine.elapsed_seconds(), 3.75)

        engine.reset()
        self.assertFalse(engine.is_running)
        self.assertAlmostEqual(engine.elapsed_seconds(), 0.0)
        self.assertEqual(engine.laps, ())

    def test_laps_compute_splits_and_totals(self) -> None:
        clock = FakeClock(0.0)
        engine = StopwatchEngine(clock=clock)

        with self.assertRaises(RuntimeError):
            engine.lap()

        engine.start()
        clock.advance(1.5)
        lap1 = engine.lap()
        self.assertEqual(lap1.index, 1)
        self.assertAlmostEqual(lap1.lap_seconds, 1.5)
        self.assertAlmostEqual(lap1.total_seconds, 1.5)

        clock.advance(2.25)
        lap2 = engine.lap()
        self.assertEqual(lap2.index, 2)
        self.assertAlmostEqual(lap2.lap_seconds, 2.25)
        self.assertAlmostEqual(lap2.total_seconds, 3.75)
        self.assertEqual(len(engine.laps), 2)


if __name__ == "__main__":
    unittest.main()
