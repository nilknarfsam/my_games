"""Pure game logic for the 3-lane Car Dodge (Jogo de Carro) game."""

from dataclasses import dataclass
import random


LANE_COUNT = 3
ROAD_WIDTH = 330.0
ROAD_HEIGHT = 560.0
LANE_WIDTH = ROAD_WIDTH / LANE_COUNT

CAR_WIDTH = 46.0
CAR_HEIGHT = 82.0
PLAYER_Y = ROAD_HEIGHT - CAR_HEIGHT - 24.0
HITBOX_INSET_X = 5.0
HITBOX_INSET_Y = 6.0


@dataclass(frozen=True)
class SpeedLevel:
    """Configuration for one of the 10 playable speed levels."""

    level: int
    name: str
    speed_px_per_sec: float
    spawn_interval_sec: float
    min_vertical_gap_px: float
    max_simultaneous_in_band: int
    lane_change_chance: float


# Level 1 starts at the previous Level 3 ("Rodovia", 380 px/s) and scales to Level 10.
SPEED_LEVELS: tuple[SpeedLevel, ...] = (
    SpeedLevel(1, "Rodovia", 380.0, 0.82, 195.0, 2, 0.15),
    SpeedLevel(2, "Expresso", 415.0, 0.76, 190.0, 2, 0.22),
    SpeedLevel(3, "Turbo", 450.0, 0.70, 186.0, 2, 0.28),
    SpeedLevel(4, "Esportivo", 485.0, 0.65, 182.0, 2, 0.34),
    SpeedLevel(5, "Fórmula", 520.0, 0.60, 178.0, 2, 0.40),
    SpeedLevel(6, "Supersônico", 555.0, 0.56, 175.0, 2, 0.46),
    SpeedLevel(7, "Hiper", 590.0, 0.52, 172.0, 2, 0.52),
    SpeedLevel(8, "Relâmpago", 625.0, 0.48, 170.0, 2, 0.58),
    SpeedLevel(9, "Extremo", 660.0, 0.45, 168.0, 2, 0.64),
    SpeedLevel(10, "Lenda", 695.0, 0.42, 166.0, 2, 0.70),
)

CARS_PER_LEVEL = 10

CAR_STYLES: tuple[str, ...] = (
    "sedan",
    "esportivo",
    "pickup",
    "van",
    "taxi",
)

# Distinct color pools per level so traffic visuals shift as levels change.
LEVEL_COLOR_POOLS: tuple[tuple[str, ...], ...] = (
    ("#ef4444", "#f59e0b", "#10b981", "#a855f7", "#ec4899"),
    ("#f97316", "#eab308", "#22c55e", "#06b6d4", "#e11d48"),
    ("#fb7185", "#facc15", "#34d399", "#818cf8", "#f472b6"),
    ("#dc2626", "#d97706", "#059669", "#7c3aed", "#db2777"),
    ("#f43f5e", "#fb923c", "#4ade80", "#c084fc", "#2dd4bf"),
    ("#e11d48", "#fbbf24", "#14b8a6", "#6366f1", "#ec4899"),
    ("#ef4444", "#a3e635", "#22d3ee", "#e879f9", "#f59e0b"),
    ("#fb7185", "#fde047", "#34d399", "#a78bfa", "#fb923c"),
    ("#f87171", "#facc15", "#2dd4bf", "#f472b6", "#8b5cf6"),
    ("#ff3b30", "#ffcc00", "#34c759", "#af52de", "#ff2d55"),
)


@dataclass
class TrafficCar:
    """An oncoming/obstacle car on the road."""

    car_id: int
    lane: int
    y: float
    color: str
    style: str = "sedan"
    speed_factor: float = 1.0
    swerve_cooldown: float = 0.0
    morph_timer: float = 0.0


def lane_center_x(lane: int) -> float:
    """Return horizontal center coordinate for a lane (0, 1, or 2)."""
    return lane * LANE_WIDTH + LANE_WIDTH / 2.0


