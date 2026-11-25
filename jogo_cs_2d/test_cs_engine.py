"""Unit tests for the 2D Counter-Strike-style arena engine."""

import random
import unittest

from cs_engine import (
    CS2DEngine,
    ENEMY_COUNT,
    GameConfig,
    InputState,
    MAGAZINE_SIZE,
    RELOAD_DURATION_SEC,
    WEAPONS,
)


class TestCS2DEngine(unittest.TestCase):
    def test_starts_with_exactly_two_opponents_and_full_magazine(self) -> None:
        engine = CS2DEngine(rng=random.Random(1))
        self.assertEqual(len(engine.opponents), ENEMY_COUNT)
        self.assertEqual(engine.alive_opponents, 2)
        self.assertEqual(engine.ammo, MAGAZINE_SIZE)

    def test_wasd_movement_and_mouse_aim(self) -> None:
        engine = CS2DEngine(rng=random.Random(2))
        x0, y0 = engine.player_x, engine.player_y

        engine.update(
            0.1,
            InputState(w=True, d=True, mouse_x=x0 + 100.0, mouse_y=y0),
        )
        self.assertGreater(engine.player_x, x0)
        self.assertLess(engine.player_y, y0)
        self.assertAlmostEqual(engine.player_angle, 0.0, places=4)

    def test_shooting_consumes_ammo_and_r_reloads(self) -> None:
        engine = CS2DEngine(rng=random.Random(3))
        engine.update(
            0.05,
            InputState(mouse_x=engine.player_x + 50.0, mouse_y=engine.player_y, firing=True),
        )
        self.assertEqual(engine.ammo, MAGAZINE_SIZE - 1)
        self.assertEqual(len(engine.bullets), 1)

        engine.update(0.01, InputState(reload_pressed=True))
        self.assertTrue(engine.is_reloading)

        steps = int(RELOAD_DURATION_SEC / 0.1) + 2
        for _ in range(steps):
            engine.update(0.1, InputState())
        self.assertFalse(engine.is_reloading)
        self.assertEqual(engine.ammo, MAGAZINE_SIZE)

    def test_eliminating_both_opponents_wins_round(self) -> None:
        engine = CS2DEngine(rng=random.Random(4))
        for bot in engine.opponents:
            bot.hp = 10
            bot.x = engine.player_x + 40.0
            bot.y = engine.player_y
            engine.fire_cooldown = 0.0
            engine.update(
                0.01,
                InputState(mouse_x=bot.x, mouse_y=bot.y, firing=True),
            )
            engine.update(0.06, InputState())

        self.assertTrue(engine.round_over)
        self.assertTrue(engine.round_won)
        self.assertEqual(engine.wins, 1)

    def test_walls_block_line_of_sight(self) -> None:
        engine = CS2DEngine(rng=random.Random(5))
        self.assertFalse(engine.has_line_of_sight(300.0, 270.0, 460.0, 270.0))
        self.assertTrue(engine.has_line_of_sight(50.0, 50.0, 200.0, 50.0))

    def test_menu_config_changes_weapon_difficulty_and_opponent_count(self) -> None:
        engine = CS2DEngine(rng=random.Random(6))
        cfg = GameConfig(
            difficulty="hard",
            weapon="smg",
            opponent_count=4,
            show_vision_cone=False,
            show_laser_sight=False,
        )
        engine.apply_config(cfg, reset_match=True)
        self.assertEqual(len(engine.opponents), 4)
        self.assertEqual(engine.ammo, WEAPONS["smg"].magazine_size)
        self.assertEqual(engine.difficulty_spec.label, "Difícil")
        self.assertFalse(engine.config.show_vision_cone)


if __name__ == "__main__":
    unittest.main()
