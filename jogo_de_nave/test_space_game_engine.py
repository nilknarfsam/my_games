"""Unit tests for the Jogo de Nave simulation engine."""

import random
import unittest

from space_game_engine import (
    ARENA_HEIGHT,
    ARENA_WIDTH,
    INITIAL_LIVES,
    InputState,
    KILLS_PER_SHOT_LEVEL,
    MAX_SHOT_LEVEL,
    SPECIAL_BONUS_LIMIT_SEC,
    SpaceGameEngine,
)


class TestSpaceGameEngine(unittest.TestCase):
    def test_initial_state_has_three_lives_and_shot_level_one(self) -> None:
        engine = SpaceGameEngine(rng=random.Random(1))
        self.assertEqual(engine.lives, INITIAL_LIVES)
        self.assertEqual(engine.shot_level, 1)
        self.assertFalse(engine.game_over)

    def test_four_direction_movement_stays_in_arena(self) -> None:
        engine = SpaceGameEngine(rng=random.Random(2))
        start_x, start_y = engine.player_x, engine.player_y

        engine.update(0.1, InputState(up=True, left=True))
        self.assertLess(engine.player_x, start_x)
        self.assertLess(engine.player_y, start_y)

        # Push far beyond boundaries and ensure clamping
        for _ in range(40):
            engine.update(0.1, InputState(down=True, right=True))
        self.assertLess(engine.player_x, ARENA_WIDTH)
        self.assertLess(engine.player_y, ARENA_HEIGHT)

    def test_shot_levels_upgrade_without_dying_and_reset_on_hit(self) -> None:
        engine = SpaceGameEngine(rng=random.Random(3))
        for _ in range(KILLS_PER_SHOT_LEVEL):
            e = engine._spawn_enemy(kind="scout")
            engine._award_kill(e)
        self.assertEqual(engine.shot_level, 2)

        for _ in range(KILLS_PER_SHOT_LEVEL):
            e = engine._spawn_enemy(kind="scout")
            engine._award_kill(e)
        self.assertEqual(engine.shot_level, MAX_SHOT_LEVEL)

        # Taking damage drops 1 heart and resets shot level to 1
        engine._damage_player()
        self.assertEqual(engine.lives, INITIAL_LIVES - 1)
        self.assertEqual(engine.shot_level, 1)

    def test_special_weapon_and_bomb_have_twenty_second_limit(self) -> None:
        engine = SpaceGameEngine(rng=random.Random(4))
        engine.spawn_timer = 999.0
        engine.bonus_spawn_timer = 999.0
        engine.spawn_bonus(kind="special_weapon", x=engine.player_x)
        engine.bonuses[0].y = engine.player_y
        engine.update(0.016, InputState())

        self.assertTrue(engine.special_weapon_active)
        self.assertAlmostEqual(
            engine.special_weapon_timer, SPECIAL_BONUS_LIMIT_SEC, delta=0.1
        )

        # Advance past 20s -> expires
        for _ in range(205):
            engine.update(0.1, InputState())
        self.assertFalse(engine.special_weapon_active)

        # Bomb pickup + 20s expiration
        engine.spawn_bonus(kind="bomb", x=engine.player_x)
        engine.bonuses[0].y = engine.player_y
        engine.update(0.016, InputState())
        self.assertTrue(engine.has_bomb)
        self.assertAlmostEqual(engine.bomb_timer, SPECIAL_BONUS_LIMIT_SEC, delta=0.1)

        for _ in range(205):
            engine.update(0.1, InputState())
        self.assertFalse(engine.has_bomb)

    def test_bomb_detonation_destroys_enemies(self) -> None:
        engine = SpaceGameEngine(rng=random.Random(5))
        engine.has_bomb = True
        engine.bomb_timer = SPECIAL_BONUS_LIMIT_SEC
        engine._spawn_enemy(kind="scout")
        engine._spawn_enemy(kind="maluca")
        destroyed = engine.detonate_bomb()
        self.assertEqual(destroyed, 2)
        self.assertFalse(engine.has_bomb)
        self.assertEqual(len(engine.enemies), 0)

    def test_maluca_ship_moves_erratically(self) -> None:
        engine = SpaceGameEngine(rng=random.Random(6))
        maluca = engine._spawn_enemy(kind="maluca")
        maluca.y = 120.0
        positions = []
        for _ in range(25):
            engine.update(0.05, InputState())
            positions.append(maluca.x)
        self.assertGreater(max(positions) - min(positions), 20.0)


if __name__ == "__main__":
    unittest.main()
