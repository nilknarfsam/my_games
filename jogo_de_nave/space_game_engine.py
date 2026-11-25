"""Pure simulation engine for the Space Shooter (Jogo de Nave) game."""

from dataclasses import dataclass
import math
import random


ARENA_WIDTH = 480.0
ARENA_HEIGHT = 600.0

PLAYER_WIDTH = 42.0
PLAYER_HEIGHT = 44.0
PLAYER_SPEED = 290.0

INITIAL_LIVES = 3
MAX_SHOT_LEVEL = 3
KILLS_PER_SHOT_LEVEL = 10
SPECIAL_BONUS_LIMIT_SEC = 20.0
INVULNERABLE_SEC = 1.6

ENEMY_TYPES: tuple[str, ...] = ("scout", "zigzag", "shooter", "maluca")


@dataclass(frozen=True)
class InputState:
    """Frame input flags controlled by keyboard."""

    up: bool = False
    down: bool = False
    left: bool = False
    right: bool = False
    fire: bool = False
    use_bomb: bool = False


@dataclass
class Bullet:
    """Projectile fired by the player or an enemy."""

    x: float
    y: float
    vx: float
    vy: float
    from_player: bool
    damage: int = 1
    color: str = "#38bdf8"
    radius: float = 4.0


@dataclass
class Enemy:
    """Enemy spaceship with distinct movement and HP."""

    enemy_id: int
    kind: str
    x: float
    y: float
    width: float
    height: float
    hp: int
    max_hp: int
    vx: float
    vy: float
    age: float = 0.0
    fire_cooldown: float = 1.4
    dash_timer: float = 0.6
    phase: float = 0.0
    points: int = 10


@dataclass
class BonusItem:
    """Collectible bonus drifting down the screen."""

    bonus_id: int
    kind: str  # "special_weapon" or "bomb"
    x: float
    y: float
    vy: float = 105.0
    radius: float = 16.0


@dataclass
class Explosion:
    """Visual explosion ring with remaining lifetime."""

    x: float
    y: float
    color: str
    timer: float = 0.35
    max_timer: float = 0.35


