"""Pure simulation engine for the Snake (Jogo da Cobrinha) game."""

from collections import deque
from dataclasses import dataclass, field
import random


GRID_WIDTH = 28
GRID_HEIGHT = 24

Point = tuple[int, int]

UP: Point = (0, -1)
DOWN: Point = (0, 1)
LEFT: Point = (-1, 0)
RIGHT: Point = (1, 0)

ALL_DIRECTIONS: tuple[Point, ...] = (UP, DOWN, LEFT, RIGHT)


def is_opposite(d1: Point, d2: Point) -> bool:
    return d1[0] + d2[0] == 0 and d1[1] + d2[1] == 0


@dataclass
class RivalSnake:
    """An AI-controlled rival snake roaming the field."""

    snake_id: int
    body: deque[Point]
    direction: Point
    color_head: str
    color_body: str
    grow_pending: int = 0
    respawn_ticks: int = 0


@dataclass
class FoodItem:
    """Food on the grid that grows the player snake."""

    pos: Point
    is_bonus: bool = False


class SnakeGameEngine:
    """Grid-based Snake engine with obstacles and rival snakes."""

    def __init__(
        self,
        obstacle_count: int = 14,
        rival_count: int = 2,
        rng: random.Random | None = None,
    ) -> None:
        self._rng = rng or random.Random()
        self._obstacle_count = obstacle_count
        self._rival_count = rival_count

        self.player_body: deque[Point] = deque()
        self.direction: Point = RIGHT
        self._turn_queue: deque[Point] = deque(maxlen=2)
        self._grow_pending = 0

        self.obstacles: set[Point] = set()
        self.rivals: list[RivalSnake] = []
        self.food = FoodItem((0, 0), False)

        self.score = 0
        self.high_score = 0
        self.foods_eaten = 0
        self.ticks = 0
        self.game_over = False
        self.death_reason = ""
        self.paused = False

        self.reset()

    @property
    def player_head(self) -> Point:
        return self.player_body[0]

    @property
    def tick_interval_ms(self) -> int:
        """Speed up gently as the player eats more food, staying playable."""
        return max(75, 135 - (self.foods_eaten * 2))

    def reset(self) -> None:
        """Reset board, obstacles, rival snakes, and player."""
        cx = GRID_WIDTH // 4
        cy = GRID_HEIGHT // 2
        self.player_body = deque([(cx, cy), (cx - 1, cy), (cx - 2, cy)])
        self.direction = RIGHT
        self._turn_queue.clear()
        self._grow_pending = 0

        self.score = 0
        self.foods_eaten = 0
        self.ticks = 0
        self.game_over = False
        self.death_reason = ""
        self.paused = False

        self.obstacles.clear()
        self.rivals.clear()

        self._generate_obstacles()
        self._spawn_rivals()
        self._spawn_food()

    def toggle_pause(self) -> bool:
        if self.game_over:
            return False
        self.paused = not self.paused
        return self.paused

    def queue_direction(self, new_dir: Point) -> bool:
        """Buffer a turn, rejecting 180-degree self-reversals."""
        if new_dir not in ALL_DIRECTIONS:
            return False
        reference = self._turn_queue[-1] if self._turn_queue else self.direction
        if new_dir == reference or is_opposite(new_dir, reference):
            return False
        if len(self._turn_queue) < 2:
            self._turn_queue.append(new_dir)
            return True
        return False

    def step(self) -> None:
        """Advance simulation by one grid tick."""
        if self.game_over or self.paused:
            return

        self.ticks += 1
        if self._turn_queue:
            self.direction = self._turn_queue.popleft()

        hx, hy = self.player_head
        next_head = (hx + self.direction[0], hy + self.direction[1])

        # Check wall and obstacle collisions
        if not self._in_bounds(next_head):
            self._trigger_game_over("Bateu na parede!")
            return
        if next_head in self.obstacles:
            self._trigger_game_over("Bateu em um objeto na pista!")
            return

        # Check self-collision (tail is safe if not growing)
        body_to_check = (
            list(self.player_body)
            if self._grow_pending > 0
            else list(self.player_body)[:-1]
        )
        if next_head in body_to_check:
            self._trigger_game_over("Bateu no próprio corpo!")
            return

        # Check collision with rival snakes before moving
        for rival in self.rivals:
            if rival.respawn_ticks == 0 and next_head in rival.body:
                self._trigger_game_over("Bateu em outra cobra!")
                return

        # Move player snake
        self.player_body.appendleft(next_head)
        if next_head == self.food.pos:
            growth = 2 if self.food.is_bonus else 1
            points = 30 if self.food.is_bonus else 10
            self._grow_pending += growth
            self.foods_eaten += 1
            self.score += points
            if self.score > self.high_score:
                self.high_score = self.score
            self._spawn_food()

        if self._grow_pending > 0:
            self._grow_pending -= 1
        else:
            self.player_body.pop()

        # Move rival snakes on the field
        self._step_rivals()

    def _trigger_game_over(self, reason: str) -> None:
        self.game_over = True
        self.death_reason = reason

    @staticmethod
    def _in_bounds(pos: Point) -> bool:
        return 0 <= pos[0] < GRID_WIDTH and 0 <= pos[1] < GRID_HEIGHT

    def _occupied_cells(self) -> set[Point]:
        occupied = set(self.obstacles)
        occupied.update(self.player_body)
        for rival in self.rivals:
            if rival.respawn_ticks == 0:
                occupied.update(rival.body)
        return occupied

    def _generate_obstacles(self) -> None:
        """Place solid objects safely away from player's starting path."""
        cx, cy = self.player_head
        safe_zone = {
            (x, y)
            for x in range(max(0, cx - 4), min(GRID_WIDTH, cx + 7))
            for y in range(max(0, cy - 2), min(GRID_HEIGHT, cy + 3))
        }

        candidates = [
            (x, y)
            for x in range(1, GRID_WIDTH - 1)
            for y in range(1, GRID_HEIGHT - 1)
            if (x, y) not in safe_zone
        ]
        self._rng.shuffle(candidates)

        for pos in candidates:
            if len(self.obstacles) >= self._obstacle_count:
                break
            # Avoid clustering obstacles directly adjacent horizontally/vertically
            neighbors = (
                (pos[0] + 1, pos[1]),
                (pos[0] - 1, pos[1]),
                (pos[0], pos[1] + 1),
                (pos[0], pos[1] - 1),
            )
            if any(nb in self.obstacles for nb in neighbors):
                continue
            self.obstacles.add(pos)

    def _spawn_rivals(self) -> None:
        palettes = (
            ("#f59e0b", "#d97706"),
            ("#a855f7", "#7e22ce"),
            ("#ec4899", "#be185d"),
        )
        for idx in range(self._rival_count):
            head_c, body_c = palettes[idx % len(palettes)]
            rival = RivalSnake(
                snake_id=idx + 1,
                body=deque(),
                direction=LEFT,
                color_head=head_c,
                color_body=body_c,
            )
            self._place_rival(rival)
            self.rivals.append(rival)

    def _place_rival(self, rival: RivalSnake) -> None:
        """Find a free 3-cell horizontal/vertical spot away from the player head."""
        occupied = self._occupied_cells()
        px, py = self.player_head
        attempts = 120
        for _ in range(attempts):
            d = self._rng.choice(ALL_DIRECTIONS)
            hx = self._rng.randint(3, GRID_WIDTH - 4)
            hy = self._rng.randint(3, GRID_HEIGHT - 4)
            if abs(hx - px) + abs(hy - py) < 7:
                continue
            cells = [
                (hx, hy),
                (hx - d[0], hy - d[1]),
                (hx - d[0] * 2, hy - d[1] * 2),
            ]
            if all(self._in_bounds(c) and c not in occupied for c in cells):
                rival.body = deque(cells)
                rival.direction = d
                rival.grow_pending = 0
                rival.respawn_ticks = 0
                return

        # Fallback: delay respawn if board is very full
        rival.body.clear()
        rival.respawn_ticks = 6

    def _step_rivals(self) -> None:
        # Move rival snakes slightly slower or at grid pace; move every 2 ticks?
        # Moving every tick makes them feel alive, or every tick while avoiding player!
        for rival in self.rivals:
            if rival.respawn_ticks > 0:
                rival.respawn_ticks -= 1
                if rival.respawn_ticks == 0:
                    self._place_rival(rival)
                continue

            next_dir = self._choose_rival_direction(rival)
            if next_dir is None:
                # Cornered rival disappears briefly and respawns elsewhere
                rival.body.clear()
                rival.respawn_ticks = 8
                continue

            rival.direction = next_dir
            rhx, rhy = rival.body[0]
            next_pos = (rhx + next_dir[0], rhy + next_dir[1])

            # If a rival steps directly into the player's head, player loses
            if next_pos == self.player_head:
                self._trigger_game_over("Colisão frontal com outra cobra!")
                return

            rival.body.appendleft(next_pos)
            if next_pos == self.food.pos:
                rival.grow_pending += 1
                self._spawn_food()

            if rival.grow_pending > 0:
                rival.grow_pending -= 1
            else:
                rival.body.pop()

    def _choose_rival_direction(self, rival: RivalSnake) -> Point | None:
        """Pick a valid move for a rival snake, preferring straight or food."""
        blocked = set(self.obstacles)
        blocked.update(self.player_body)
        # Don't ram straight into player head unfairly; avoid player head cell
        blocked.add(self.player_head)
        for other in self.rivals:
            if other.respawn_ticks > 0:
                continue
            if other.snake_id == rival.snake_id:
                blocked.update(list(other.body)[:-1])
            else:
                blocked.update(other.body)

        rhx, rhy = rival.body[0]
        valid: list[Point] = []
        for d in ALL_DIRECTIONS:
            if is_opposite(d, rival.direction):
                continue
            nx, ny = rhx + d[0], rhy + d[1]
            if self._in_bounds((nx, ny)) and (nx, ny) not in blocked:
                valid.append(d)

        if not valid:
            return None

        # Slight preference to keep going straight (70%) so movement looks natural
        if rival.direction in valid and self._rng.random() < 0.70:
            return rival.direction
        return self._rng.choice(valid)

    def _spawn_food(self) -> None:
        occupied = self._occupied_cells()
        free = [
            (x, y)
            for x in range(GRID_WIDTH)
            for y in range(GRID_HEIGHT)
            if (x, y) not in occupied
        ]
        if not free:
            return
        pos = self._rng.choice(free)
        is_bonus = self.foods_eaten > 0 and (self.foods_eaten % 5 == 0)
        self.food = FoodItem(pos=pos, is_bonus=is_bonus)
