"""Tkinter graphical interface for the 3-lane Car Dodge (Jogo de Carro) game."""

from time import perf_counter
import tkinter as tk

from car_game_engine import (
    CAR_HEIGHT,
    CAR_WIDTH,
    CarGameEngine,
    LANE_COUNT,
    LANE_WIDTH,
    ROAD_HEIGHT,
    ROAD_WIDTH,
    SPEED_LEVELS,
    lane_center_x,
)

# Theme colors
BG_MAIN = "#0f172a"
BG_CARD = "#1e293b"
BORDER_SLATE = "#334155"
FG_PRIMARY = "#f8fafc"
FG_MUTED = "#94a3b8"
ACCENT_PLAYER = "#38bdf8"
ACCENT_WIN = "#10b981"
ACCENT_WARN = "#f59e0b"
ACCENT_DANGER = "#ef4444"

GRASS_COLOR = "#14532d"
ROAD_COLOR = "#1e293b"
CURB_RED = "#ef4444"
CURB_WHITE = "#e2e8f0"
LANE_LINE_COLOR = "#cbd5e1"

SHOULDER_WIDTH = 44.0
CANVAS_WIDTH = int(ROAD_WIDTH + SHOULDER_WIDTH * 2)
CANVAS_HEIGHT = int(ROAD_HEIGHT)
FRAME_MS = 16


