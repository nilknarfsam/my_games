"""Tkinter graphical interface for Jogo da Cobrinha."""

import tkinter as tk

from snake_game_engine import (
    DOWN,
    GRID_HEIGHT,
    GRID_WIDTH,
    LEFT,
    Point,
    RIGHT,
    SnakeGameEngine,
    UP,
)

# Theme colors
BG_MAIN = "#0f172a"
BG_CARD = "#1e293b"
BG_BOARD = "#111827"
GRID_LINE = "#1f2937"
BORDER_SLATE = "#334155"
FG_PRIMARY = "#f8fafc"
FG_MUTED = "#94a3b8"
PLAYER_HEAD = "#34d399"
PLAYER_BODY = "#10b981"
OBSTACLE_FILL = "#475569"
OBSTACLE_INNER = "#64748b"
OBSTACLE_HAZARD = "#ef4444"
FOOD_COLOR = "#ef4444"
FOOD_BONUS_COLOR = "#facc15"
ACCENT_WARN = "#f59e0b"

CELL_SIZE = 22
CANVAS_W = GRID_WIDTH * CELL_SIZE
CANVAS_H = GRID_HEIGHT * CELL_SIZE


class CobrinhaApp:
    """Main Tkinter window controller for Jogo da Cobrinha."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.engine = SnakeGameEngine()
        self._after_id: str | None = None

        self._configure_window()
        self._build_ui()
        self._bind_controls()
        self._refresh_hud()
        self._render()
        self._schedule_tick()

    def _configure_window(self) -> None:
        self.root.title("Jogo da Cobrinha")
        self.root.geometry("670x700")
        self.root.minsize(650, 670)
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
            text="JOGO DA COBRINHA",
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
            text="Jogando",
            bg=BG_CARD,
            fg=PLAYER_HEAD,
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
        hud.columnconfigure((0, 1, 2, 3), weight=1)

        self.length_label = tk.Label(
            hud,
            text="Tamanho: 3",
            bg=BG_CARD,
            fg=PLAYER_HEAD,
            font=("Consolas", 10, "bold"),
        )
        self.length_label.grid(row=0, column=0, sticky="w")

        self.score_label = tk.Label(
            hud,
            text="Pontos: 0",
            bg=BG_CARD,
            fg=FG_PRIMARY,
            font=("Consolas", 10, "bold"),
        )
        self.score_label.grid(row=0, column=1)

        self.record_label = tk.Label(
            hud,
            text="Recorde: 0",
            bg=BG_CARD,
            fg=FOOD_BONUS_COLOR,
            font=("Consolas", 10, "bold"),
        )
        self.record_label.grid(row=0, column=2)

        self.info_label = tk.Label(
            hud,
            text="Rivais: 2 | Obj: 14",
            bg=BG_CARD,
            fg=FG_MUTED,
            font=("Consolas", 9, "bold"),
        )
        self.info_label.grid(row=0, column=3, sticky="e")

        # Game canvas
        board_holder = tk.Frame(container, bg=BORDER_SLATE, padx=1, pady=1)
        board_holder.pack()

        self.canvas = tk.Canvas(
            board_holder,
            width=CANVAS_W,
            height=CANVAS_H,
            bg=BG_BOARD,
            highlightthickness=0,
        )
        self.canvas.pack()

        # Controls hint
        tk.Label(
            container,
            text="Setas ← → ↑ ↓ ou WASD (mover)  •  P / Espaço (pausar)  •  Enter / R (reiniciar)",
            bg=BG_MAIN,
            fg=FG_MUTED,
            font=("Segoe UI", 8),
        ).pack(pady=(10, 0))

    def _bind_controls(self) -> None:
        self.root.bind("<Up>", lambda _e: self.engine.queue_direction(UP))
        self.root.bind("<Down>", lambda _e: self.engine.queue_direction(DOWN))
        self.root.bind("<Left>", lambda _e: self.engine.queue_direction(LEFT))
        self.root.bind("<Right>", lambda _e: self.engine.queue_direction(RIGHT))
        self.root.bind("<KeyPress-w>", lambda _e: self.engine.queue_direction(UP))
        self.root.bind("<KeyPress-W>", lambda _e: self.engine.queue_direction(UP))
        self.root.bind("<KeyPress-s>", lambda _e: self.engine.queue_direction(DOWN))
        self.root.bind("<KeyPress-S>", lambda _e: self.engine.queue_direction(DOWN))
        self.root.bind("<KeyPress-a>", lambda _e: self.engine.queue_direction(LEFT))
        self.root.bind("<KeyPress-A>", lambda _e: self.engine.queue_direction(LEFT))
        self.root.bind("<KeyPress-d>", lambda _e: self.engine.queue_direction(RIGHT))
        self.root.bind("<KeyPress-D>", lambda _e: self.engine.queue_direction(RIGHT))
        self.root.bind("<KeyPress-p>", lambda _e: self.on_toggle_pause())
        self.root.bind("<KeyPress-P>", lambda _e: self.on_toggle_pause())
        self.root.bind("<space>", lambda _e: self.on_toggle_pause())
        self.root.bind("<Return>", lambda _e: self.on_restart())
        self.root.bind("<KeyPress-r>", lambda _e: self.on_restart())
        self.root.bind("<KeyPress-R>", lambda _e: self.on_restart())

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
        self._refresh_hud()
        self._render()

    def on_restart(self) -> None:
        self.engine.reset()
        self._refresh_hud()
        self._render()

    def _schedule_tick(self) -> None:
        self._after_id = self.root.after(
            self.engine.tick_interval_ms, self._on_tick
        )

    def _on_tick(self) -> None:
        self.engine.step()
        self._refresh_hud()
        self._render()
        self._schedule_tick()

    def _refresh_hud(self) -> None:
        self.length_label.config(text=f"Tamanho: {len(self.engine.player_body)}")
        self.score_label.config(text=f"Pontos: {self.engine.score}")
        self.record_label.config(text=f"Recorde: {self.engine.high_score}")
        active_rivals = sum(1 for r in self.engine.rivals if r.respawn_ticks == 0)
        self.info_label.config(
            text=f"Rivais: {active_rivals} | Obj: {len(self.engine.obstacles)}"
        )

        if self.engine.game_over:
            self.status_badge.config(text="Fim de jogo", fg=OBSTACLE_HAZARD)
            self.pause_btn.config(text="Reiniciar")
        elif self.engine.paused:
            self.status_badge.config(text="Pausado", fg=ACCENT_WARN)
            self.pause_btn.config(text="Retomar (P)")
        else:
            self.status_badge.config(text="Jogando", fg=PLAYER_HEAD)
            self.pause_btn.config(text="Pausar (P)")

    def _render(self) -> None:
        c = self.canvas
        c.delete("all")

        # Subtle grid
        for gx in range(1, GRID_WIDTH):
            x = gx * CELL_SIZE
            c.create_line(x, 0, x, CANVAS_H, fill=GRID_LINE)
        for gy in range(1, GRID_HEIGHT):
            y = gy * CELL_SIZE
            c.create_line(0, y, CANVAS_W, y, fill=GRID_LINE)

        # Obstacles (objects on the field)
        for ox, oy in self.engine.obstacles:
            x1 = ox * CELL_SIZE + 2
            y1 = oy * CELL_SIZE + 2
            x2 = (ox + 1) * CELL_SIZE - 2
            y2 = (oy + 1) * CELL_SIZE - 2
            c.create_rectangle(
                x1, y1, x2, y2, fill=OBSTACLE_FILL, outline=OBSTACLE_INNER, width=2
            )
            c.create_line(x1 + 3, y1 + 3, x2 - 3, y2 - 3, fill=OBSTACLE_HAZARD, width=2)
            c.create_line(x2 - 3, y1 + 3, x1 + 3, y2 - 3, fill=OBSTACLE_HAZARD, width=2)

        # Food
        fx, fy = self.engine.food.pos
        fx1 = fx * CELL_SIZE + 3
        fy1 = fy * CELL_SIZE + 3
        fx2 = (fx + 1) * CELL_SIZE - 3
        fy2 = (fy + 1) * CELL_SIZE - 3
        food_color = (
            FOOD_BONUS_COLOR if self.engine.food.is_bonus else FOOD_COLOR
        )
        c.create_oval(
            fx1, fy1, fx2, fy2, fill=food_color, outline="#fef2f2", width=1
        )

        # Rival snakes
        for rival in self.engine.rivals:
            if rival.respawn_ticks > 0 or not rival.body:
                continue
            self._draw_snake(
                list(rival.body),
                rival.direction,
                rival.color_head,
                rival.color_body,
            )

        # Player snake
        if self.engine.player_body:
            head_c = OBSTACLE_HAZARD if self.engine.game_over else PLAYER_HEAD
            body_c = "#b91c1c" if self.engine.game_over else PLAYER_BODY
            self._draw_snake(
                list(self.engine.player_body),
                self.engine.direction,
                head_c,
                body_c,
            )

        # Overlay for Pause or Game Over
        if self.engine.paused or self.engine.game_over:
            c.create_rectangle(
                CANVAS_W / 2 - 190,
                CANVAS_H / 2 - 75,
                CANVAS_W / 2 + 190,
                CANVAS_H / 2 + 75,
                fill=BG_MAIN,
                outline=BORDER_SLATE,
                width=2,
            )
            if self.engine.game_over:
                c.create_text(
                    CANVAS_W / 2,
                    CANVAS_H / 2 - 34,
                    text="GAME OVER!",
                    fill=OBSTACLE_HAZARD,
                    font=("Segoe UI", 20, "bold"),
                )
                c.create_text(
                    CANVAS_W / 2,
                    CANVAS_H / 2 + 2,
                    text=self.engine.death_reason,
                    fill=FG_PRIMARY,
                    font=("Segoe UI", 11, "bold"),
                )
                c.create_text(
                    CANVAS_W / 2,
                    CANVAS_H / 2 + 36,
                    text=f"Pontos: {self.engine.score}  •  Enter ou R para reiniciar",
                    fill=FG_MUTED,
                    font=("Segoe UI", 9),
                )
            else:
                c.create_text(
                    CANVAS_W / 2,
                    CANVAS_H / 2 - 14,
                    text="PAUSADO",
                    fill=ACCENT_WARN,
                    font=("Segoe UI", 20, "bold"),
                )
                c.create_text(
                    CANVAS_W / 2,
                    CANVAS_H / 2 + 22,
                    text="Pressione P ou Espaço para continuar",
                    fill=FG_MUTED,
                    font=("Segoe UI", 10),
                )

    def _draw_snake(
        self,
        segments: list[Point],
        direction: Point,
        head_color: str,
        body_color: str,
    ) -> None:
        c = self.canvas
        for idx, (sx, sy) in enumerate(segments):
            pad = 2 if idx == 0 else 3
            x1 = sx * CELL_SIZE + pad
            y1 = sy * CELL_SIZE + pad
            x2 = (sx + 1) * CELL_SIZE - pad
            y2 = (sy + 1) * CELL_SIZE - pad
            fill = head_color if idx == 0 else body_color
            c.create_rectangle(x1, y1, x2, y2, fill=fill, outline="#0f172a", width=1)

        # Draw eyes on head
        hx, hy = segments[0]
        cx = hx * CELL_SIZE + CELL_SIZE / 2
        cy = hy * CELL_SIZE + CELL_SIZE / 2
        dx, dy = direction
        perp = (-dy, dx)
        for side in (-1, 1):
            ex = cx + dx * 4 + perp[0] * 4 * side
            ey = cy + dy * 4 + perp[1] * 4 * side
            c.create_oval(ex - 2, ey - 2, ex + 2, ey + 2, fill="#020617", outline="")


def main() -> None:
    root = tk.Tk()
    CobrinhaApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