class SpaceGameEngine:
    """State machine for the space shooter game."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()
        self._next_enemy_id = 1
        self._next_bonus_id = 1

        self.player_x = ARENA_WIDTH / 2.0
        self.player_y = ARENA_HEIGHT - 70.0
        self.lives = INITIAL_LIVES
        self.shot_level = 1
        self.kills_since_hit = 0
        self.total_kills = 0
        self.score = 0
        self.high_score = 0
        self.wave = 1

        self.special_weapon_timer = 0.0
        self.bomb_timer = 0.0
        self.has_bomb = False
        self.bomb_flash_timer = 0.0

        self.invulnerable_timer = 0.0
        self.fire_cooldown = 0.0
        self.spawn_timer = 0.6
        self.bonus_spawn_timer = 7.0
        self.elapsed_time = 0.0

        self.game_over = False
        self.paused = False

        self.bullets: list[Bullet] = []
        self.enemies: list[Enemy] = []
        self.bonuses: list[BonusItem] = []
        self.explosions: list[Explosion] = []

    @property
    def special_weapon_active(self) -> bool:
        return self.special_weapon_timer > 0.0

    def reset(self) -> None:
        """Reset game state for a new match."""
        self.player_x = ARENA_WIDTH / 2.0
        self.player_y = ARENA_HEIGHT - 70.0
        self.lives = INITIAL_LIVES
        self.shot_level = 1
        self.kills_since_hit = 0
        self.total_kills = 0
        self.score = 0
        self.wave = 1

        self.special_weapon_timer = 0.0
        self.bomb_timer = 0.0
        self.has_bomb = False
        self.bomb_flash_timer = 0.0

        self.invulnerable_timer = 0.0
        self.fire_cooldown = 0.0
        self.spawn_timer = 0.5
        self.bonus_spawn_timer = 6.5
        self.elapsed_time = 0.0

        self.game_over = False
        self.paused = False

        self.bullets.clear()
        self.enemies.clear()
        self.bonuses.clear()
        self.explosions.clear()

    def toggle_pause(self) -> bool:
        if self.game_over:
            return False
        self.paused = not self.paused
        return self.paused

    def update(self, dt: float, inputs: InputState) -> None:
        """Advance simulation by dt seconds."""
        if self.game_over or self.paused or dt <= 0.0:
            return

        self.elapsed_time += dt
        self.wave = 1 + (self.total_kills // 12)

        # Countdown timers (including 20s limits for bomb & special weapon)
        if self.invulnerable_timer > 0.0:
            self.invulnerable_timer = max(0.0, self.invulnerable_timer - dt)
        if self.special_weapon_timer > 0.0:
            self.special_weapon_timer = max(0.0, self.special_weapon_timer - dt)
        if self.has_bomb:
            self.bomb_timer = max(0.0, self.bomb_timer - dt)
            if self.bomb_timer <= 0.0:
                self.has_bomb = False
        if self.bomb_flash_timer > 0.0:
            self.bomb_flash_timer = max(0.0, self.bomb_flash_timer - dt)
        if self.fire_cooldown > 0.0:
            self.fire_cooldown = max(0.0, self.fire_cooldown - dt)

        self._move_player(dt, inputs)

        if inputs.use_bomb and self.has_bomb:
            self.detonate_bomb()

        if inputs.fire and self.fire_cooldown <= 0.0:
            self._fire_player_weapon()

        self._update_bullets(dt)
        self._update_enemies(dt)
        self._update_bonuses(dt)
        self._update_explosions(dt)

        self._handle_bullet_collisions()
        self._handle_player_collisions()
        self._handle_bonus_pickups()

        # Spawn enemies and bonuses
        self.spawn_timer -= dt
        if self.spawn_timer <= 0.0:
            self._spawn_enemy()
            base_interval = max(0.36, 1.05 - (self.wave - 1) * 0.07)
            self.spawn_timer = self._rng.uniform(
                base_interval * 0.75, base_interval * 1.25
            )

        self.bonus_spawn_timer -= dt
        if self.bonus_spawn_timer <= 0.0:
            self.spawn_bonus()
            self.bonus_spawn_timer = self._rng.uniform(7.5, 12.0)

    def _move_player(self, dt: float, inputs: InputState) -> None:
        dx = float(inputs.right) - float(inputs.left)
        dy = float(inputs.down) - float(inputs.up)
        if dx != 0.0 and dy != 0.0:
            inv_sqrt2 = 0.70710678
            dx *= inv_sqrt2
            dy *= inv_sqrt2

        self.player_x += dx * PLAYER_SPEED * dt
        self.player_y += dy * PLAYER_SPEED * dt

        half_w = PLAYER_WIDTH / 2.0 + 6.0
        half_h = PLAYER_HEIGHT / 2.0 + 6.0
        self.player_x = max(half_w, min(ARENA_WIDTH - half_w, self.player_x))
        self.player_y = max(half_h + 24.0, min(ARENA_HEIGHT - half_h, self.player_y))

    def _fire_player_weapon(self) -> None:
        py = self.player_y - PLAYER_HEIGHT / 2.0
        if self.special_weapon_active:
            # 5-way special plasma spread
            self.fire_cooldown = 0.11
            angles_vx = (-170.0, -85.0, 0.0, 85.0, 170.0)
            for vx in angles_vx:
                self.bullets.append(
                    Bullet(
                        x=self.player_x,
                        y=py,
                        vx=vx,
                        vy=-640.0,
                        from_player=True,
                        damage=2,
                        color="#facc15",
                        radius=5.0,
                    )
                )
            return

        if self.shot_level == 1:
            self.fire_cooldown = 0.20
            self.bullets.append(
                Bullet(self.player_x, py, 0.0, -560.0, True, 1, "#38bdf8", 4.0)
            )
        elif self.shot_level == 2:
            self.fire_cooldown = 0.18
            self.bullets.append(
                Bullet(self.player_x - 11.0, py + 4.0, 0.0, -580.0, True, 1, "#34d399", 4.0)
            )
            self.bullets.append(
                Bullet(self.player_x + 11.0, py + 4.0, 0.0, -580.0, True, 1, "#34d399", 4.0)
            )
        else:
            self.fire_cooldown = 0.16
            self.bullets.append(
                Bullet(self.player_x, py, 0.0, -600.0, True, 1, "#a78bfa", 4.5)
            )
            self.bullets.append(
                Bullet(self.player_x - 12.0, py + 6.0, -75.0, -580.0, True, 1, "#38bdf8", 4.0)
            )
            self.bullets.append(
                Bullet(self.player_x + 12.0, py + 6.0, 75.0, -580.0, True, 1, "#38bdf8", 4.0)
            )

    def detonate_bomb(self) -> int:
        """Detonate the active bomb, wiping normal enemies and damaging tough ones."""
        if not self.has_bomb or self.game_over:
            return 0

        self.has_bomb = False
        self.bomb_timer = 0.0
        self.bomb_flash_timer = 0.30

        # Clear enemy bullets
        self.bullets = [b for b in self.bullets if b.from_player]

        destroyed = 0
        survivors: list[Enemy] = []
        for enemy in self.enemies:
            enemy.hp -= 4
            self.explosions.append(Explosion(enemy.x, enemy.y, "#f97316"))
            if enemy.hp <= 0:
                destroyed += 1
                self._award_kill(enemy)
            else:
                survivors.append(enemy)
        self.enemies = survivors
        return destroyed

    def _award_kill(self, enemy: Enemy) -> None:
        self.total_kills += 1
        self.kills_since_hit += 1
        self.score += enemy.points
        if self.score > self.high_score:
            self.high_score = self.score

        # Automatic shot upgrade up to level 3 if player doesn't die
        target_level = min(
            MAX_SHOT_LEVEL, 1 + (self.kills_since_hit // KILLS_PER_SHOT_LEVEL)
        )
        if target_level > self.shot_level:
            self.shot_level = target_level

    def _update_bullets(self, dt: float) -> None:
        kept: list[Bullet] = []
        for b in self.bullets:
            b.x += b.vx * dt
            b.y += b.vy * dt
            if -20.0 <= b.x <= ARENA_WIDTH + 20.0 and -20.0 <= b.y <= ARENA_HEIGHT + 20.0:
                kept.append(b)
        self.bullets = kept

    def _update_enemies(self, dt: float) -> None:
        kept: list[Enemy] = []
        for e in self.enemies:
            e.age += dt
            if e.kind == "zigzag":
                e.vx = math.sin(e.age * 4.5 + e.phase) * 140.0
            elif e.kind == "maluca":
                # Crazy erratic ship: fast sinusoidal weave + sudden random dashes!
                e.dash_timer -= dt
                if e.dash_timer <= 0.0:
                    e.dash_timer = self._rng.uniform(0.22, 0.55)
                    e.vx = self._rng.choice((-1.0, 1.0)) * self._rng.uniform(220.0, 340.0)
                    e.vy = self._rng.uniform(95.0, 200.0)
                e.vx += math.cos(e.age * 11.0 + e.phase) * 260.0 * dt
                e.vx = max(-340.0, min(340.0, e.vx))
            elif e.kind == "shooter":
                e.vx = math.sin(e.age * 2.2 + e.phase) * 55.0

            e.x += e.vx * dt
            e.y += e.vy * dt

            half_w = e.width / 2.0 + 6.0
            if e.x < half_w:
                e.x = half_w
                e.vx = abs(e.vx)
            elif e.x > ARENA_WIDTH - half_w:
                e.x = ARENA_WIDTH - half_w
                e.vx = -abs(e.vx)

            # Enemy firing
            if e.kind in ("shooter", "maluca") and 20.0 < e.y < ARENA_HEIGHT - 120.0:
                e.fire_cooldown -= dt
                if e.fire_cooldown <= 0.0:
                    e.fire_cooldown = (
                        self._rng.uniform(1.1, 1.9)
                        if e.kind == "shooter"
                        else self._rng.uniform(0.9, 1.6)
                    )
                    dx = self.player_x - e.x
                    dy = max(40.0, self.player_y - e.y)
                    dist = math.hypot(dx, dy)
                    speed = 250.0 if e.kind == "shooter" else 290.0
                    self.bullets.append(
                        Bullet(
                            x=e.x,
                            y=e.y + e.height / 2.0,
                            vx=(dx / dist) * speed * 0.45,
                            vy=speed,
                            from_player=False,
                            damage=1,
                            color="#fb7185",
                            radius=4.5,
                        )
                    )

            if e.y <= ARENA_HEIGHT + 50.0:
                kept.append(e)
        self.enemies = kept

    def _update_bonuses(self, dt: float) -> None:
        kept: list[BonusItem] = []
        for b in self.bonuses:
            b.y += b.vy * dt
            if b.y <= ARENA_HEIGHT + 30.0:
                kept.append(b)
        self.bonuses = kept

    def _update_explosions(self, dt: float) -> None:
        kept: list[Explosion] = []
        for exp in self.explosions:
            exp.timer -= dt
            if exp.timer > 0.0:
                kept.append(exp)
        self.explosions = kept

    def _handle_bullet_collisions(self) -> None:
        remaining_bullets: list[Bullet] = []
        for b in self.bullets:
            if not b.from_player:
                remaining_bullets.append(b)
                continue

            hit = False
            for e in self.enemies:
                if (
                    abs(b.x - e.x) <= (e.width / 2.0 + b.radius)
                    and abs(b.y - e.y) <= (e.height / 2.0 + b.radius)
                ):
                    e.hp -= b.damage
                    hit = True
                    if e.hp <= 0:
                        self.explosions.append(
                            Explosion(
                                e.x,
                                e.y,
                                "#f43f5e" if e.kind == "maluca" else "#fbbf24",
                            )
                        )
                        self._award_kill(e)
                    break
            if not hit:
                remaining_bullets.append(b)

        self.bullets = remaining_bullets
        self.enemies = [e for e in self.enemies if e.hp > 0]

    def _handle_player_collisions(self) -> None:
        if self.invulnerable_timer > 0.0:
            return

        px_half = PLAYER_WIDTH / 2.0 - 6.0
        py_half = PLAYER_HEIGHT / 2.0 - 6.0

        # Enemy bullets hitting player
        remaining_bullets: list[Bullet] = []
        took_hit = False
        for b in self.bullets:
            if (
                not b.from_player
                and not took_hit
                and abs(b.x - self.player_x) <= (px_half + b.radius)
                and abs(b.y - self.player_y) <= (py_half + b.radius)
            ):
                took_hit = True
                continue
            remaining_bullets.append(b)
        self.bullets = remaining_bullets

        # Enemy ships colliding with player
        if not took_hit:
            for e in self.enemies:
                if (
                    abs(e.x - self.player_x) <= (px_half + e.width / 2.0 - 5.0)
                    and abs(e.y - self.player_y) <= (py_half + e.height / 2.0 - 5.0)
                ):
                    e.hp = 0
                    self.explosions.append(Explosion(e.x, e.y, "#ef4444"))
                    took_hit = True
                    break
            self.enemies = [e for e in self.enemies if e.hp > 0]

        if took_hit:
            self._damage_player()

    def _damage_player(self) -> None:
        self.lives = max(0, self.lives - 1)
        self.kills_since_hit = 0
        self.shot_level = 1
        self.invulnerable_timer = INVULNERABLE_SEC
        self.explosions.append(Explosion(self.player_x, self.player_y, "#38bdf8"))
        if self.lives <= 0:
            self.game_over = True

    def _handle_bonus_pickups(self) -> None:
        remaining: list[BonusItem] = []
        for b in self.bonuses:
            dist = math.hypot(b.x - self.player_x, b.y - self.player_y)
            if dist <= (b.radius + PLAYER_WIDTH / 2.0):
                self._apply_bonus(b.kind)
            else:
                remaining.append(b)
        self.bonuses = remaining

    def _apply_bonus(self, kind: str) -> None:
        if kind == "special_weapon":
            self.special_weapon_timer = SPECIAL_BONUS_LIMIT_SEC
            if self.shot_level < MAX_SHOT_LEVEL:
                self.shot_level += 1
        elif kind == "bomb":
            self.has_bomb = True
            self.bomb_timer = SPECIAL_BONUS_LIMIT_SEC

    def spawn_bonus(self, kind: str | None = None, x: float | None = None) -> BonusItem:
        """Spawn a bonus item (special weapon or bomb) at the top."""
        chosen_kind = kind or self._rng.choice(("special_weapon", "bomb"))
        chosen_x = x if x is not None else self._rng.uniform(44.0, ARENA_WIDTH - 44.0)
        item = BonusItem(
            bonus_id=self._next_bonus_id,
            kind=chosen_kind,
            x=chosen_x,
            y=-20.0,
        )
        self._next_bonus_id += 1
        self.bonuses.append(item)
        return item

    def _spawn_enemy(self, kind: str | None = None) -> Enemy:
        """Spawn a random enemy; crazy ships appear more often in higher waves."""
        if kind is None:
            maluca_weight = min(0.38, 0.16 + (self.wave - 1) * 0.04)
            weights = (
                0.36,
                0.24,
                max(0.14, 0.40 - maluca_weight),
                maluca_weight,
            )
            kind = self._rng.choices(ENEMY_TYPES, weights=weights, k=1)[0]

        x = self._rng.uniform(38.0, ARENA_WIDTH - 38.0)
        phase = self._rng.uniform(0.0, math.tau)
        speed_boost = 1.0 + min(0.6, (self.wave - 1) * 0.06)

        if kind == "scout":
            w, h, hp, vy, pts = 34.0, 34.0, 1, 165.0 * speed_boost, 10
            vx = self._rng.uniform(-45.0, 45.0)
        elif kind == "zigzag":
            w, h, hp, vy, pts = 38.0, 36.0, 2, 135.0 * speed_boost, 20
            vx = 120.0
        elif kind == "shooter":
            w, h, hp, vy, pts = 44.0, 42.0, 3, 95.0 * speed_boost, 30
            vx = 40.0
        else:  # maluca (hard-to-hit erratic ship)
            w, h, hp, vy, pts = 32.0, 32.0, 3, 150.0 * speed_boost, 50
            vx = self._rng.choice((-1.0, 1.0)) * 240.0

        enemy = Enemy(
            enemy_id=self._next_enemy_id,
            kind=kind,
            x=x,
            y=-30.0,
            width=w,
            height=h,
            hp=hp,
            max_hp=hp,
            vx=vx,
            vy=vy,
            phase=phase,
            points=pts,
        )
        self._next_enemy_id += 1
        self.enemies.append(enemy)
        return enemy
