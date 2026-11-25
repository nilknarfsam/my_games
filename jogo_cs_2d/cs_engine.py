"""Pure 2D tactical shooter engine inspired by Counter-Strike."""

from dataclasses import dataclass
import math
import random


MAP_WIDTH = 940.0
MAP_HEIGHT = 600.0
WALL_THICKNESS = 18.0

PLAYER_RADIUS = 15.0
PLAYER_SPEED = 215.0
PLAYER_WALK_SPEED = 112.0  # Silent Shift walk speed
PLAYER_MAX_HP = 100

STEP_INTERVAL_RUN_DIST = 54.0
ENEMY_STEP_INTERVAL_DIST = 58.0
HEARING_RADIUS = 290.0
SOUND_AUDIBLE_RADIUS = 460.0

MAGAZINE_SIZE = 15
RELOAD_DURATION_SEC = 1.25
PLAYER_FIRE_COOLDOWN = 0.16

ENEMY_COUNT = 2
ENEMY_RADIUS = 15.0
ENEMY_SPEED = 145.0
ENEMY_MAX_HP = 100
ENEMY_FIRE_COOLDOWN = 0.48
ENEMY_MAGAZINE = 10


@dataclass(frozen=True)
class WeaponSpec:
    """Stats for a selectable player weapon."""

    key: str
    label: str
    damage: int
    magazine_size: int
    fire_cooldown: float
    reload_duration: float
    bullet_speed: float
    spread: float


WEAPONS: dict[str, WeaponSpec] = {
    "rifle": WeaponSpec(
        key="rifle",
        label="Rifle Tático",
        damage=34,
        magazine_size=15,
        fire_cooldown=0.16,
        reload_duration=1.25,
        bullet_speed=760.0,
        spread=0.02,
    ),
    "smg": WeaponSpec(
        key="smg",
        label="Submetralhadora",
        damage=22,
        magazine_size=25,
        fire_cooldown=0.095,
        reload_duration=1.15,
        bullet_speed=720.0,
        spread=0.06,
    ),
    "pistol": WeaponSpec(
        key="pistol",
        label="Pistola Pesada",
        damage=50,
        magazine_size=9,
        fire_cooldown=0.28,
        reload_duration=1.00,
        bullet_speed=800.0,
        spread=0.01,
    ),
}


@dataclass(frozen=True)
class DifficultySpec:
    """Tuning parameters for bot AI difficulty."""

    key: str
    label: str
    bot_speed: float
    fire_cooldown: float
    spread: float
    damage: int


DIFFICULTIES: dict[str, DifficultySpec] = {
    "easy": DifficultySpec("easy", "Fácil", 115.0, 0.72, 0.18, 12),
    "normal": DifficultySpec("normal", "Normal", 145.0, 0.48, 0.11, 18),
    "hard": DifficultySpec("hard", "Difícil", 178.0, 0.32, 0.05, 24),
}


@dataclass(frozen=True)
class GameConfig:
    """User-configurable options chosen in the menu."""

    difficulty: str = "normal"
    weapon: str = "rifle"
    opponent_count: int = ENEMY_COUNT
    show_vision_cone: bool = True
    show_laser_sight: bool = True
    enable_sound: bool = True


@dataclass(frozen=True)
class RectObstacle:
    """Axis-aligned wall or crate in the map."""

    x: float
    y: float
    w: float
    h: float
    kind: str = "wall"  # "wall" or "crate"


@dataclass(frozen=True)
class InputState:
    """Real-time keyboard and mouse input state."""

    w: bool = False
    s: bool = False
    a: bool = False
    d: bool = False
    shift: bool = False
    mouse_x: float = MAP_WIDTH / 2.0
    mouse_y: float = MAP_HEIGHT / 2.0
    firing: bool = False
    reload_pressed: bool = False


@dataclass
class Projectile:
    """Bullet fired by player or an opponent."""

    x: float
    y: float
    vx: float
    vy: float
    from_player: bool
    damage: int = 25
    life: float = 1.6


@dataclass
class SoundRipple:
    """Visual acoustic ring produced by footsteps (unless walking with Shift)."""

    x: float
    y: float
    from_player: bool
    timer: float = 0.48
    max_timer: float = 0.48
    max_radius: float = 44.0


