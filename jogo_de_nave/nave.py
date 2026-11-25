"""Tkinter graphical interface for Jogo de Nave."""

import math
import random
from time import perf_counter
import tkinter as tk

from space_game_engine import (
    ARENA_HEIGHT,
    ARENA_WIDTH,
    Enemy,
    InputState,
    INITIAL_LIVES,
    PLAYER_HEIGHT,
    PLAYER_WIDTH,
    SPECIAL_BONUS_LIMIT_SEC,
    SpaceGameEngine,
)

# Theme colors
BG_MAIN = "#090d1a"
BG_CARD = "#131b2e"
BORDER_SLATE = "#28354f"
FG_PRIMARY = "#f8fafc"
FG_MUTED = "#94a3b8"
ACCENT_CYAN = "#38bdf8"
ACCENT_HEART = "#f43f5e"
ACCENT_GOLD = "#facc15"
ACCENT_BOMB = "#fb923c"
ACCENT_WIN = "#10b981"

FRAME_MS = 16


class NaveApp:
    """Main Tkinter window controller for Jogo de Nave."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.engine = SpaceGameEngine()
        self._pressed_keys: set[str] = set()
        self._auto_fire = True
        self._last_tick = perf_counter()
        self._after_id: str | None = None

        rng = random.Random(7)
        self._stars: list[list[float]] = [
            [
                rng.uniform(0, ARENA_WIDTH),
                rng.uniform(0, ARENA_HEIGHT),
                rng.uniform(30.0, 120.0),
                rng.choice((1.0, 1.5, 2.2)),
            ]
            for _ in range(55)
        ]

        self._configure_window()
        self._build_ui()
        self._bind_controls()
        self._refresh_hud()
        self._render()
        self._schedule_loop()

    def _configure_window(self) -> None:
        self.root.title("Jogo de Nave")
        self.root.geometry("540x820")
        self.root.minsize(515, 780)
        self.root.configure(bg=BG_MAIN)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        container = tk.Frame(self.root, bg=BG_MAIN, padx=20, pady=14)
        container.pack(fill=tk.BOTH, expand=True)

        # Header
        header = tk.Frame(container, bg=BG_MAIN)
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text="JOGO DE NAVE",
            bg=BG_MAIN,
            fg=FG_MUTED,
            font=("Segoe UI", 10, "bold"),
        ).pack(side=tk.LEFT)

        self.pause_btn = tk.Button(
            header,
            text="Pausar (P)",
            command=self.on_toggle_pause,
            bg=BG_CARD,
            fg=FG_PRIMARY,
            relief=tk.FLAT,
            cursor="hand2",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=2,
        )
        self.pause_btn.pack(side=tk.RIGHT, padx=(6, 0))

        self.autofire_btn = tk.Button(
            header,
            text="Auto-Tiro: ON",
            command=self.on_toggle_autofire,
            bg="#065f46",
            fg="#6ee7b7",
            relief=tk.FLAT,
            cursor="hand2",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=2,
        )
        self.autofire_btn.pack(side=tk.RIGHT)

        # HUD Card: Hearts, Shot Level, Score/Wave
        hud = tk.Frame(
            container,
            bg=BG_CARD,
            highlightbackground=BORDER_SLATE,
            highlightthickness=1,
            padx=14,
            pady=8,
        )
        hud.pack(fill=tk.X, pady=(8, 8))
        hud.columnconfigure((0, 1, 2), weight=1)

        self.hearts_label = tk.Label(
            hud,
            text="♥ ♥ ♥",
            bg=BG_CARD,
            fg=ACCENT_HEART,
            font=("Segoe UI", 14, "bold"),
        )
        self.hearts_label.grid(row=0, column=0, sticky="w")

        self.shot_label = tk.Label(
            hud,
            text="Tiro: Nível 1/3",
            bg=BG_CARD,
            fg=ACCENT_CYAN,
            font=("Segoe UI", 10, "bold"),
        )
        self.shot_label.grid(row=0, column=1)

        self.score_label = tk.Label(
            hud,
            text="Pts: 0  |  Rec: 0",
            bg=BG_CARD,
            fg=FG_PRIMARY,
            font=("Consolas", 10, "bold"),
        )
        self.score_label.grid(row=0, column=2, sticky="e")

        # Active 20s bonus timers bar
        bonus_bar = tk.Frame(container, bg=BG_MAIN)
        bonus_bar.pack(fill=tk.X, pady=(0, 8))
        bonus_bar.columnconfigure((0, 1), weight=1)

        self.special_label = tk.Label(
            bonus_bar,
            text="Arma Especial: —",
            bg=BG_CARD,
            fg=FG_MUTED,
            font=("Consolas", 9, "bold"),
            padx=10,
            pady=5,
        )
        self.special_label.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self.bomb_label = tk.Label(
            bonus_bar,
            text="Bomba [B]: —",
            bg=BG_CARD,
            fg=FG_MUTED,
            font=("Consolas", 9, "bold"),
            padx=10,
            pady=5,
        )
        self.bomb_label.grid(row=0, column=1, sticky="ew", padx=(5, 0))

        # Arena Canvas
        arena_holder = tk.Frame(container, bg=BORDER_SLATE, padx=1, pady=1)
        arena_holder.pack()

        self.canvas = tk.Canvas(
            arena_holder,
            width=int(ARENA_WIDTH),
            height=int(ARENA_HEIGHT),
            bg=BG_MAIN,
            highlightthickness=0,
        )
        self.canvas.pack()

        # Controls hint
        tk.Label(
            container,
            text="Setas ← → ↑ ↓ (mover)  •  Espaço (atirar)  •  B (bomba)  •  P (pausa)  •  Enter (reiniciar)",
            bg=BG_MAIN,
            fg=FG_MUTED,
            font=("Segoe UI", 8),
        ).pack(pady=(10, 0))

    def _bind_controls(self) -> None:
        self.root.bind("<KeyPress>", self._on_key_press)
        self.root.bind("<KeyRelease>", self._on_key_release)
        self.root.bind("<KeyPress-p>", lambda _e: self.on_toggle_pause())
        self.root.bind("<KeyPress-P>", lambda _e: self.on_toggle_pause())
        self.root.bind("<Return>", lambda _e: self.on_restart())
        self.root.bind("<KeyPress-r>", lambda _e: self.on_restart())
        self.root.bind("<KeyPress-R>", lambda _e: self.on_restart())
        self.root.bind("<KeyPress-b>", lambda _e: self.on_use_bomb())
        self.root.bind("<KeyPress-B>", lambda _e: self.on_use_bomb())

    def _on_key_press(self, event: tk.Event) -> None:
        self._pressed_keys.add(event.keysym.lower())

    def _on_key_release(self, event: tk.Event) -> None:
        self._pressed_keys.discard(event.keysym.lower())

    def _on_close(self) -> None:
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        self.root.destroy()

    def on_toggle_pause(self) -> None:
        if self.engine.game_over:
            self.on_restart()
            return
        self.engine.toggle_pause()
        self._last_tick = perf_counter()
        self._refresh_hud()
        self._render()

    def on_toggle_autofire(self) -> None:
        self._auto_fire = not self._auto_fire
        if self._auto_fire:
            self.autofire_btn.config(
                text="Auto-Tiro: ON", bg="#065f46", fg="#6ee7b7"
            )
        else:
            self.autofire_btn.config(
                text="Auto-Tiro: OFF", bg=BG_CARD, fg=FG_MUTED
            )

    def on_use_bomb(self) -> None:
        self.engine.detonate_bomb()
        self._refresh_hud()

    def on_restart(self) -> None:
        self.engine.reset()
        self._last_tick = perf_counter()
        self._refresh_hud()
        self._render()

    def _current_input_state(self) -> InputState:
        keys = self._pressed_keys
        return InputState(
            up="up" in keys or "w" in keys,
            down="down" in keys or "s" in keys,
            left="left" in keys or "a" in keys,
            right="right" in keys or "d" in keys,
            fire=self._auto_fire or ("space" in keys),
            use_bomb=False,
        )

    def _schedule_loop(self) -> None:
        self._after_id = self.root.after(FRAME_MS, self._on_tick)

    def _on_tick(self) -> None:
        now = perf_counter()
        dt = min(0.05, max(0.0, now - self._last_tick))
        self._last_tick = now

        if not self.engine.paused and not self.engine.game_over:
            for star in self._stars:
                star[1] += star[2] * dt
                if star[1] > ARENA_HEIGHT:
                    star[1] = -2.0

        self.engine.update(dt, self._current_input_state())
        self._refresh_hud()
        self._render()
        self._schedule_loop()

    def _refresh_hud(self) -> None:
        hearts = " ".join(
            "♥" if i < self.engine.lives else "♡" for i in range(INITIAL_LIVES)
        )
        self.hearts_label.config(text=hearts)

        if self.engine.special_weapon_active:
            self.shot_label.config(text="Tiro: ESPECIAL 5x", fg=ACCENT_GOLD)
        else:
            self.shot_label.config(
                text=f"Tiro: Nível {self.engine.shot_level}/3", fg=ACCENT_CYAN
            )

        self.score_label.config(
            text=f"Pts: {self.engine.score}  |  Rec: {self.engine.high_score}"
        )

        if self.engine.special_weapon_active:
            secs = math.ceil(self.engine.special_weapon_timer)
            self.special_label.config(
                text=f"Arma Especial: {secs:02d}s / {int(SPECIAL_BONUS_LIMIT_SEC)}s",
                fg=ACCENT_GOLD,
            )
        else:
            self.special_label.config(text="Arma Especial: —", fg=FG_MUTED)

        if self.engine.has_bomb:
            secs = math.ceil(self.engine.bomb_timer)
            self.bomb_label.config(
                text=f"Bomba [B]: {secs:02d}s / {int(SPECIAL_BONUS_LIMIT_SEC)}s",
                fg=ACCENT_BOMB,
            )
        else:
            self.bomb_label.config(text="Bomba [B]: —", fg=FG_MUTED)

        if self.engine.game_over:
            self.pause_btn.config(text="Reiniciar")
        elif self.engine.paused:
            self.pause_btn.config(text="Retomar (P)")
        else:
            self.pause_btn.config(text="Pausar (P)")

    def _render(self) -> None:
        c = self.canvas
        c.delete("all")

        # Bomb detonation flash
        if self.engine.bomb_flash_timer > 0.0:
            c.create_rectangle(
                0, 0, ARENA_WIDTH, ARENA_HEIGHT, fill="#7c2d12", outline=""
            )

        # Starfield
        for sx, sy, speed, size in self._stars:
            shade = "#cbd5e1" if speed > 85.0 else "#475569"
            c.create_oval(sx, sy, sx + size, sy + size, fill=shade, outline="")

        # Bonuses
        for bonus in self.engine.bonuses:
            if bonus.kind == "special_weapon":
                c.create_oval(
                    bonus.x - bonus.radius,
                    bonus.y - bonus.radius,
                    bonus.x + bonus.radius,
                    bonus.y + bonus.radius,
                    fill="#713f12",
                    outline=ACCENT_GOLD,
                    width=2,
                )
                c.create_text(
                    bonus.x,
                    bonus.y,
                    text="ARMA",
                    fill=ACCENT_GOLD,
                    font=("Segoe UI", 7, "bold"),
                )
            else:
                c.create_oval(
                    bonus.x - bonus.radius,
                    bonus.y - bonus.radius,
                    bonus.x + bonus.radius,
                    bonus.y + bonus.radius,
                    fill="#7c2d12",
                    outline=ACCENT_BOMB,
                    width=2,
                )
                c.create_text(
                    bonus.x,
                    bonus.y,
                    text="BOMB",
                    fill=ACCENT_BOMB,
                    font=("Segoe UI", 7, "bold"),
                )

        # Bullets
        for b in self.engine.bullets:
            c.create_oval(
                b.x - b.radius,
                b.y - b.radius * 1.4,
                b.x + b.radius,
                b.y + b.radius * 1.4,
                fill=b.color,
                outline="",
            )

        # Enemies
        for enemy in self.engine.enemies:
            self._draw_enemy(enemy)

        # Explosions
        for exp in self.engine.explosions:
            progress = 1.0 - (exp.timer / exp.max_timer)
            r = 8.0 + progress * 26.0
            c.create_oval(
                exp.x - r, exp.y - r, exp.x + r, exp.y + r, outline=exp.color, width=2
            )

        # Player Ship
        if not self.engine.game_over:
            self._draw_player()

        # Overlay for Pause or Game Over
        if self.engine.paused or self.engine.game_over:
            c.create_rectangle(
                36,
                ARENA_HEIGHT / 2 - 80,
                ARENA_WIDTH - 36,
                ARENA_HEIGHT / 2 + 80,
                fill=BG_MAIN,
                outline=BORDER_SLATE,
                width=2,
            )
            if self.engine.game_over:
                c.create_text(
                    ARENA_WIDTH / 2,
                    ARENA_HEIGHT / 2 - 34,
                    text="NAVE DESTRUÍDA!",
                    fill=ACCENT_HEART,
                    font=("Segoe UI", 20, "bold"),
                )
                c.create_text(
                    ARENA_WIDTH / 2,
                    ARENA_HEIGHT / 2 + 4,
                    text=f"Pontuação: {self.engine.score}   •   Inimigos: {self.engine.total_kills}",
                    fill=FG_PRIMARY,
                    font=("Segoe UI", 11, "bold"),
                )
                c.create_text(
                    ARENA_WIDTH / 2,
                    ARENA_HEIGHT / 2 + 38,
                    text="Pressione Enter ou R para jogar novamente",
                    fill=FG_MUTED,
                    font=("Segoe UI", 10),
                )
            else:
                c.create_text(
                    ARENA_WIDTH / 2,
                    ARENA_HEIGHT / 2 - 14,
                    text="PAUSADO",
                    fill=ACCENT_GOLD,
                    font=("Segoe UI", 20, "bold"),
                )
                c.create_text(
                    ARENA_WIDTH / 2,
                    ARENA_HEIGHT / 2 + 22,
                    text="Pressione P para continuar",
                    fill=FG_MUTED,
                    font=("Segoe UI", 10),
                )

    def _draw_player(self) -> None:
        c = self.canvas
        px = self.engine.player_x
        py = self.engine.player_y

        # Blink during invulnerability frames
        if (
            self.engine.invulnerable_timer > 0.0
            and int(self.engine.invulnerable_timer * 14) % 2 == 1
        ):
            return

        if self.engine.invulnerable_timer > 0.0:
            c.create_oval(
                px - 28, py - 28, px + 28, py + 28, outline=ACCENT_CYAN, width=2
            )

        # Thruster flame
        flame_len = 10 + (int(self.engine.elapsed_time * 30) % 7)
        c.create_polygon(
            px - 6,
            py + PLAYER_HEIGHT / 2 - 4,
            px + 6,
            py + PLAYER_HEIGHT / 2 - 4,
            px,
            py + PLAYER_HEIGHT / 2 + flame_len,
            fill=ACCENT_BOMB,
            outline="",
        )

        # Main ship hull
        ship_color = ACCENT_GOLD if self.engine.special_weapon_active else ACCENT_CYAN
        c.create_polygon(
            px,
            py - PLAYER_HEIGHT / 2,
            px + PLAYER_WIDTH / 2,
            py + PLAYER_HEIGHT / 2 - 4,
            px + 7,
            py + PLAYER_HEIGHT / 2 - 10,
            px - 7,
            py + PLAYER_HEIGHT / 2 - 10,
            px - PLAYER_WIDTH / 2,
            py + PLAYER_HEIGHT / 2 - 4,
            fill=ship_color,
            outline="#0f172a",
            width=2,
        )
        # Cockpit
        c.create_oval(
            px - 5, py - 9, px + 5, py + 5, fill="#e0f2fe", outline=""
        )

    def _draw_enemy(self, e: Enemy) -> None:
        c = self.canvas
        x, y = e.x, e.y
        hw, hh = e.width / 2.0, e.height / 2.0

        if e.kind == "scout":
            c.create_polygon(
                x, y + hh, x - hw, y - hh + 6, x + hw, y - hh + 6,
                fill="#ef4444", outline="#0f172a", width=2,
            )
        elif e.kind == "zigzag":
            c.create_polygon(
                x, y - hh, x + hw, y, x, y + hh, x - hw, y,
                fill="#a855f7", outline="#0f172a", width=2,
            )
        elif e.kind == "shooter":
            c.create_rectangle(
                x - hw, y - hh, x + hw, y + hh,
                fill="#f59e0b", outline="#0f172a", width=2,
            )
            c.create_rectangle(
                x - 6, y - 6, x + 6, y + hh + 3, fill="#78350f", outline=""
            )
        else:  # maluca (flashing neon erratic ship)
            flash = int(e.age * 16) % 2 == 0
            neon = "#f43f5e" if flash else "#22d3ee"
            c.create_oval(
                x - hw - 4, y - hh - 4, x + hw + 4, y + hh + 4,
                outline=neon, width=2,
            )
            c.create_polygon(
                x, y - hh, x + hw, y + hh * 0.5, x, y + hh, x - hw, y + hh * 0.5,
                fill="#ec4899" if flash else "#a3e635", outline="#0f172a", width=2,
            )

        # Mini HP bar for multi-HP enemies
        if e.max_hp > 1 and e.hp < e.max_hp:
            bar_w = e.width
            ratio = max(0.0, e.hp / e.max_hp)
            c.create_rectangle(
                x - bar_w / 2, y - hh - 7, x + bar_w / 2, y - hh - 3,
                fill="#1e293b", outline="",
            )
            c.create_rectangle(
                x - bar_w / 2, y - hh - 7, x - bar_w / 2 + bar_w * ratio, y - hh - 3,
                fill=ACCENT_WIN, outline="",
            )


def main() -> None:
    root = tk.Tk()
    NaveApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
