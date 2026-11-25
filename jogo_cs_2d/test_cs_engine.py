"""Unit tests for the 2D Counter-Strike-style arena engine."""

import random
import unittest

from cs_engine import (
    CS2DEngine,
    ENEMY_COUNT,
    GameConfig,
    InputState,
    MAGAZINE_SIZE,
    PLAYER_SPEED,
    PLAYER_WALK_SPEED,
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

    def test_shift_walk_is_slower_and_silences_player_footsteps(self) -> None:
        # Running without Shift generates steps & alerts nearby bots
        run_engine = CS2DEngine(rng=random.Random(10))
        run_engine.opponents[0].x = run_engine.player_x + 120.0
        run_engine.opponents[0].y = run_engine.player_y
        start_x = run_engine.player_x

        for _ in range(10):
            run_engine.update(0.05, InputState(d=True, shift=False))
        run_dist = run_engine.player_x - start_x
        run_sounds = run_engine.consume_sounds()
        self.assertAlmostEqual(run_dist, PLAYER_SPEED * 0.5, delta=1.0)
        self.assertIn("player_step", run_sounds)
        self.assertIsNotNone(run_engine.opponents[0].investigate_target)

        # Walking with Shift held is slower, silent, and does not alert bots
        walk_engine = CS2DEngine(rng=random.Random(10))
        walk_engine.opponents[0].x = walk_engine.player_x + 120.0
        walk_engine.opponents[0].y = walk_engine.player_y
        walk_engine.opponents[0].investigate_target = None
        w_start_x = walk_engine.player_x

        for _ in range(10):
            walk_engine.update(0.05, InputState(d=True, shift=True))
        walk_dist = walk_engine.player_x - w_start_x
        walk_sounds = walk_engine.consume_sounds()
        self.assertAlmostEqual(walk_dist, PLAYER_WALK_SPEED * 0.5, delta=1.0)
        self.assertLess(walk_dist, run_dist)
        self.assertNotIn("player_step", walk_sounds)
        self.assertIsNone(walk_engine.opponents[0].investigate_target)

    def test_opponents_emit_footsteps_when_moving(self) -> None:
        engine = CS2DEngine(rng=random.Random(11))
        for _ in range(15):
            engine.update(0.05, InputState())
        self.assertTrue(
            any(not r.from_player for r in engine.sound_ripples)
            or any("enemy_step" in s for s in engine.consume_sounds())
        )

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
        # Central warehouse bunker is at x=415..525, y=240..360
        self.assertFalse(engine.has_line_of_sight(380.0, 300.0, 560.0, 300.0))
        self.assertTrue(engine.has_line_of_sight(50.0, 50.0, 200.0, 50.0))

    def test_menu_config_changes_weapon_difficulty_and_opponent_count(self) -> None:
        engine = CS2DEngine(rng=random.Random(6))
        cfg = GameConfig(
            difficulty="hard",
            weapon="smg",
            opponent_count=4,
            show_vision_cone=False,
            show_laser_sight=False,
            enable_sound=False,
        )
        engine.apply_config(cfg, reset_match=True)
        self.assertEqual(len(engine.opponents), 4)
        self.assertEqual(engine.ammo, WEAPONS["smg"].magazine_size)
        self.assertEqual(engine.difficulty_spec.label, "Difícil")
        self.assertFalse(engine.config.show_vision_cone)
        self.assertFalse(engine.config.enable_sound)


if __name__ == "__main__":
    unittest.main()