@dataclass
class Opponent:
    """An enemy bot on the map."""

    bot_id: int
    x: float
    y: float
    angle: float
    hp: int = ENEMY_MAX_HP
    ammo: int = ENEMY_MAGAZINE
    fire_cooldown: float = 0.6
    reload_timer: float = 0.0
    strafe_dir: float = 1.0
    strafe_timer: float = 1.2
    patrol_target: tuple[float, float] = (MAP_WIDTH / 2.0, MAP_HEIGHT / 2.0)
    move_phase: float = 0.0
    step_accum: float = 0.0
    investigate_target: tuple[float, float] | None = None
    investigate_timer: float = 0.0
    reaction_delay: float = 0.0
    was_seeing_player: bool = False
    alive: bool = True


BOT_SPAWN_POINTS: tuple[tuple[float, float, float], ...] = (
    (MAP_WIDTH - 95.0, 90.0, math.pi * 0.75),
    (MAP_WIDTH - 110.0, MAP_HEIGHT - 95.0, math.pi),
    (115.0, 88.0, math.pi * 0.25),
    (MAP_WIDTH * 0.62, MAP_HEIGHT * 0.50, math.pi),
)


def build_small_map() -> tuple[RectObstacle, ...]:
    """Create a medium-compact tactical arena where you hunt opponents across lanes."""
    t = WALL_THICKNESS
    return (
        # Outer perimeter
        RectObstacle(0.0, 0.0, MAP_WIDTH, t, "wall"),
        RectObstacle(0.0, MAP_HEIGHT - t, MAP_WIDTH, t, "wall"),
        RectObstacle(0.0, 0.0, t, MAP_HEIGHT, "wall"),
        RectObstacle(MAP_WIDTH - t, 0.0, t, MAP_HEIGHT, "wall"),
        # Central tactical warehouse bunker
        RectObstacle(415.0, 240.0, 110.0, 120.0, "wall"),
        # Upper and lower lane cover dividers
        RectObstacle(175.0, 145.0, 125.0, 32.0, "wall"),
        RectObstacle(175.0, 423.0, 125.0, 32.0, "wall"),
        RectObstacle(640.0, 145.0, 125.0, 32.0, "wall"),
        RectObstacle(640.0, 423.0, 125.0, 32.0, "wall"),
        # Flank ambush pillars / crates for hunting & surprise peeks
        RectObstacle(275.0, 276.0, 48.0, 48.0, "crate"),
        RectObstacle(617.0, 276.0, 48.0, 48.0, "crate"),
        RectObstacle(445.0, 82.0, 50.0, 46.0, "crate"),
        RectObstacle(445.0, 472.0, 50.0, 46.0, "crate"),
    )


def circle_intersects_rect(
    cx: float, cy: float, radius: float, rect: RectObstacle
) -> bool:
    closest_x = max(rect.x, min(cx, rect.x + rect.w))
    closest_y = max(rect.y, min(cy, rect.y + rect.h))
    dx = cx - closest_x
    dy = cy - closest_y
    return (dx * dx + dy * dy) < (radius * radius)


def segment_intersects_rect(
    x1: float, y1: float, x2: float, y2: float, rect: RectObstacle
) -> float | None:
    """Liang-Barsky ray/segment intersection returning hit t in [0, 1], or None."""
    dx = x2 - x1
    dy = y2 - y1
    p = (-dx, dx, -dy, dy)
    q = (x1 - rect.x, rect.x + rect.w - x1, y1 - rect.y, rect.y + rect.h - y1)

    t0 = 0.0
    t1 = 1.0
    for pi, qi in zip(p, q):
        if pi == 0.0:
            if qi < 0.0:
                return None
        else:
            r = qi / pi
            if pi < 0.0:
                if r > t1:
                    return None
                if r > t0:
                    t0 = r
            else:
                if r < t0:
                    return None
                if r < t1:
                    t1 = r
    return t0