class CarroApp:
    """Main Tkinter window controller for Jogo de Carro."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.engine = CarGameEngine(starting_level=1)
        self._visual_player_x = lane_center_x(self.engine.player_lane)
        self._visual_traffic_x: dict[int, float] = {}
        self._last_tick = perf_counter()
        self._after_id: str | None = None
        self._level_buttons: dict[int, tk.Button] = {}

        self._configure_window()
        self._build_ui()
        self._bind_controls()
        self._refresh_hud()
        self._render()
        self._schedule_loop()

    def _configure_window(self) -> None:
        self.root.title("Jogo de Carro — 3 Faixas (10 Níveis)")
        self.root.geometry("510x780")
        self.root.minsize(480, 740)
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
            text="JOGO DE CARRO",
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

        self.status_badge = tk.Label(
            header,
            text="Nível 1/10 • Rodovia",
            bg=BG_CARD,
            fg=ACCENT_PLAYER,
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=3,
        )
        self.status_badge.pack(side=tk.RIGHT)

        # HUD metrics
        hud = tk.Frame(
            container,
            bg=BG_CARD,
            highlightbackground=BORDER_SLATE,
            highlightthickness=1,
            padx=14,
            pady=8,
        )
        hud.pack(fill=tk.X, pady=(8, 10))
        hud.columnconfigure((0, 1, 2), weight=1)

        self.score_label = tk.Label(
            hud,
            text="Pontos: 0",
            bg=BG_CARD,
            fg=FG_PRIMARY,
            font=("Consolas", 11, "bold"),
        )
        self.score_label.grid(row=0, column=0, sticky="w")

        self.dodged_label = tk.Label(
            hud,
            text="Desvios: 0",
            bg=BG_CARD,
            fg=ACCENT_WIN,
            font=("Consolas", 11, "bold"),
        )
        self.dodged_label.grid(row=0, column=1)

        self.record_label = tk.Label(
            hud,
            text="Recorde: 0",
            bg=BG_CARD,
            fg=ACCENT_WARN,
            font=("Consolas", 11, "bold"),
        )
        self.record_label.grid(row=0, column=2, sticky="e")

        # Speed level selector (1-10)
        speed_bar = tk.Frame(container, bg=BG_MAIN)
        speed_bar.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            speed_bar,
            text="Nível:",
            bg=BG_MAIN,
            fg=FG_MUTED,
            font=("Segoe UI", 9, "bold"),
        ).pack(side=tk.LEFT, padx=(0, 6))

        for lvl_cfg in SPEED_LEVELS:
            btn = tk.Button(
                speed_bar,
                text=f"{lvl_cfg.level}",
                width=2,
                command=lambda lv=lvl_cfg.level: self.on_select_level(lv),
                bg=BG_CARD,
                fg=FG_PRIMARY,
                relief=tk.FLAT,
                cursor="hand2",
                font=("Segoe UI", 9, "bold"),
                pady=3,
            )
            btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
            self._level_buttons[lvl_cfg.level] = btn

        # Road canvas
        road_holder = tk.Frame(
            container,
            bg=BORDER_SLATE,
            padx=1,
            pady=1,
        )
        road_holder.pack()

        self.canvas = tk.Canvas(
            road_holder,
            width=CANVAS_WIDTH,
            height=CANVAS_HEIGHT,
            bg=ROAD_COLOR,
            highlightthickness=0,
        )
        self.canvas.pack()

        # Controls hint
        tk.Label(
            container,
            text="Setas ← → (faixas)  •  ↑ ↓ (avançar/recuar)  •  1-9 / 0 (nível 1-10)  •  Enter (reiniciar)",
            bg=BG_MAIN,
            fg=FG_MUTED,
            font=("Segoe UI", 8),
        ).pack(pady=(10, 0))

    def _bind_controls(self) -> None:
        self.root.bind("<Left>", lambda _e: self.on_move_left())
        self.root.bind("<Right>", lambda _e: self.on_move_right())
        self.root.bind("<Up>", lambda _e: self.on_move_up())
        self.root.bind("<Down>", lambda _e: self.on_move_down())
        self.root.bind("<KeyPress-a>", lambda _e: self.on_move_left())
        self.root.bind("<KeyPress-d>", lambda _e: self.on_move_right())
        self.root.bind("<KeyPress-p>", lambda _e: self.on_toggle_pause())
        self.root.bind("<KeyPress-P>", lambda _e: self.on_toggle_pause())
        self.root.bind("<space>", lambda _e: self.on_toggle_pause())
        self.root.bind("<Return>", lambda _e: self.on_restart())
        self.root.bind("<KeyPress-r>", lambda _e: self.on_restart())
        self.root.bind("<KeyPress-R>", lambda _e: self.on_restart())
        for lv in range(1, 10):
            self.root.bind(
                f"<KeyPress-{lv}>",
                lambda _e, level=lv: self.on_select_level(level),
            )
        self.root.bind("<KeyPress-0>", lambda _e: self.on_select_level(10))

    def _on_close(self) -> None:
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        self.root.destroy()

    def on_move_left(self) -> None:
        self.engine.move_left()

    def on_move_right(self) -> None:
        self.engine.move_right()

    def on_move_up(self) -> None:
        self.engine.move_up()

    def on_move_down(self) -> None:
        self.engine.move_down()

    def on_toggle_pause(self) -> None:
        if self.engine.game_over:
            self.on_restart()
            return
        self.engine.toggle_pause()
        self._last_tick = perf_counter()
        self._refresh_hud()
        self._render()

    def on_select_level(self, level: int) -> None:
        if self.engine.game_over:
            self.engine.reset(starting_level=level)
            self._visual_player_x = lane_center_x(self.engine.player_lane)
            self._visual_traffic_x.clear()
        else:
            self.engine.set_level(level)
        self._refresh_hud()

    def on_restart(self) -> None:
        self.engine.reset(
            starting_level=self.engine.level if not self.engine.game_over else 1
        )
        self._visual_player_x = lane_center_x(self.engine.player_lane)
        self._visual_traffic_x.clear()
        self._last_tick = perf_counter()
        self._refresh_hud()
        self._render()

    def _schedule_loop(self) -> None:
        self._after_id = self.root.after(FRAME_MS, self._on_tick)

    def _on_tick(self) -> None:
        now = perf_counter()
        dt = min(0.05, max(0.0, now - self._last_tick))
        self._last_tick = now

        self.engine.update(dt)

        target_x = lane_center_x(self.engine.player_lane)
        self._visual_player_x += (target_x - self._visual_player_x) * min(
            1.0, dt * 22.0
        )

        active_ids = set()
        for car in self.engine.traffic:
            active_ids.add(car.car_id)
            car_target_x = lane_center_x(car.lane)
            current_x = self._visual_traffic_x.get(car.car_id, car_target_x)
            self._visual_traffic_x[car.car_id] = current_x + (
                car_target_x - current_x
            ) * min(1.0, dt * 14.0)
        self._visual_traffic_x = {
            cid: vx for cid, vx in self._visual_traffic_x.items() if cid in active_ids
        }

        self._refresh_hud()
        self._render()
        self._schedule_loop()

    def _refresh_hud(self) -> None:
        cfg = self.engine.speed_config
        self.score_label.config(text=f"Pontos: {self.engine.score}")
        self.dodged_label.config(text=f"Desvios: {self.engine.dodged}")
        self.record_label.config(text=f"Recorde: {self.engine.high_score}")

        if self.engine.game_over:
            self.status_badge.config(
                text="Colisão! Fim de jogo", fg=ACCENT_DANGER
            )
            self.pause_btn.config(text="Reiniciar")
        elif self.engine.paused:
            self.status_badge.config(text="Pausado", fg=ACCENT_WARN)
            self.pause_btn.config(text="Retomar (P)")
        else:
            self.status_badge.config(
                text=f"Nível {cfg.level}/10 • {cfg.name}", fg=ACCENT_PLAYER
            )
            self.pause_btn.config(text="Pausar (P)")

        for lv, btn in self._level_buttons.items():
            if lv == self.engine.level:
                btn.config(bg=ACCENT_PLAYER, fg=BG_MAIN)
            else:
                btn.config(bg=BG_CARD, fg=FG_PRIMARY)

    def _render(self) -> None:
        c = self.canvas
        c.delete("all")

        # Shoulders (grass)
        c.create_rectangle(
            0, 0, SHOULDER_WIDTH, CANVAS_HEIGHT, fill=GRASS_COLOR, outline=""
        )
        c.create_rectangle(
            CANVAS_WIDTH - SHOULDER_WIDTH,
            0,
            CANVAS_WIDTH,
            CANVAS_HEIGHT,
            fill=GRASS_COLOR,
            outline="",
        )

        # Asphalt road
        road_left = SHOULDER_WIDTH
        road_right = CANVAS_WIDTH - SHOULDER_WIDTH
        c.create_rectangle(
            road_left, 0, road_right, CANVAS_HEIGHT, fill=ROAD_COLOR, outline=""
        )

        # Scrolling racing curbs
        scroll = self.engine.road_scroll_y
        curb_w = 8.0
        seg_h = 40.0
        y = -seg_h + (scroll % (seg_h * 2))
        idx = 0
        while y < CANVAS_HEIGHT:
            color = CURB_RED if idx % 2 == 0 else CURB_WHITE
            c.create_rectangle(
                road_left - curb_w, y, road_left, y + seg_h, fill=color, outline=""
            )
            c.create_rectangle(
                road_right, y, road_right + curb_w, y + seg_h, fill=color, outline=""
            )
            y += seg_h
            idx += 1

        # Scrolling dashed lane dividers (separating 3 lanes)
        dash_len = 42.0
        gap_len = 38.0
        period = dash_len + gap_len
        for divider in range(1, LANE_COUNT):
            x = road_left + divider * LANE_WIDTH
            dy = -period + (scroll % period)
            while dy < CANVAS_HEIGHT:
                c.create_rectangle(
                    x - 2,
                    dy,
                    x + 2,
                    dy + dash_len,
                    fill=LANE_LINE_COLOR,
                    outline="",
                )
                dy += period

        # Draw traffic cars (smoothly interpolated X + varied vehicle styles)
        for car in self.engine.traffic:
            vx = self._visual_traffic_x.get(car.car_id, lane_center_x(car.lane))
            cx = road_left + vx
            self._draw_car(cx, car.y, car.color, style=car.style, is_player=False)

        # Draw player car
        px = road_left + self._visual_player_x
        self._draw_car(
            px,
            self.engine.player_y,
            ACCENT_DANGER if self.engine.game_over else ACCENT_PLAYER,
            style="esportivo",
            is_player=True,
        )

        # Overlay for Pause or Game Over
        if self.engine.paused or self.engine.game_over:
            c.create_rectangle(
                24,
                CANVAS_HEIGHT / 2 - 80,
                CANVAS_WIDTH - 24,
                CANVAS_HEIGHT / 2 + 80,
                fill=BG_MAIN,
                outline=BORDER_SLATE,
                width=2,
            )
            if self.engine.game_over:
                c.create_text(
                    CANVAS_WIDTH / 2,
                    CANVAS_HEIGHT / 2 - 36,
                    text="BATEU!",
                    fill=ACCENT_DANGER,
                    font=("Segoe UI", 22, "bold"),
                )
                c.create_text(
                    CANVAS_WIDTH / 2,
                    CANVAS_HEIGHT / 2 + 2,
                    text=f"Pontuação: {self.engine.score}   •   Desvios: {self.engine.dodged}",
                    fill=FG_PRIMARY,
                    font=("Segoe UI", 11, "bold"),
                )
                c.create_text(
                    CANVAS_WIDTH / 2,
                    CANVAS_HEIGHT / 2 + 38,
                    text="Pressione Enter ou R para jogar novamente",
                    fill=FG_MUTED,
                    font=("Segoe UI", 10),
                )
            else:
                c.create_text(
                    CANVAS_WIDTH / 2,
                    CANVAS_HEIGHT / 2 - 14,
                    text="PAUSADO",
                    fill=ACCENT_WARN,
                    font=("Segoe UI", 20, "bold"),
                )
                c.create_text(
                    CANVAS_WIDTH / 2,
                    CANVAS_HEIGHT / 2 + 22,
                    text="Pressione P ou Espaço para continuar",
                    fill=FG_MUTED,
                    font=("Segoe UI", 10),
                )

    def _draw_car(
        self,
        center_x: float,
        top_y: float,
        body_color: str,
        style: str,
        is_player: bool,
    ) -> None:
        c = self.canvas
        x1 = center_x - CAR_WIDTH / 2.0
        x2 = center_x + CAR_WIDTH / 2.0
        y1 = top_y
        y2 = top_y + CAR_HEIGHT

        # Wheels
        wheel_w = 5
        wheel_h = 16
        for wy in (y1 + 10, y2 - 10 - wheel_h):
            c.create_rectangle(
                x1 - 3, wy, x1 + wheel_w - 3, wy + wheel_h, fill="#020617", outline=""
            )
            c.create_rectangle(
                x2 - wheel_w + 3, wy, x2 + 3, wy + wheel_h, fill="#020617", outline=""
            )

        # Car body
        c.create_rectangle(
            x1, y1, x2, y2, fill=body_color, outline="#0f172a", width=2
        )

        # Style-specific details
        if style == "esportivo":
            c.create_rectangle(
                center_x - 3, y1 + 2, center_x + 3, y2 - 2, fill="#f8fafc", outline=""
            )
        elif style == "taxi":
            c.create_rectangle(
                x1 + 12, y1 + 34, x2 - 12, y1 + 44, fill="#facc15", outline="#0f172a"
            )
        elif style == "pickup":
            c.create_rectangle(
                x1 + 6, y1 + 6, x2 - 6, y1 + 28, fill="#334155", outline=""
            )
        elif style == "van":
            c.create_rectangle(
                x1 + 6, y1 + 12, x2 - 6, y2 - 22, fill="#0f172a", outline=""
            )

        if style != "van":
            c.create_rectangle(
                x1 + 7, y1 + 22, x2 - 7, y2 - 20, fill="#0f172a", outline=""
            )

        # Windshield & headlights
        if is_player:
            c.create_rectangle(
                x1 + 9, y1 + 14, x2 - 9, y1 + 28, fill="#bae6fd", outline=""
            )
            c.create_rectangle(
                x1 + 5, y1 + 1, x1 + 13, y1 + 5, fill="#fef08a", outline=""
            )
            c.create_rectangle(
                x2 - 13, y1 + 1, x2 - 5, y1 + 5, fill="#fef08a", outline=""
            )
        else:
            c.create_rectangle(
                x1 + 9, y2 - 28, x2 - 9, y2 - 14, fill="#cbd5e1", outline=""
            )
            c.create_rectangle(
                x1 + 5, y2 - 5, x1 + 13, y2 - 1, fill="#fef08a", outline=""
            )
            c.create_rectangle(
                x2 - 13, y2 - 5, x2 - 5, y2 - 1, fill="#fef08a", outline=""
            )


def main() -> None:
    root = tk.Tk()
    CarroApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