class CarGameEngine:
    """State machine for the 3-lane car dodging game."""

    def __init__(
        self,
        starting_level: int = 1,
        rng: random.Random | None = None,
    ) -> None:
        if not (1 <= starting_level <= len(SPEED_LEVELS)):
            raise ValueError("Nível inicial deve estar entre 1 e 10.")
        self._rng = rng or random.Random()
        self._starting_level = starting_level
        self._next_car_id = 1

        self.player_lane = 1
        self.player_y = PLAYER_Y
        self.level = starting_level
        self.score = 0
        self.dodged = 0
        self.high_score = 0
        self.game_over = False
        self.paused = False
        self.road_scroll_y = 0.0
        self._spawn_timer = 0.0
        self.traffic: list[TrafficCar] = []

    @property
    def speed_config(self) -> SpeedLevel:
        return SPEED_LEVELS[self.level - 1]

    def _level_colors(self) -> tuple[str, ...]:
        return LEVEL_COLOR_POOLS[self.level - 1]

    def reset(self, starting_level: int | None = None) -> None:
        """Reset round state, optionally changing the starting level (1-10)."""
        if starting_level is not None:
            if not (1 <= starting_level <= len(SPEED_LEVELS)):
                raise ValueError("Nível deve estar entre 1 e 10.")
            self._starting_level = starting_level

        self.player_lane = 1
        self.player_y = PLAYER_Y
        self.level = self._starting_level
        self.score = 0
        self.dodged = 0
        self.game_over = False
        self.paused = False
        self.road_scroll_y = 0.0
        self._spawn_timer = 0.0
        self.traffic.clear()

    def set_level(self, level: int) -> None:
        """Directly switch speed level (1-10) and mutate traffic cars."""
        if not (1 <= level <= len(SPEED_LEVELS)):
            raise ValueError("Nível deve estar entre 1 e 10.")
        if level != self.level:
            self.level = level
            self._mutate_traffic_for_level()

    def move_left(self) -> bool:
        """Move player car one lane left if possible."""
        if self.game_over or self.paused or self.player_lane <= 0:
            return False
        self.player_lane -= 1
        return True

    def move_right(self) -> bool:
        """Move player car one lane right if possible."""
        if self.game_over or self.paused or self.player_lane >= LANE_COUNT - 1:
            return False
        self.player_lane += 1
        return True

    def move_up(self) -> None:
        """Move player car slightly forward on the road."""
        if self.game_over or self.paused:
            return
        min_y = ROAD_HEIGHT * 0.45
        self.player_y = max(min_y, self.player_y - 26.0)

    def move_down(self) -> None:
        """Move player car back toward the bottom of the road."""
        if self.game_over or self.paused:
            return
        self.player_y = min(PLAYER_Y, self.player_y + 26.0)

    def toggle_pause(self) -> bool:
        """Toggle pause state when game is active."""
        if self.game_over:
            return False
        self.paused = not self.paused
        return self.paused

    def update(self, dt: float) -> None:
        """Advance simulation by dt seconds."""
        if self.game_over or self.paused or dt <= 0.0:
            return

        cfg = self.speed_config
        self.road_scroll_y = (
            self.road_scroll_y + cfg.speed_px_per_sec * dt
        ) % 80.0

        for car in self.traffic:
            car.y += cfg.speed_px_per_sec * car.speed_factor * dt
            self._update_dynamic_car(car, dt)

        # Remove cars that passed the bottom and award points
        remaining: list[TrafficCar] = []
        for car in self.traffic:
            if car.y > ROAD_HEIGHT + 10.0:
                self.dodged += 1
                self.score += 10 * self.level
                if self.score > self.high_score:
                    self.high_score = self.score
            else:
                remaining.append(car)
        self.traffic = remaining

        self._update_level_progression()

        # Spawn new traffic fairly
        self._spawn_timer += dt
        if self._spawn_timer >= cfg.spawn_interval_sec:
            if self._try_spawn_car():
                self._spawn_timer = 0.0

        # Check collisions with forgiving hitbox
        if self._has_collision():
            self.game_over = True

    def _update_level_progression(self) -> None:
        progressed_level = self._starting_level + (self.dodged // CARS_PER_LEVEL)
        new_level = min(len(SPEED_LEVELS), max(self.level, progressed_level))
        if new_level != self.level:
            self.level = new_level
            self._mutate_traffic_for_level()

    def _mutate_traffic_for_level(self) -> None:
        """Refresh active cars' styles, colors, and speeds when level changes."""
        colors = self._level_colors()
        for car in self.traffic:
            car.color = self._rng.choice(colors)
            car.style = self._rng.choice(CAR_STYLES)
            car.speed_factor = self._rng.uniform(0.90, 1.16)

    def _update_dynamic_car(self, car: TrafficCar, dt: float) -> None:
        """Continuously vary car appearance/speed and safely switch lanes."""
        car.morph_timer -= dt
        if car.morph_timer <= 0.0:
            car.morph_timer = self._rng.uniform(0.55, 1.15)
            car.color = self._rng.choice(self._level_colors())
            car.style = self._rng.choice(CAR_STYLES)
            car.speed_factor = self._rng.uniform(0.90, 1.16)

        car.swerve_cooldown -= dt
        # Only attempt a random lane change well above the player so it stays fair
        if (
            car.swerve_cooldown > 0.0
            or car.y < 10.0
            or car.y > self.player_y - CAR_HEIGHT * 2.1
        ):
            return

        car.swerve_cooldown = self._rng.uniform(0.65, 1.25)
        if self._rng.random() > self.speed_config.lane_change_chance:
            return

        adjacent = [
            target
            for target in (car.lane - 1, car.lane + 1)
            if 0 <= target < LANE_COUNT and self._is_lane_safe_for_shift(car, target)
        ]
        if adjacent:
            car.lane = self._rng.choice(adjacent)

    def _is_lane_safe_for_shift(self, moving_car: TrafficCar, target_lane: int) -> bool:
        """Ensure shifting to target_lane neither overlaps a car nor blocks all 3 lanes."""
        band_lanes = {moving_car.lane}
        for other in self.traffic:
            if other.car_id == moving_car.car_id:
                continue
            if abs(other.y - moving_car.y) < CAR_HEIGHT * 1.65:
                if other.lane == target_lane:
                    return False
                band_lanes.add(other.lane)

        band_lanes.add(target_lane)
        # Never allow a shift that creates a 3-lane wall
        return len(band_lanes) < LANE_COUNT

    def _try_spawn_car(self) -> bool:
        """Spawn an obstacle car ensuring at least one lane remains passable."""
        cfg = self.speed_config
        spawn_y = -CAR_HEIGHT - 12.0

        near_top = [
            car
            for car in self.traffic
            if (car.y - spawn_y) < cfg.min_vertical_gap_px
        ]
        occupied_lanes = {car.lane for car in near_top}

        if len(occupied_lanes) >= min(LANE_COUNT - 1, cfg.max_simultaneous_in_band):
            return False

        blocked_for_lane = {
            car.lane
            for car in self.traffic
            if abs(car.y - spawn_y) < CAR_HEIGHT + 40.0
        }
        available_lanes = [
            lane
            for lane in range(LANE_COUNT)
            if lane not in blocked_for_lane and lane not in occupied_lanes
        ]
        if not available_lanes:
            return False

        chosen_lane = self._rng.choice(available_lanes)
        color = self._rng.choice(self._level_colors())
        style = self._rng.choice(CAR_STYLES)
        speed_factor = self._rng.uniform(0.90, 1.16)

        self.traffic.append(
            TrafficCar(
                car_id=self._next_car_id,
                lane=chosen_lane,
                y=spawn_y,
                color=color,
                style=style,
                speed_factor=speed_factor,
                swerve_cooldown=self._rng.uniform(0.5, 1.1),
                morph_timer=self._rng.uniform(0.6, 1.2),
            )
        )
        self._next_car_id += 1
        return True

    def _has_collision(self) -> bool:
        px1 = (
            lane_center_x(self.player_lane)
            - CAR_WIDTH / 2.0
            + HITBOX_INSET_X
        )
        px2 = (
            lane_center_x(self.player_lane)
            + CAR_WIDTH / 2.0
            - HITBOX_INSET_X
        )
        py1 = self.player_y + HITBOX_INSET_Y
        py2 = self.player_y + CAR_HEIGHT - HITBOX_INSET_Y

        for car in self.traffic:
            if car.lane != self.player_lane:
                continue
            cy1 = car.y + HITBOX_INSET_Y
            cy2 = car.y + CAR_HEIGHT - HITBOX_INSET_Y
            if py1 < cy2 and py2 > cy1 and px1 < px2:
                return True
        return False
