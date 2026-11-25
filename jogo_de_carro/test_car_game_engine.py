"""Unit tests for the 3-lane, 10-level Car Dodge game engine."""

import random
import unittest

from car_game_engine import (
    CAR_HEIGHT,
    CAR_STYLES,
    CARS_PER_LEVEL,
    CarGameEngine,
    LANE_COUNT,
    LEVEL_COLOR_POOLS,
    SPEED_LEVELS,
    TrafficCar,
)


class TestSpeedLevels(unittest.TestCase):
    def test_ten_strictly_increasing_playable_levels_starting_at_380(self) -> None:
        self.assertEqual(len(SPEED_LEVELS), 10)
        self.assertEqual(len(LEVEL_COLOR_POOLS), 10)
        self.assertEqual(SPEED_LEVELS[0].speed_px_per_sec, 380.0)

        speeds = [lvl.speed_px_per_sec for lvl in SPEED_LEVELS]
        self.assertEqual(speeds, sorted(speeds))
        self.assertEqual(len(set(speeds)), 10)
        for lvl in SPEED_LEVELS:
            self.assertLess(lvl.max_simultaneous_in_band, LANE_COUNT)
            self.assertGreaterEqual(lvl.min_vertical_gap_px, CAR_HEIGHT * 2.0)


class TestCarGameEngine(unittest.TestCase):
    def test_lane_movement_bounds(self) -> None:
        engine = CarGameEngine(rng=random.Random(1))
        self.assertEqual(engine.player_lane, 1)

        self.assertTrue(engine.move_left())
        self.assertEqual(engine.player_lane, 0)
        self.assertFalse(engine.move_left())
        self.assertEqual(engine.player_lane, 0)

        self.assertTrue(engine.move_right())
        self.assertTrue(engine.move_right())
        self.assertEqual(engine.player_lane, 2)
        self.assertFalse(engine.move_right())
        self.assertEqual(engine.player_lane, 2)

    def test_collision_triggers_game_over(self) -> None:
        engine = CarGameEngine(rng=random.Random(2))
        engine.traffic.append(
            TrafficCar(
                car_id=1,
                lane=engine.player_lane,
                y=engine.player_y,
                color="#ef4444",
            )
        )
        engine.update(0.016)
        self.assertTrue(engine.game_over)

    def test_dodge_awards_points_and_mutates_cars_on_level_up(self) -> None:
        engine = CarGameEngine(starting_level=1, rng=random.Random(3))
        active_car = TrafficCar(
            car_id=99,
            lane=2,
            y=120.0,
            color="#000000",
            style="unknown",
        )
        engine.traffic.append(active_car)
        for i in range(CARS_PER_LEVEL):
            engine.traffic.append(
                TrafficCar(
                    car_id=i + 1,
                    lane=0,
                    y=600.0,
                    color="#ef4444",
                )
            )
        engine.update(0.1)
        self.assertEqual(engine.dodged, CARS_PER_LEVEL)
        self.assertGreater(engine.score, 0)
        self.assertEqual(engine.level, 2)
        self.assertIn(active_car.color, LEVEL_COLOR_POOLS[1])
        self.assertIn(active_car.style, CAR_STYLES)

    def test_dynamic_cars_change_and_never_block_all_three_lanes(self) -> None:
        for lv in range(1, 11):
            engine = CarGameEngine(starting_level=lv, rng=random.Random(42 + lv))
            for _ in range(300):
                engine.update(0.05)
                if engine.game_over:
                    engine.reset(starting_level=lv)
                for car in engine.traffic:
                    band_lanes = {
                        other.lane
                        for other in engine.traffic
                        if abs(other.y - car.y) < CAR_HEIGHT * 1.4
                    }
                    self.assertLess(len(band_lanes), LANE_COUNT)


if __name__ == "__main__":
    unittest.main()
