"""Tkinter graphical interface for the 2D Counter-Strike-style game."""

import math
from time import perf_counter
import tkinter as tk

from cs_engine import (
    CS2DEngine,
    ENEMY_COUNT,
    ENEMY_MAX_HP,
    ENEMY_RADIUS,
    InputState,
    MAGAZINE_SIZE,
    MAP_HEIGHT,
    MAP_WIDTH,
    PLAYER_MAX_HP,
    PLAYER_RADIUS,
    RELOAD_DURATION_SEC,
)

# Theme colors
BG_MAIN = "#0f172a"
BG_CARD = "#1e293b"
FLOOR_COLOR = "#1a2433"
FLOOR_GRID = "#233044"
WALL_COLOR = "#475569"
WALL_BORDER = "#64748b"
CRATE_COLOR = "#92400e"
CRATE_BORDER = "#d97706"
BORDER_SLATE = "#334155"

FG_PRIMARY = "#f8fafc"
FG_MUTED = "#94a3b8"
CT_COLOR = "#38bdf8"
TR_COLOR = "#ef4444"
ACCENT_WIN = "#10b981"
ACCENT_WARN = "#facc15"

FRAME_MS = 16


class CS2DApp:
    """Main Tkinter window controller for CS 2D."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.engine = CS2DEngine()
        self._pressed_keys: set[str] = set()
        self._mouse_x = MAP_WIDTH / 2.0
        self._mouse_y = MAP_HEIGHT / 2.0
        self._mouse_firing = False
        self._reload_queued = False
        self._last_tick = perf_counter()
        self._after_id: str | None = None

        self._configure_window()
        self._build_ui()
        self._bind_controls()
        self._refresh_hud()
        self._render()
        self._schedule_loop()

    def _configure_window(self) -> None:
        self.root.title("CS 2D — Tático")
        self.root.geometry("820x690")
        self.root.minsize(800, 660)
        self.root.configure(bg=BG_MAIN)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        container = tk.Frame(self.root, bg=BG_MAIN, padx=20, pady=12)
        container.pack(fill=tk.BOTH, expand=True)

        # Header
        header = tk.Frame(container, bg=BG_MAIN)
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text="CS 2D — ARENA TÁTICA",
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
        self.pause_btn.pack(side=tk.RIGHT, padx=(8, 0))

        self.round_badge = tk.Label(
            header,
            text="Round 1",
            bg=BG_CARD,
            fg=CT_COLOR,
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=3,
        )
        self.round_badge.pack(side=tk.RIGHT)

        # Tactical HUD
        hud = tk.Frame(
            container,
            bg=BG_CARD,
            highlightbackground=BORDER_SLATE,
            highlightthickness=1,
            padx=14,
            pady=8,
        )
        hud.pack(fill=tk.X, pady=(8, 10))
        hud.columnconfigure((0, 1, 2, 3), weight=1)

        self.hp_label = tk.Label(
            hud,
            text=f"HP: {PLAYER_MAX_HP}",
            bg=BG_CARD,
            fg=ACCENT_WIN,
            font=("Consolas", 11, "bold"),
        )
        self.hp_label.grid(row=0, column=0, sticky="w")

        self.ammo_label = tk.Label(
            hud,
            text=f"Munição: {MAGAZINE_SIZE}/{MAGAZINE_SIZE}",
            bg=BG_CARD,
            fg=ACCENT_WARN,
            font=("Consolas", 11, "bold"),
        )
        self.ammo_label.grid(row=0, column=1)

        self.enemies_label = tk.Label(
            hud,
            text=f"Oponentes: {ENEMY_COUNT}/{ENEMY_COUNT}",
            bg=BG_CARD,
            fg=TR_COLOR,
            font=("Consolas", 11, "bold"),
        )
        self.enemies_label.grid(row=0, column=2)

        self.score_label = tk.Label(
            hud,
            text="CT 0 x 0 TR",
            bg=BG_CARD,
            fg=FG_PRIMARY,
            font=("Consolas", 11, "bold"),
        )
        self.score_label.grid(row=0, column=3, sticky="e")

        # Map Canvas
        map_holder = tk.Frame(container, bg=BORDER_SLATE, padx=1, pady=1)
        map_holder.pack()

        self.canvas = tk.Canvas(
            map_holder,
            width=int(MAP_WIDTH),
            height=int(MAP_HEIGHT),
            bg=FLOOR_COLOR,
            highlightthickness=0,
            cursor="crosshair",
        )
        self.canvas.pack()

        # Controls hint
        tk.Label(
            container,
            text="WASD (mover: W frente, S trás, A esq, D dir)  •  Mouse (visão/mira)  •  Botão Esq (atirar)  •  R (recarregar)  •  Enter (novo round)",
            bg=BG_MAIN,
            fg=FG_MUTED,
            font=("Segoe UI", 8),
        ).pack(pady=(10, 0))

    def _bind_controls(self) -> None:
        self.root.bind("<KeyPress>", self._on_key_press)
        self.root.bind("<KeyRelease>", self._on_key_release)
        self.root.bind("<KeyPress-r>", lambda _e: self._queue_reload())
        self.root.bind("<KeyPress-R>", lambda _e: self._queue_reload())
        self.root.bind("<KeyPress-p>", lambda _e: self.on_toggle_pause())
        self.root.bind("<KeyPress-P>", lambda _e: self.on_toggle_pause())
        self.root.bind("<Return>", lambda _e: self.on_next_round())

        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<B1-Motion>", self._on_mouse_move)
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)

    def _on_key_press(self, event: tk.Event) -> None:
        self._pressed_keys.add(event.keysym.lower())

    def _on_key_release(self, event: tk.Event) -> None:
        self._pressed_keys.discard(event.keysym.lower())

    def _on_mouse_move(self, event: tk.Event) -> None:
        self._mouse_x = float(event.x)
        self._mouse_y = float(event.y)

    def _on_mouse_down(self, event: tk.Event) -> None:
        self._mouse_x = float(event.x)
        self._mouse_y = float(event.y)
        self._mouse_firing = True

    def _on_mouse_up(self, event: tk.Event) -> None:
        self._mouse_x = float(event.x)
        self._mouse_y = float(event.y)
        self._mouse_firing = False

    def _queue_reload(self) -> None:
        self._reload_queued = True

    def _on_close(self) -> None:
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        self.root.destroy()

    def on_toggle_pause(self) -> None:
        if self.engine.round_over:
            self.on_next_round()
            return
        self.engine.toggle_pause()
        self._last_tick = perf_counter()
        self._refresh_hud()
        self._render()

    def on_next_round(self) -> None:
        self.engine.reset_round(increment_round=self.engine.round_over)
        self._last_tick = perf_counter()
        self._refresh_hud()
        self._render()

    def _current_inputs(self) -> InputState:
        keys = self._pressed_keys
        reload_now = self._reload_queued
        self._reload_queued = False
        return InputState(
            w="w" in keys,
            s="s" in keys,
            a="a" in keys,
            d="d" in keys,
            mouse_x=self._mouse_x,
            mouse_y=self._mouse_y,
            firing=self._mouse_firing,
            reload_pressed=reload_now,
        )

    def _schedule_loop(self) -> None:
        self._after_id = self.root.after(FRAME_MS, self._on_tick)

    def _on_tick(self) -> None:
        now = perf_counter()
        dt = min(0.05, max(0.0, now - self._last_tick))
        self._last_tick = now

        self.engine.update(dt, self._current_inputs())
        self._refresh_hud()
        self._render()
        self._schedule_loop()

    def _refresh_hud(self) -> None:
        hp = self.engine.player_hp
        hp_color = (
            ACCENT_WIN if hp > 50 else (ACCENT_WARN if hp > 25 else TR_COLOR)
        )
        self.hp_label.config(text=f"HP: {hp}", fg=hp_color)

        if self.engine.is_reloading:
            self.ammo_label.config(text="Recarregando...", fg=CT_COLOR)
        elif self.engine.ammo == 0:
            self.ammo_label.config(text="SEM BALA [R]", fg=TR_COLOR)
        else:
            self.ammo_label.config(
                text=f"Munição: {self.engine.ammo}/{MAGAZINE_SIZE}",
                fg=ACCENT_WARN,
            )

        self.enemies_label.config(
            text=f"Oponentes: {self.engine.alive_opponents}/{ENEMY_COUNT}"
        )
        self.score_label.config(
            text=f"CT {self.engine.wins} x {self.engine.losses} TR"
        )
        self.round_badge.config(text=f"Round {self.engine.round_number}")

        if self.engine.round_over:
            self.pause_btn.config(text="Próx. Round")
        elif self.engine.paused:
            self.pause_btn.config(text="Retomar (P)")
        else:
            self.pause_btn.config(text="Pausar (P)")

    def _render(self) -> None:
        c = self.canvas
        c.delete("all")

        # Floor grid
        for gx in range(38, int(MAP_WIDTH), 38):
            c.create_line(gx, 0, gx, MAP_HEIGHT, fill=FLOOR_GRID)
        for gy in range(38, int(MAP_HEIGHT), 38):
            c.create_line(0, gy, MAP_WIDTH, gy, fill=FLOOR_GRID)

        # 2D Vision cone (mouse aim FOV clipped by map obstacles)
        if not self.engine.round_over:
            self._draw_vision_cone()

        # Map obstacles (walls and crates)
        for obs in self.engine.obstacles:
            if obs.kind == "wall":
                c.create_rectangle(
                    obs.x, obs.y, obs.x + obs.w, obs.y + obs.h,
                    fill=WALL_COLOR, outline=WALL_BORDER, width=1,
                )
            else:
                c.create_rectangle(
                    obs.x, obs.y, obs.x + obs.w, obs.y + obs.h,
                    fill=CRATE_COLOR, outline=CRATE_BORDER, width=2,
                )
                c.create_line(
                    obs.x + 3, obs.y + 3, obs.x + obs.w - 3, obs.y + obs.h - 3,
                    fill=CRATE_BORDER, width=1,
                )
                c.create_line(
                    obs.x + obs.w - 3, obs.y + 3, obs.x + 3, obs.y + obs.h - 3,
                    fill=CRATE_BORDER, width=1,
                )

        # Laser sight line from player to cursor/obstacle
        if not self.engine.round_over:
            rx, ry = self.engine.cast_ray(
                self.engine.player_x,
                self.engine.player_y,
                self.engine.player_angle,
                420.0,
            )
            c.create_line(
                self.engine.player_x,
                self.engine.player_y,
                rx,
                ry,
                fill="#0284c7",
                dash=(4, 4),
            )

        # Opponents (only visible if alive)
        for bot in self.engine.opponents:
            if not bot.alive:
                continue
            self._draw_soldier(
                bot.x, bot.y, bot.angle, ENEMY_RADIUS, TR_COLOR, "#991b1b"
            )
            if bot.hp < ENEMY_MAX_HP:
                ratio = bot.hp / ENEMY_MAX_HP
                c.create_rectangle(
                    bot.x - 16, bot.y - 24, bot.x + 16, bot.y - 20,
                    fill="#0f172a", outline="",
                )
                c.create_rectangle(
                    bot.x - 16, bot.y - 24, bot.x - 16 + 32 * ratio, bot.y - 20,
                    fill=TR_COLOR, outline="",
                )

        # Player
        if self.engine.player_hp > 0:
            self._draw_soldier(
                self.engine.player_x,
                self.engine.player_y,
                self.engine.player_angle,
                PLAYER_RADIUS,
                CT_COLOR,
                "#0369a1",
            )
            if self.engine.muzzle_flash_timer > 0.0:
                mx = self.engine.player_x + math.cos(self.engine.player_angle) * 26.0
                my = self.engine.player_y + math.sin(self.engine.player_angle) * 26.0
                c.create_oval(
                    mx - 6, my - 6, mx + 6, my + 6, fill="#fef08a", outline=""
                )
            if self.engine.is_reloading:
                prog = 1.0 - (self.engine.reload_timer / RELOAD_DURATION_SEC)
                c.create_rectangle(
                    self.engine.player_x - 18,
                    self.engine.player_y - 26,
                    self.engine.player_x + 18,
                    self.engine.player_y - 21,
                    fill="#0f172a",
                    outline="",
                )
                c.create_rectangle(
                    self.engine.player_x - 18,
                    self.engine.player_y - 26,
                    self.engine.player_x - 18 + 36 * prog,
                    self.engine.player_y - 21,
                    fill=ACCENT_WARN,
                    outline="",
                )

        # Bullets
        for b in self.engine.bullets:
            color = "#fef08a" if b.from_player else "#fb7185"
            c.create_oval(
                b.x - 3, b.y - 3, b.x + 3, b.y + 3, fill=color, outline=""
            )

        # Hit sparks
        for hx, hy, _t in self.engine.hit_markers:
            c.create_oval(
                hx - 4, hy - 4, hx + 4, hy + 4, outline="#fbbf24", width=2
            )

        # Custom tactical crosshair at mouse
        mx, my = self._mouse_x, self._mouse_y
        c.create_oval(mx - 8, my - 8, mx + 8, my + 8, outline=ACCENT_WARN, width=1)
        c.create_line(mx - 12, my, mx - 4, my, fill=ACCENT_WARN)
        c.create_line(mx + 4, my, mx + 12, my, fill=ACCENT_WARN)
        c.create_line(mx, my - 12, mx, my - 4, fill=ACCENT_WARN)
        c.create_line(mx, my + 4, mx, my + 12, fill=ACCENT_WARN)

        # Overlay for Pause or Round Over
        if self.engine.paused or self.engine.round_over:
            c.create_rectangle(
                MAP_WIDTH / 2 - 200,
                MAP_HEIGHT / 2 - 75,
                MAP_WIDTH / 2 + 200,
                MAP_HEIGHT / 2 + 75,
                fill=BG_MAIN,
                outline=BORDER_SLATE,
                width=2,
            )
            if self.engine.round_over:
                title = (
                    "VITÓRIA DOS CTs!"
                    if self.engine.round_won
                    else "OPONENTES VENCERAM!"
                )
                color = ACCENT_WIN if self.engine.round_won else TR_COLOR
                c.create_text(
                    MAP_WIDTH / 2,
                    MAP_HEIGHT / 2 - 26,
                    text=title,
                    fill=color,
                    font=("Segoe UI", 19, "bold"),
                )
                c.create_text(
                    MAP_WIDTH / 2,
                    MAP_HEIGHT / 2 + 12,
                    text=f"Placar: CT {self.engine.wins} x {self.engine.losses} TR",
                    fill=FG_PRIMARY,
                    font=("Segoe UI", 11, "bold"),
                )
                c.create_text(
                    MAP_WIDTH / 2,
                    MAP_HEIGHT / 2 + 42,
                    text="Pressione Enter para o próximo round",
                    fill=FG_MUTED,
                    font=("Segoe UI", 9),
                )
            else:
                c.create_text(
                    MAP_WIDTH / 2,
                    MAP_HEIGHT / 2 - 14,
                    text="PAUSADO",
                    fill=ACCENT_WARN,
                    font=("Segoe UI", 20, "bold"),
                )
                c.create_text(
                    MAP_WIDTH / 2,
                    MAP_HEIGHT / 2 + 20,
                    text="Pressione P para continuar",
                    fill=FG_MUTED,
                    font=("Segoe UI", 10),
                )

    def _draw_vision_cone(self) -> None:
        """Draw a wall-clipped 2D field-of-view cone toward the mouse."""
        px, py = self.engine.player_x, self.engine.player_y
        base_angle = self.engine.player_angle
        fov = math.radians(66.0)
        steps = 22
        points: list[float] = [px, py]
        for i in range(steps + 1):
            a = base_angle - fov / 2.0 + (fov * i / steps)
            rx, ry = self.engine.cast_ray(px, py, a, 380.0)
            points.extend((rx, ry))
        self.canvas.create_polygon(
            points,
            fill="#38bdf8",
            stipple="gray12",
            outline="",
        )

    def _draw_soldier(
        self,
        x: float,
        y: float,
        angle: float,
        radius: float,
        primary: str,
        secondary: str,
    ) -> None:
        c = self.canvas
        # Gun barrel pointing toward aim angle
        gx = x + math.cos(angle) * (radius + 11.0)
        gy = y + math.sin(angle) * (radius + 11.0)
        c.create_line(x, y, gx, gy, fill="#cbd5e1", width=5)

        # Body & helmet
        c.create_oval(
            x - radius, y - radius, x + radius, y + radius,
            fill=secondary, outline="#0f172a", width=2,
        )
        c.create_oval(
            x - radius * 0.62,
            y - radius * 0.62,
            x + radius * 0.62,
            y + radius * 0.62,
            fill=primary,
            outline="#0f172a",
            width=1,
        )


def main() -> None:
    root = tk.Tk()
    CS2DApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
