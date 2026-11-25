"""Tkinter graphical interface for CS 2D with top-down soldiers, stealth, sound, and menu."""

import math
from time import perf_counter
import tkinter as tk

from cs_engine import (
    CS2DEngine,
    DIFFICULTIES,
    ENEMY_MAX_HP,
    GameConfig,
    InputState,
    MAP_HEIGHT,
    MAP_WIDTH,
    PLAYER_MAX_HP,
    WEAPONS,
)
from sound_fx import SoundManager

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


def _rotate_point(
    cx: float, cy: float, lx: float, ly: float, angle: float
) -> tuple[float, float]:
    """Rotate a local offset (lx, ly) around (cx, cy) by angle radians."""
    ca = math.cos(angle)
    sa = math.sin(angle)
    return cx + lx * ca - ly * sa, cy + lx * sa + ly * ca


def _rotated_poly(
    cx: float, cy: float, angle: float, local_pts: tuple[tuple[float, float], ...]
) -> list[float]:
    """Return flattened rotated coordinates ready for Canvas.create_polygon."""
    coords: list[float] = []
    for lx, ly in local_pts:
        wx, wy = _rotate_point(cx, cy, lx, ly, angle)
        coords.extend((wx, wy))
    return coords


class CS2DApp:
    """Main Tkinter window controller for CS 2D."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.engine = CS2DEngine()
        self.sound = SoundManager(enabled=self.engine.config.enable_sound)
        self._pressed_keys: set[str] = set()
        self._shift_held = False
        self._mouse_x = MAP_WIDTH / 2.0
        self._mouse_y = MAP_HEIGHT / 2.0
        self._mouse_firing = False
        self._reload_queued = False
        self._menu_open = True
        self._match_started = False
        self._last_tick = perf_counter()
        self._after_id: str | None = None

        self._diff_buttons: dict[str, tk.Button] = {}
        self._weapon_buttons: dict[str, tk.Button] = {}
        self._count_buttons: dict[int, tk.Button] = {}

        self._selected_diff = self.engine.config.difficulty
        self._selected_weapon = self.engine.config.weapon
        self._selected_count = self.engine.config.opponent_count
        self._var_cone = tk.BooleanVar(value=self.engine.config.show_vision_cone)
        self._var_laser = tk.BooleanVar(value=self.engine.config.show_laser_sight)
        self._var_sound = tk.BooleanVar(value=self.engine.config.enable_sound)

        self._configure_window()
        self._build_ui()
        self._build_menu_overlay()
        self._bind_controls()
        self._sync_menu_styles()
        self._refresh_hud()
        self._render()
        self._schedule_loop()

    def _configure_window(self) -> None:
        self.root.title("CS 2D — Arena Tática")
        self.root.geometry("990x760")
        self.root.minsize(970, 730)
        self.root.configure(bg=BG_MAIN)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        container = tk.Frame(self.root, bg=BG_MAIN, padx=18, pady=10)
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

        self.stealth_badge = tk.Label(
            header,
            text="CORRENDO (Com passos)",
            bg=BG_CARD,
            fg=FG_MUTED,
            font=("Segoe UI", 8, "bold"),
            padx=10,
            pady=3,
        )
        self.stealth_badge.pack(side=tk.LEFT, padx=(14, 0))

        self.menu_btn = tk.Button(
            header,
            text="Menu / Opções (Esc)",
            command=self.on_toggle_menu,
            bg=BG_CARD,
            fg=CT_COLOR,
            relief=tk.FLAT,
            cursor="hand2",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=2,
        )
        self.menu_btn.pack(side=tk.RIGHT, padx=(6, 0))

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
            pady=7,
        )
        hud.pack(fill=tk.X, pady=(8, 8))
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
            text="Munição: 15/15",
            bg=BG_CARD,
            fg=ACCENT_WARN,
            font=("Consolas", 11, "bold"),
        )
        self.ammo_label.grid(row=0, column=1)

        self.enemies_label = tk.Label(
            hud,
            text="Oponentes: 2/2",
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

        # Map Canvas holder (also hosts Menu overlay)
        self.map_holder = tk.Frame(container, bg=BORDER_SLATE, padx=1, pady=1)
        self.map_holder.pack()

        self.canvas = tk.Canvas(
            self.map_holder,
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
            text="WASD (mover)  •  Segurar Shift (andar sem passos)  •  Mouse (visão/mira)  •  Botão Esq (atirar)  •  R (recarregar)  •  Esc (menu)",
            bg=BG_MAIN,
            fg=FG_MUTED,
            font=("Segoe UI", 8),
        ).pack(pady=(8, 0))

    def _build_menu_overlay(self) -> None:
        self.menu_overlay = tk.Frame(
            self.map_holder,
            bg=BG_MAIN,
            highlightbackground=CT_COLOR,
            highlightthickness=2,
            padx=28,
            pady=22,
        )

        tk.Label(
            self.menu_overlay,
            text="CS 2D — MENU & OPÇÕES",
            bg=BG_MAIN,
            fg=CT_COLOR,
            font=("Segoe UI", 16, "bold"),
        ).pack(pady=(0, 4))

        tk.Label(
            self.menu_overlay,
            text="Configure sua partida tática e use Shift para andar sem fazer barulho",
            bg=BG_MAIN,
            fg=FG_MUTED,
            font=("Segoe UI", 9),
        ).pack(pady=(0, 14))

        self._add_option_title("Dificuldade dos Oponentes")
        diff_row = tk.Frame(self.menu_overlay, bg=BG_MAIN)
        diff_row.pack(fill=tk.X, pady=(0, 10))
        for key, spec in DIFFICULTIES.items():
            btn = tk.Button(
                diff_row,
                text=spec.label,
                command=lambda k=key: self._select_difficulty(k),
                relief=tk.FLAT,
                cursor="hand2",
                font=("Segoe UI", 9, "bold"),
                padx=12,
                pady=6,
            )
            btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)
            self._diff_buttons[key] = btn

        self._add_option_title("Arma Inicial")
        weapon_row = tk.Frame(self.menu_overlay, bg=BG_MAIN)
        weapon_row.pack(fill=tk.X, pady=(0, 10))
        for key, spec in WEAPONS.items():
            btn = tk.Button(
                weapon_row,
                text=spec.label,
                command=lambda k=key: self._select_weapon(k),
                relief=tk.FLAT,
                cursor="hand2",
                font=("Segoe UI", 9, "bold"),
                padx=10,
                pady=6,
            )
            btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)
            self._weapon_buttons[key] = btn

        self._add_option_title("Quantidade de Oponentes")
        count_row = tk.Frame(self.menu_overlay, bg=BG_MAIN)
        count_row.pack(fill=tk.X, pady=(0, 10))
        for count in (1, 2, 3, 4):
            btn = tk.Button(
                count_row,
                text=f"{count} {'Oponente' if count == 1 else 'Oponentes'}",
                command=lambda c=count: self._select_count(c),
                relief=tk.FLAT,
                cursor="hand2",
                font=("Segoe UI", 9, "bold"),
                padx=8,
                pady=6,
            )
            btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)
            self._count_buttons[count] = btn

        toggles_row = tk.Frame(self.menu_overlay, bg=BG_CARD, padx=12, pady=8)
        toggles_row.pack(fill=tk.X, pady=(4, 16))

        for label, var in (
            ("Cone de visão 2D", self._var_cone),
            ("Mira laser", self._var_laser),
            ("Som de passos e tiros", self._var_sound),
        ):
            tk.Checkbutton(
                toggles_row,
                text=label,
                variable=var,
                bg=BG_CARD,
                fg=FG_PRIMARY,
                selectcolor=BG_MAIN,
                activebackground=BG_CARD,
                activeforeground=FG_PRIMARY,
                font=("Segoe UI", 9),
            ).pack(side=tk.LEFT, padx=(0, 12))

        actions = tk.Frame(self.menu_overlay, bg=BG_MAIN)
        actions.pack(fill=tk.X)

        self.play_btn = tk.Button(
            actions,
            text="Iniciar Partida",
            command=self.on_apply_and_play,
            bg=ACCENT_WIN,
            fg=BG_MAIN,
            activebackground="#059669",
            activeforeground=BG_MAIN,
            relief=tk.FLAT,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=16,
            pady=9,
        )
        self.play_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 6))

        self.restart_match_btn = tk.Button(
            actions,
            text="Reiniciar Placar",
            command=self.on_restart_match,
            bg=BG_CARD,
            fg=FG_PRIMARY,
            activebackground=BORDER_SLATE,
            activeforeground=FG_PRIMARY,
            relief=tk.FLAT,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=9,
        )
        self.restart_match_btn.pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(
            actions,
            text="Sair",
            command=self._on_close,
            bg="#7f1d1d",
            fg=FG_PRIMARY,
            activebackground=TR_COLOR,
            activeforeground=FG_PRIMARY,
            relief=tk.FLAT,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=9,
        ).pack(side=tk.LEFT)

        self._show_menu_overlay(True)

    def _add_option_title(self, text: str) -> None:
        tk.Label(
            self.menu_overlay,
            text=text,
            bg=BG_MAIN,
            fg=FG_MUTED,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        ).pack(fill=tk.X, pady=(0, 4))

    def _select_difficulty(self, key: str) -> None:
        self._selected_diff = key
        self._sync_menu_styles()

    def _select_weapon(self, key: str) -> None:
        self._selected_weapon = key
        self._sync_menu_styles()

    def _select_count(self, count: int) -> None:
        self._selected_count = count
        self._sync_menu_styles()

    def _sync_menu_styles(self) -> None:
        for key, btn in self._diff_buttons.items():
            active = key == self._selected_diff
            btn.config(
                bg=CT_COLOR if active else BG_CARD,
                fg=BG_MAIN if active else FG_PRIMARY,
            )
        for key, btn in self._weapon_buttons.items():
            active = key == self._selected_weapon
            btn.config(
                bg=ACCENT_WARN if active else BG_CARD,
                fg=BG_MAIN if active else FG_PRIMARY,
            )
        for count, btn in self._count_buttons.items():
            active = count == self._selected_count
            btn.config(
                bg=ACCENT_WIN if active else BG_CARD,
                fg=BG_MAIN if active else FG_PRIMARY,
            )

    def _show_menu_overlay(self, show: bool) -> None:
        self._menu_open = show
        if show:
            self.play_btn.config(
                text="Continuar Partida" if self._match_started else "Iniciar Partida"
            )
            self.menu_overlay.place(
                relx=0.5, rely=0.5, anchor=tk.CENTER, width=560
            )
            self.menu_overlay.lift()
        else:
            self.menu_overlay.place_forget()

    def _bind_controls(self) -> None:
        self.root.bind("<KeyPress>", self._on_key_press)
        self.root.bind("<KeyRelease>", self._on_key_release)
        self.root.bind("<FocusOut>", self._on_focus_out)
        self.root.bind("<KeyPress-r>", lambda _e: self._queue_reload())
        self.root.bind("<KeyPress-R>", lambda _e: self._queue_reload())
        self.root.bind("<KeyPress-p>", lambda _e: self.on_toggle_pause())
        self.root.bind("<KeyPress-P>", lambda _e: self.on_toggle_pause())
        self.root.bind("<Escape>", lambda _e: self.on_toggle_menu())
        self.root.bind("<Return>", lambda _e: self.on_next_round())

        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<B1-Motion>", self._on_mouse_move)
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)

    def _on_key_press(self, event: tk.Event) -> None:
        sym = event.keysym.lower()
        self._pressed_keys.add(sym)
        if sym in ("shift_l", "shift_r") or bool(event.state & 0x0001):
            self._shift_held = True

    def _on_key_release(self, event: tk.Event) -> None:
        sym = event.keysym.lower()
        self._pressed_keys.discard(sym)
        if sym in ("shift_l", "shift_r"):
            self._shift_held = (
                "shift_l" in self._pressed_keys or "shift_r" in self._pressed_keys
            )

    def _on_focus_out(self, _event: tk.Event) -> None:
        self._pressed_keys.clear()
        self._shift_held = False
        self._mouse_firing = False

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

    def on_toggle_menu(self) -> None:
        if self._menu_open:
            self.on_apply_and_play()
        else:
            self._mouse_firing = False
            self._show_menu_overlay(True)
            self._refresh_hud()

    def on_apply_and_play(self) -> None:
        cfg = GameConfig(
            difficulty=self._selected_diff,
            weapon=self._selected_weapon,
            opponent_count=self._selected_count,
            show_vision_cone=self._var_cone.get(),
            show_laser_sight=self._var_laser.get(),
            enable_sound=self._var_sound.get(),
        )
        self.sound.enabled = cfg.enable_sound
        self.engine.apply_config(cfg, reset_match=not self._match_started)
        self._match_started = True
        self._show_menu_overlay(False)
        self._last_tick = perf_counter()
        self._refresh_hud()
        self._render()

    def on_restart_match(self) -> None:
        cfg = GameConfig(
            difficulty=self._selected_diff,
            weapon=self._selected_weapon,
            opponent_count=self._selected_count,
            show_vision_cone=self._var_cone.get(),
            show_laser_sight=self._var_laser.get(),
            enable_sound=self._var_sound.get(),
        )
        self.sound.enabled = cfg.enable_sound
        self.engine.apply_config(cfg, reset_match=True)
        self._match_started = True
        self._show_menu_overlay(False)
        self._last_tick = perf_counter()
        self._refresh_hud()
        self._render()

    def on_toggle_pause(self) -> None:
        if self._menu_open:
            return
        if self.engine.round_over:
            self.on_next_round()
            return
        self.engine.toggle_pause()
        self._last_tick = perf_counter()
        self._refresh_hud()
        self._render()

    def on_next_round(self) -> None:
        if self._menu_open:
            self.on_apply_and_play()
            return
        self.engine.reset_round(increment_round=self.engine.round_over)
        self._last_tick = perf_counter()
        self._refresh_hud()
        self._render()

    def _current_inputs(self) -> InputState:
        keys = self._pressed_keys
        reload_now = self._reload_queued
        self._reload_queued = False
        shift_now = (
            self._shift_held or "shift_l" in keys or "shift_r" in keys
        )
        return InputState(
            w="w" in keys,
            s="s" in keys,
            a="a" in keys,
            d="d" in keys,
            shift=shift_now,
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

        if not self._menu_open:
            self.engine.update(dt, self._current_inputs())
            for sound_name in self.engine.consume_sounds():
                self.sound.play(sound_name)
            self._refresh_hud()
            self._render()
        self._schedule_loop()

    def _refresh_hud(self) -> None:
        hp = self.engine.player_hp
        hp_color = (
            ACCENT_WIN if hp > 50 else (ACCENT_WARN if hp > 25 else TR_COLOR)
        )
        self.hp_label.config(text=f"HP: {hp}", fg=hp_color)

        max_ammo = self.engine.weapon_spec.magazine_size
        if self.engine.is_reloading:
            self.ammo_label.config(text="Recarregando...", fg=CT_COLOR)
        elif self.engine.ammo == 0:
            self.ammo_label.config(text="SEM BALA [R]", fg=TR_COLOR)
        else:
            self.ammo_label.config(
                text=f"Munição: {self.engine.ammo}/{max_ammo}",
                fg=ACCENT_WARN,
            )

        if self.engine.is_stealth_walking:
            self.stealth_badge.config(
                text="FURTIVO [SHIFT] (Sem passos)", fg=ACCENT_WIN
            )
        else:
            self.stealth_badge.config(
                text="CORRENDO (Com passos)", fg=FG_MUTED
            )

        total_bots = len(self.engine.opponents)
        self.enemies_label.config(
            text=f"Oponentes: {self.engine.alive_opponents}/{total_bots}"
        )
        self.score_label.config(
            text=f"CT {self.engine.wins} x {self.engine.losses} TR"
        )
        diff_label = self.engine.difficulty_spec.label
        self.round_badge.config(
            text=f"Round {self.engine.round_number} • {diff_label}"
        )

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
        for gx in range(47, int(MAP_WIDTH), 47):
            c.create_line(gx, 0, gx, MAP_HEIGHT, fill=FLOOR_GRID)
        for gy in range(47, int(MAP_HEIGHT), 47):
            c.create_line(0, gy, MAP_WIDTH, gy, fill=FLOOR_GRID)

        # 2D Vision cone
        if self.engine.config.show_vision_cone and not self.engine.round_over:
            self._draw_vision_cone()

        # Acoustic footstep ripples (visible even behind cover!)
        for ripple in self.engine.sound_ripples:
            progress = 1.0 - (ripple.timer / ripple.max_timer)
            r = 10.0 + progress * ripple.max_radius
            color = CT_COLOR if ripple.from_player else "#fb923c"
            c.create_oval(
                ripple.x - r,
                ripple.y - r,
                ripple.x + r,
                ripple.y + r,
                outline=color,
                width=2 if progress < 0.5 else 1,
                dash=(4, 3),
            )

        # Map obstacles
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

        # Laser sight
        if self.engine.config.show_laser_sight and not self.engine.round_over:
            rx, ry = self.engine.cast_ray(
                self.engine.player_x,
                self.engine.player_y,
                self.engine.player_angle,
                460.0,
            )
            c.create_line(
                self.engine.player_x,
                self.engine.player_y,
                rx,
                ry,
                fill="#0284c7",
                dash=(4, 4),
            )

        # Top-down opponents
        for bot in self.engine.opponents:
            if not bot.alive:
                continue
            self._draw_topdown_soldier(
                bot.x,
                bot.y,
                bot.angle,
                bot.move_phase,
                weapon_key="rifle",
                is_player=False,
            )
            if bot.hp < ENEMY_MAX_HP:
                ratio = bot.hp / ENEMY_MAX_HP
                c.create_rectangle(
                    bot.x - 16, bot.y - 26, bot.x + 16, bot.y - 22,
                    fill="#0f172a", outline="",
                )
                c.create_rectangle(
                    bot.x - 16, bot.y - 26, bot.x - 16 + 32 * ratio, bot.y - 22,
                    fill=TR_COLOR, outline="",
                )

        # Top-down player
        if self.engine.player_hp > 0:
            self._draw_topdown_soldier(
                self.engine.player_x,
                self.engine.player_y,
                self.engine.player_angle,
                self.engine.player_move_phase,
                weapon_key=self.engine.config.weapon,
                is_player=True,
            )
            if self.engine.is_stealth_walking:
                c.create_oval(
                    self.engine.player_x - 20,
                    self.engine.player_y - 20,
                    self.engine.player_x + 20,
                    self.engine.player_y + 20,
                    outline=ACCENT_WIN,
                    width=1,
                    dash=(3, 3),
                )
            if self.engine.muzzle_flash_timer > 0.0:
                flash_dist = 27.0 if self.engine.config.weapon == "pistol" else 31.0
                mx = self.engine.player_x + math.cos(self.engine.player_angle) * flash_dist
                my = self.engine.player_y + math.sin(self.engine.player_angle) * flash_dist
                c.create_oval(
                    mx - 6, my - 6, mx + 6, my + 6, fill="#fef08a", outline=""
                )
            if self.engine.is_reloading:
                dur = max(0.1, self.engine.weapon_spec.reload_duration)
                prog = 1.0 - (self.engine.reload_timer / dur)
                c.create_rectangle(
                    self.engine.player_x - 18,
                    self.engine.player_y - 28,
                    self.engine.player_x + 18,
                    self.engine.player_y - 23,
                    fill="#0f172a",
                    outline="",
                )
                c.create_rectangle(
                    self.engine.player_x - 18,
                    self.engine.player_y - 28,
                    self.engine.player_x - 18 + 36 * prog,
                    self.engine.player_y - 23,
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

        # Crosshair
        mx, my = self._mouse_x, self._mouse_y
        c.create_oval(mx - 8, my - 8, mx + 8, my + 8, outline=ACCENT_WARN, width=1)
        c.create_line(mx - 12, my, mx - 4, my, fill=ACCENT_WARN)
        c.create_line(mx + 4, my, mx + 12, my, fill=ACCENT_WARN)
        c.create_line(mx, my - 12, mx, my - 4, fill=ACCENT_WARN)
        c.create_line(mx, my + 4, mx, my + 12, fill=ACCENT_WARN)

        # Pause or Round Over overlay
        if not self._menu_open and (self.engine.paused or self.engine.round_over):
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
                    text="Pressione P para continuar ou Esc para Opções",
                    fill=FG_MUTED,
                    font=("Segoe UI", 10),
                )

    def _draw_vision_cone(self) -> None:
        px, py = self.engine.player_x, self.engine.player_y
        base_angle = self.engine.player_angle
        fov = math.radians(66.0)
        steps = 22
        points: list[float] = [px, py]
        for i in range(steps + 1):
            a = base_angle - fov / 2.0 + (fov * i / steps)
            rx, ry = self.engine.cast_ray(px, py, a, 420.0)
            points.extend((rx, ry))
        self.canvas.create_polygon(
            points,
            fill="#38bdf8",
            stipple="gray12",
            outline="",
        )

    def _draw_topdown_soldier(
        self,
        x: float,
        y: float,
        angle: float,
        move_phase: float,
        weapon_key: str,
        is_player: bool,
    ) -> None:
        """Render a detailed top-down tactical character (boots, shoulders, vest, arms, weapon, helmet)."""
        c = self.canvas
        vest_color = "#1d4ed8" if is_player else "#991b1b"
        sleeve_color = "#1e3a8a" if is_player else "#7f1d1d"
        helmet_color = "#0ea5e9" if is_player else "#dc2626"
        visor_color = "#bae6fd" if is_player else "#fca5a5"
        pack_color = "#0f172a" if is_player else "#451a03"
        skin_color = "#eab38f"

        c.create_oval(
            x - 14, y - 10, x + 16, y + 16, fill="#0b1120", outline=""
        )

        step = math.sin(move_phase) * 4.5
        for side, offset in ((-1, step), (1, -step)):
            boot_pts = _rotated_poly(
                x,
                y,
                angle,
                (
                    (offset - 3.0, side * 6.0 - 2.5),
                    (offset + 5.0, side * 6.0 - 2.5),
                    (offset + 5.0, side * 6.0 + 2.5),
                    (offset - 3.0, side * 6.0 + 2.5),
                ),
            )
            c.create_polygon(boot_pts, fill="#020617", outline="")

        pack_pts = _rotated_poly(
            x, y, angle, ((-14.0, -7.0), (-6.0, -7.0), (-6.0, 7.0), (-14.0, 7.0))
        )
        c.create_polygon(pack_pts, fill=pack_color, outline="#020617", width=1)

        torso_pts = _rotated_poly(
            x,
            y,
            angle,
            (
                (-6.5, -14.0),
                (5.5, -13.0),
                (8.0, -8.0),
                (8.0, 8.0),
                (5.5, 13.0),
                (-6.5, 14.0),
                (-8.5, 9.0),
                (-8.5, -9.0),
            ),
        )
        c.create_polygon(torso_pts, fill=vest_color, outline="#020617", width=2)

        right_arm = _rotated_poly(
            x,
            y,
            angle,
            ((1.0, 9.0), (14.0, 4.0), (14.0, 8.5), (1.0, 13.5)),
        )
        left_arm = _rotated_poly(
            x,
            y,
            angle,
            ((1.0, -13.5), (17.0, -4.0), (16.0, 0.5), (0.0, -9.0)),
        )
        c.create_polygon(right_arm, fill=sleeve_color, outline="#020617", width=1)
        c.create_polygon(left_arm, fill=sleeve_color, outline="#020617", width=1)

        for hx_l, hy_l in ((13.5, 4.5), (17.0, -1.0)):
            hx, hy = _rotate_point(x, y, hx_l, hy_l, angle)
            c.create_oval(
                hx - 2.6, hy - 2.6, hx + 2.6, hy + 2.6, fill=skin_color, outline=""
            )

        if weapon_key == "pistol":
            gun_pts = _rotated_poly(
                x, y, angle, ((12.0, -1.5), (24.0, -1.5), (24.0, 2.5), (12.0, 2.5))
            )
            c.create_polygon(gun_pts, fill="#334155", outline="#020617", width=1)
        elif weapon_key == "smg":
            body_pts = _rotated_poly(
                x, y, angle, ((7.0, -2.5), (20.0, -2.0), (20.0, 3.0), (7.0, 3.5))
            )
            barrel_pts = _rotated_poly(
                x, y, angle, ((20.0, -0.8), (27.0, -0.8), (27.0, 1.8), (20.0, 1.8))
            )
            c.create_polygon(body_pts, fill="#334155", outline="#020617", width=1)
            c.create_polygon(barrel_pts, fill="#94a3b8", outline="")
        else:
            stock_pts = _rotated_poly(
                x, y, angle, ((3.0, -1.5), (22.0, -2.0), (22.0, 3.0), (3.0, 3.0))
            )
            barrel_pts = _rotated_poly(
                x, y, angle, ((22.0, -0.8), (30.5, -0.8), (30.5, 1.6), (22.0, 1.6))
            )
            c.create_polygon(stock_pts, fill="#1e293b", outline="#020617", width=1)
            c.create_polygon(barrel_pts, fill="#cbd5e1", outline="")

        c.create_oval(
            x - 8.5, y - 8.5, x + 8.5, y + 8.5,
            fill=helmet_color, outline="#020617", width=2,
        )
        visor_pts = _rotated_poly(
            x, y, angle, ((3.5, -5.5), (8.2, -3.5), (8.2, 3.5), (3.5, 5.5))
        )
        c.create_polygon(visor_pts, fill=visor_color, outline="")


def main() -> None:
    root = tk.Tk()
    CS2DApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
