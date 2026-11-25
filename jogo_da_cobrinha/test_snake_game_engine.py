"""Unit tests for the Jogo da Cobrinha game engine."""

from collections import deque
import random
import unittest

from snake_game_engine import (
    DOWN,
    FoodItem,
    GRID_HEIGHT,
    GRID_WIDTH,
    LEFT,
    RIGHT,
    RivalSnake,
    SnakeGameEngine,
    UP,
)


class TestSnakeGameEngine(unittest.TestCase):
    def test_initial_setup_has_obstacles_and_rivals(self) -> None:
        engine = SnakeGameEngine(obstacle_count=12, rival_count=2, rng=random.Random(1))
        self.assertEqual(len(engine.player_body), 3)
        self.assertEqual(len(engine.obstacles), 12)
        self.assertEqual(len(engine.rivals), 2)
        self.assertFalse(engine.game_over)
        self.assertNotIn(engine.food.pos, engine.obstacles)

    def test_eating_food_grows_snake_and_scores(self) -> None:
        engine = SnakeGameEngine(obstacle_count=0, rival_count=0, rng=random.Random(2))
        initial_len = len(engine.player_body)
        hx, hy = engine.player_head
        engine.food = FoodItem(pos=(hx + 1, hy), is_bonus=False)

        engine.step()
        self.assertEqual(len(engine.player_body), initial_len + 1)
        self.assertEqual(engine.score, 10)
        self.assertEqual(engine.foods_eaten, 1)

    def test_prevents_reverse_turn_and_buffers_rapid_turns(self) -> None:
        engine = SnakeGameEngine(obstacle_count=0, rival_count=0, rng=random.Random(3))
        self.assertFalse(engine.queue_direction(LEFT))
        self.assertTrue(engine.queue_direction(UP))
        self.assertTrue(engine.queue_direction(LEFT))

        engine.step()
        self.assertEqual(engine.direction, UP)
        engine.step()
        self.assertEqual(engine.direction, LEFT)

    def test_obstacle_collision_triggers_game_over(self) -> None:
        engine = SnakeGameEngine(obstacle_count=0, rival_count=0, rng=random.Random(4))
        hx, hy = engine.player_head
        engine.obstacles.add((hx + 1, hy))

        engine.step()
        self.assertTrue(engine.game_over)
        self.assertIn("objeto", engine.death_reason.lower())

    def test_rival_snake_collision_triggers_game_over(self) -> None:
        engine = SnakeGameEngine(obstacle_count=0, rival_count=0, rng=random.Random(5))
        hx, hy = engine.player_head
        engine.rivals.append(
            RivalSnake(
                snake_id=1,
                body=deque([(hx + 1, hy), (hx + 2, hy), (hx + 3, hy)]),
                direction=DOWN,
                color_head="#f59e0b",
                color_body="#d97706",
            )
        )
        engine.step()
        self.assertTrue(engine.game_over)
        self.assertIn("cobra", engine.death_reason.lower())

    def test_wall_collision_triggers_game_over(self) -> None:
        engine = SnakeGameEngine(obstacle_count=0, rival_count=0, rng=random.Random(6))
        engine.player_body = deque([(GRID_WIDTH - 1, GRID_HEIGHT // 2), (GRID_WIDTH - 2, GRID_HEIGHT // 2), (GRID_WIDTH - 3, GRID_HEIGHT // 2)])
        engine.direction = RIGHT
        engine.step()
        self.assertTrue(engine.game_over)


if __name__ == "__main__":
    unittest.main()