class CS2DEngine:
    """Simulation engine for the 2D Counter-Strike-style arena."""

    def __init__(
        self,
        config: GameConfig | None = None,
        rng: random.Random | None = None,
    ) -> None:
        self._rng = rng or random.Random()
        self.obstacles = build_small_map()
        self.config = config or GameConfig()

        self.player_x = 85.0
        self.player_y = MAP_HEIGHT - 85.0
        self.player_angle = -math.pi / 4.0
        self.player_hp = PLAYER_MAX_HP
        self.player_move_phase = 0.0
        self.player_step_accum = 0.0
        self.is_stealth_walking = False
        self.ammo = self.weapon_spec.magazine_size
        self.reload_timer = 0.0
        self.fire_cooldown = 0.0
        self.muzzle_flash_timer = 0.0

        self.opponents: list[Opponent] = []
        self.bullets: list[Projectile] = []
        self.hit_markers: list[tuple[float, float, float]] = []
        self.sound_ripples: list[SoundRipple] = []
        self.pending_sounds: list[str] = []

        self.wins = 0
        self.losses = 0
        self.round_number = 1
        self.round_over = False
        self.round_won = False
        self.paused = False

        self.reset_round(increment_round=False)

    @property
    def weapon_spec(self) -> WeaponSpec:
        return WEAPONS.get(self.config.weapon, WEAPONS["rifle"])

    @property
    def difficulty_spec(self) -> DifficultySpec:
        return DIFFICULTIES.get(self.config.difficulty, DIFFICULTIES["normal"])

    @property
    def is_reloading(self) -> bool:
        return self.reload_timer > 0.0

    @property
    def alive_opponents(self) -> int:
        return sum(1 for bot in self.opponents if bot.alive)

    def consume_sounds(self) -> list[str]:
        """Pop queued sound effect names for the audio layer."""
        events = list(self.pending_sounds)
        self.pending_sounds.clear()
        return events

    def apply_config(self, config: GameConfig, reset_match: bool = False) -> None:
        """Apply new menu options; optionally restart match scores/round."""
        count_changed = config.opponent_count != self.config.opponent_count
        weapon_changed = config.weapon != self.config.weapon
        self.config = config

        if reset_match:
            self.wins = 0
            self.losses = 0
            self.round_number = 1
            self.reset_round(increment_round=False)
            return

        if weapon_changed:
            self.ammo = self.weapon_spec.magazine_size
            self.reload_timer = 0.0
            self.fire_cooldown = 0.0

        if count_changed:
            self.reset_round(increment_round=False)

    def reset_round(self, increment_round: bool = True) -> None:
        """Reset player, configured opponents, and bullets for a fresh round."""
        if increment_round:
            self.round_number += 1

        self.player_x = 85.0
        self.player_y = MAP_HEIGHT - 85.0
        self.player_angle = -math.pi / 4.0
        self.player_hp = PLAYER_MAX_HP
        self.player_move_phase = 0.0
        self.player_step_accum = 0.0
        self.is_stealth_walking = False
        self.ammo = self.weapon_spec.magazine_size
        self.reload_timer = 0.0
        self.fire_cooldown = 0.0
        self.muzzle_flash_timer = 0.0

        count = max(1, min(len(BOT_SPAWN_POINTS), self.config.opponent_count))
        self.opponents = []
        for idx in range(count):
            sx, sy, s_angle = BOT_SPAWN_POINTS[idx]
            self.opponents.append(
                Opponent(
                    bot_id=idx + 1,
                    x=sx,
                    y=sy,
                    angle=s_angle,
                    patrol_target=(
                        MAP_WIDTH * 0.56,
                        MAP_HEIGHT * (0.28 + 0.44 * (idx % 2)),
                    ),
                    strafe_dir=1.0 if idx % 2 == 0 else -1.0,
                )
            )

        self.bullets.clear()
        self.hit_markers.clear()
        self.sound_ripples.clear()
        self.pending_sounds.clear()
        self.round_over = False
        self.round_won = False
        self.paused = False

    def toggle_pause(self) -> bool:
        if self.round_over:
            return False
        self.paused = not self.paused
        return self.paused

    def start_reload(self) -> bool:
        """Start reloading magazine on R key if not full or already reloading."""
        max_ammo = self.weapon_spec.magazine_size
        if self.round_over or self.is_reloading or self.ammo >= max_ammo:
            return False
        self.reload_timer = self.weapon_spec.reload_duration
        self.pending_sounds.append("reload")
        return True

    def cast_ray(
        self, ox: float, oy: float, angle: float, max_dist: float
    ) -> tuple[float, float]:
        """Cast a vision/laser ray from (ox, oy) clipped by map obstacles."""
        end_x = ox + math.cos(angle) * max_dist
        end_y = oy + math.sin(angle) * max_dist
        best_t = 1.0
        for obs in self.obstacles:
            hit_t = segment_intersects_rect(ox, oy, end_x, end_y, obs)
            if hit_t is not None and hit_t < best_t:
                best_t = hit_t
        return ox + (end_x - ox) * best_t, oy + (end_y - oy) * best_t

    def has_line_of_sight(self, x1: float, y1: float, x2: float, y2: float) -> bool:
        """Return True if no wall or crate blocks the segment between two points."""
        for obs in self.obstacles:
            if segment_intersects_rect(x1, y1, x2, y2, obs) is not None:
                return False
        return True

    def update(self, dt: float, inputs: InputState) -> None:
        """Advance tactical simulation by dt seconds."""
        if self.round_over or self.paused or dt <= 0.0:
            return

        # Mouse aim
        dx_aim = inputs.mouse_x - self.player_x
        dy_aim = inputs.mouse_y - self.player_y
        if dx_aim != 0.0 or dy_aim != 0.0:
            self.player_angle = math.atan2(dy_aim, dx_aim)

        # Timers
        if self.fire_cooldown > 0.0:
            self.fire_cooldown = max(0.0, self.fire_cooldown - dt)
        if self.muzzle_flash_timer > 0.0:
            self.muzzle_flash_timer = max(0.0, self.muzzle_flash_timer - dt)
        if self.reload_timer > 0.0:
            self.reload_timer = max(0.0, self.reload_timer - dt)
            if self.reload_timer == 0.0:
                self.ammo = self.weapon_spec.magazine_size

        if inputs.reload_pressed:
            self.start_reload()

        # WASD Movement (+ Shift silent slow walk)
        move_x = float(inputs.d) - float(inputs.a)
        move_y = float(inputs.s) - float(inputs.w)
        is_moving = move_x != 0.0 or move_y != 0.0
        self.is_stealth_walking = inputs.shift

        if is_moving:
            if move_x != 0.0 and move_y != 0.0:
                inv_sqrt2 = 0.70710678
                move_x *= inv_sqrt2
                move_y *= inv_sqrt2
            speed = PLAYER_WALK_SPEED if inputs.shift else PLAYER_SPEED
            self.player_move_phase += dt * (6.0 if inputs.shift else 11.0)
        else:
            speed = PLAYER_SPEED

        prev_x, prev_y = self.player_x, self.player_y
        self.player_x, self.player_y = self._move_circle_with_slide(
            self.player_x,
            self.player_y,
            move_x * speed * dt,
            move_y * speed * dt,
            PLAYER_RADIUS,
        )
        moved_dist = math.hypot(self.player_x - prev_x, self.player_y - prev_y)

        # Emit player footsteps ONLY when not holding Shift
        if moved_dist > 0.05 and not inputs.shift:
            self.player_step_accum += moved_dist
            if self.player_step_accum >= STEP_INTERVAL_RUN_DIST:
                self.player_step_accum -= STEP_INTERVAL_RUN_DIST
                self._emit_player_footstep()
        elif inputs.shift:
            self.player_step_accum = 0.0

        # Shooting with left mouse button
        if inputs.firing and not self.is_reloading and self.fire_cooldown <= 0.0:
            if self.ammo > 0:
                self._fire_player_bullet()

        # Update opponents, bullets, hit markers, and sound ripples
        self._update_opponents(dt)
        self._update_bullets(dt)
        self.hit_markers = [
            (hx, hy, t - dt) for hx, hy, t in self.hit_markers if t - dt > 0.0
        ]
        self.sound_ripples = [
            SoundRipple(
                r.x, r.y, r.from_player, r.timer - dt, r.max_timer, r.max_radius
            )
            for r in self.sound_ripples
            if r.timer - dt > 0.0
        ]

        # Check round end conditions
        if self.player_hp <= 0:
            self.player_hp = 0
            self.round_over = True
            self.round_won = False
            self.losses += 1
        elif self.alive_opponents == 0:
            self.round_over = True
            self.round_won = True
            self.wins += 1

    def _emit_player_footstep(self) -> None:
        self.pending_sounds.append("player_step")
        self.sound_ripples.append(
            SoundRipple(self.player_x, self.player_y, from_player=True, max_radius=36.0)
        )
        # Nearby bots hear loud running footsteps and investigate!
        for bot in self.opponents:
            if not bot.alive:
                continue
            if math.hypot(bot.x - self.player_x, bot.y - self.player_y) <= HEARING_RADIUS:
                bot.investigate_target = (self.player_x, self.player_y)
                bot.investigate_timer = 2.6

    def _fire_player_bullet(self) -> None:
        w = self.weapon_spec
        self.ammo -= 1
        self.fire_cooldown = w.fire_cooldown
        self.muzzle_flash_timer = 0.05
        self.pending_sounds.append("gunshot")

        shot_angle = self.player_angle + self._rng.uniform(-w.spread, w.spread)
        muzzle_dist = PLAYER_RADIUS + 11.0
        bx = self.player_x + math.cos(self.player_angle) * muzzle_dist
        by = self.player_y + math.sin(self.player_angle) * muzzle_dist
        self.bullets.append(
            Projectile(
                x=bx,
                y=by,
                vx=math.cos(shot_angle) * w.bullet_speed,
                vy=math.sin(shot_angle) * w.bullet_speed,
                from_player=True,
                damage=w.damage,
            )
        )
        # Gunshots alert opponents across a wide radius
        for bot in self.opponents:
            if not bot.alive:
                continue
            if math.hypot(bot.x - self.player_x, bot.y - self.player_y) <= HEARING_RADIUS * 1.45:
                bot.investigate_target = (self.player_x, self.player_y)
                bot.investigate_timer = 3.0

    def _move_circle_with_slide(
        self, cx: float, cy: float, dx: float, dy: float, radius: float
    ) -> tuple[float, float]:
        nx = cx + dx
        if not self._collides_with_map(nx, cy, radius):
            cx = nx
        ny = cy + dy
        if not self._collides_with_map(cx, ny, radius):
            cy = ny
        return cx, cy

    def _collides_with_map(self, cx: float, cy: float, radius: float) -> bool:
        for obs in self.obstacles:
            if circle_intersects_rect(cx, cy, radius, obs):
                return True
        return False

    def _update_opponents(self, dt: float) -> None:
        diff = self.difficulty_spec
        for bot in self.opponents:
            if not bot.alive:
                continue

            if bot.reload_timer > 0.0:
                bot.reload_timer = max(0.0, bot.reload_timer - dt)
                if bot.reload_timer == 0.0:
                    bot.ammo = ENEMY_MAGAZINE
            if bot.fire_cooldown > 0.0:
                bot.fire_cooldown = max(0.0, bot.fire_cooldown - dt)
            if bot.investigate_timer > 0.0:
                bot.investigate_timer = max(0.0, bot.investigate_timer - dt)
                if bot.investigate_timer == 0.0:
                    bot.investigate_target = None

            can_see = self.has_line_of_sight(
                bot.x, bot.y, self.player_x, self.player_y
            )
            dist = math.hypot(self.player_x - bot.x, self.player_y - bot.y)
            bot.move_phase += dt * 9.0
            prev_x, prev_y = bot.x, bot.y

            if can_see:
                # Surprise delay if player sneaks up from behind without being heard
                if not bot.was_seeing_player:
                    angle_to_player = math.atan2(
                        self.player_y - bot.y, self.player_x - bot.x
                    )
                    angle_diff = abs(
                        math.atan2(
                            math.sin(angle_to_player - bot.angle),
                            math.cos(angle_to_player - bot.angle),
                        )
                    )
                    if angle_diff > math.radians(95.0) and bot.investigate_target is None:
                        bot.reaction_delay = 0.42
                bot.was_seeing_player = True

                if bot.reaction_delay > 0.0:
                    bot.reaction_delay = max(0.0, bot.reaction_delay - dt)
                else:
                    bot.angle = math.atan2(self.player_y - bot.y, self.player_x - bot.x)

                bot.strafe_timer -= dt
                if bot.strafe_timer <= 0.0:
                    bot.strafe_timer = self._rng.uniform(0.6, 1.4)
                    bot.strafe_dir = self._rng.choice((-1.0, 1.0))

                perp_angle = bot.angle + math.pi / 2.0
                vx = math.cos(perp_angle) * bot.strafe_dir * diff.bot_speed * 0.75
                vy = math.sin(perp_angle) * bot.strafe_dir * diff.bot_speed * 0.75
                if dist > 250.0:
                    vx += math.cos(bot.angle) * diff.bot_speed * 0.55
                    vy += math.sin(bot.angle) * diff.bot_speed * 0.55
                elif dist < 130.0:
                    vx -= math.cos(bot.angle) * diff.bot_speed * 0.55
                    vy -= math.sin(bot.angle) * diff.bot_speed * 0.55

                bot.x, bot.y = self._move_circle_with_slide(
                    bot.x, bot.y, vx * dt, vy * dt, ENEMY_RADIUS
                )

                if (
                    bot.reaction_delay <= 0.0
                    and bot.reload_timer <= 0.0
                    and bot.fire_cooldown <= 0.0
                ):
                    if bot.ammo > 0:
                        bot.ammo -= 1
                        bot.fire_cooldown = diff.fire_cooldown + self._rng.uniform(0.0, 0.2)
                        shot_angle = bot.angle + self._rng.uniform(-diff.spread, diff.spread)
                        muzzle = ENEMY_RADIUS + 11.0
                        speed = 520.0
                        self.bullets.append(
                            Projectile(
                                x=bot.x + math.cos(shot_angle) * muzzle,
                                y=bot.y + math.sin(shot_angle) * muzzle,
                                vx=math.cos(shot_angle) * speed,
                                vy=math.sin(shot_angle) * speed,
                                from_player=False,
                                damage=diff.damage,
                            )
                        )
                    else:
                        bot.reload_timer = 1.4
            else:
                bot.was_seeing_player = False
                target = (
                    bot.investigate_target
                    if bot.investigate_target is not None
                    else bot.patrol_target
                )
                tx, ty = target
                if math.hypot(tx - bot.x, ty - bot.y) < 26.0:
                    if bot.investigate_target is not None:
                        bot.investigate_target = None
                        bot.investigate_timer = 0.0
                    bot.patrol_target = (
                        self._rng.uniform(80.0, MAP_WIDTH - 80.0),
                        self._rng.uniform(80.0, MAP_HEIGHT - 80.0),
                    )
                    tx, ty = bot.patrol_target

                move_angle = math.atan2(ty - bot.y, tx - bot.x)
                bot.angle = move_angle
                speed_mult = 0.90 if bot.investigate_target is not None else 0.72
                bot.x, bot.y = self._move_circle_with_slide(
                    bot.x,
                    bot.y,
                    math.cos(move_angle) * diff.bot_speed * speed_mult * dt,
                    math.sin(move_angle) * diff.bot_speed * speed_mult * dt,
                    ENEMY_RADIUS,
                )
                if math.hypot(bot.x - prev_x, bot.y - prev_y) < 0.2:
                    bot.investigate_target = None
                    bot.patrol_target = (
                        self._rng.uniform(80.0, MAP_WIDTH - 80.0),
                        self._rng.uniform(80.0, MAP_HEIGHT - 80.0),
                    )

            # Bot footsteps (audible + visual ripple so player can track them!)
            bot_moved = math.hypot(bot.x - prev_x, bot.y - prev_y)
            if bot_moved > 0.05:
                bot.step_accum += bot_moved
                if bot.step_accum >= ENEMY_STEP_INTERVAL_DIST:
                    bot.step_accum -= ENEMY_STEP_INTERVAL_DIST
                    if dist <= SOUND_AUDIBLE_RADIUS:
                        self.pending_sounds.append(
                            "enemy_step" if dist <= 240.0 else "enemy_step_far"
                        )
                    self.sound_ripples.append(
                        SoundRipple(bot.x, bot.y, from_player=False, max_radius=46.0)
                    )

    def _update_bullets(self, dt: float) -> None:
        kept: list[Projectile] = []
        for b in self.bullets:
            nx = b.x + b.vx * dt
            ny = b.y + b.vy * dt
            b.life -= dt
            if b.life <= 0.0:
                continue

            blocked = False
            for obs in self.obstacles:
                if segment_intersects_rect(b.x, b.y, nx, ny, obs) is not None:
                    self.hit_markers.append((b.x, b.y, 0.16))
                    blocked = True
                    break
            if blocked:
                continue

            b.x, b.y = nx, ny

            if b.from_player:
                hit_bot = False
                for bot in self.opponents:
                    if not bot.alive:
                        continue
                    if math.hypot(b.x - bot.x, b.y - bot.y) <= ENEMY_RADIUS + 3.0:
                        bot.hp = max(0, bot.hp - b.damage)
                        # Getting shot alerts the bot immediately
                        bot.investigate_target = (self.player_x, self.player_y)
                        bot.investigate_timer = 3.0
                        bot.reaction_delay = 0.0
                        self.hit_markers.append((b.x, b.y, 0.22))
                        if bot.hp == 0:
                            bot.alive = False
                        hit_bot = True
                        break
                if hit_bot:
                    continue
            else:
                if math.hypot(b.x - self.player_x, b.y - self.player_y) <= PLAYER_RADIUS + 3.0:
                    self.player_hp = max(0, self.player_hp - b.damage)
                    self.hit_markers.append((b.x, b.y, 0.22))
                    continue

            kept.append(b)
        self.bullets = kept
