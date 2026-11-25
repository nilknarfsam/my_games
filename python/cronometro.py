"""Tkinter graphical interface for the stopwatch application."""

import tkinter as tk
from tkinter import ttk

from stopwatch_engine import LapRecord, StopwatchEngine, format_time

# Color palette (modern dark slate theme)
BG_MAIN = "#0f172a"
BG_CARD = "#1e293b"
BG_ROW_ALT = "#263348"
FG_PRIMARY = "#f8fafc"
FG_MUTED = "#94a3b8"
ACCENT_START = "#10b981"
ACCENT_START_HOVER = "#059669"
ACCENT_PAUSE = "#f59e0b"
ACCENT_PAUSE_HOVER = "#d97706"
ACCENT_LAP = "#38bdf8"
ACCENT_LAP_HOVER = "#0284c7"
ACCENT_RESET = "#ef4444"
ACCENT_RESET_HOVER = "#dc2626"
BTN_DISABLED_BG = "#334155"
BTN_DISABLED_FG = "#64748b"
FASTEST_COLOR = "#34d399"
SLOWEST_COLOR = "#fb7185"

REFRESH_INTERVAL_MS = 20


class CronometroApp:
    """Main window controller for the stopwatch GUI."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.engine = StopwatchEngine()
        self._after_id: str | None = None

        self._configure_window()
        self._configure_styles()
        self._build_ui()
        self._bind_shortcuts()
        self._refresh_view()

    def _configure_window(self) -> None:
        self.root.title("Cronômetro")
        self.root.geometry("480x600")
        self.root.minsize(400, 480)
        self.root.configure(bg=BG_MAIN)

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "Laps.Treeview",
            background=BG_CARD,
            foreground=FG_PRIMARY,
            fieldbackground=BG_CARD,
            borderwidth=0,
            rowheight=30,
            font=("Consolas", 10),
        )
        style.configure(
            "Laps.Treeview.Heading",
            background=BG_MAIN,
            foreground=FG_MUTED,
            relief="flat",
            font=("Segoe UI", 9, "bold"),
        )
        style.map(
            "Laps.Treeview",
            background=[("selected", "#334155")],
            foreground=[("selected", FG_PRIMARY)],
        )

    def _build_ui(self) -> None:
        container = tk.Frame(self.root, bg=BG_MAIN, padx=24, pady=20)
        container.pack(fill=tk.BOTH, expand=True)

        # Header + Status badge
        header = tk.Frame(container, bg=BG_MAIN)
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text="CRONÔMETRO",
            bg=BG_MAIN,
            fg=FG_MUTED,
            font=("Segoe UI", 10, "bold"),
        ).pack(side=tk.LEFT)

        self.status_label = tk.Label(
            header,
            text="Pronto",
            bg=BG_CARD,
            fg=FG_MUTED,
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=3,
        )
        self.status_label.pack(side=tk.RIGHT)

        # Display card
        display_card = tk.Frame(
            container,
            bg=BG_CARD,
            highlightbackground="#334155",
            highlightthickness=1,
            padx=20,
            pady=28,
        )
        display_card.pack(fill=tk.X, pady=(14, 18))

        time_row = tk.Frame(display_card, bg=BG_CARD)
        time_row.pack()

        self.main_time_label = tk.Label(
            time_row,
            text="00:00:00",
            bg=BG_CARD,
            fg=FG_PRIMARY,
            font=("Consolas", 38, "bold"),
        )
        self.main_time_label.pack(side=tk.LEFT)

        self.centi_label = tk.Label(
            time_row,
            text=".00",
            bg=BG_CARD,
            fg=ACCENT_LAP,
            font=("Consolas", 24, "bold"),
        )
        self.centi_label.pack(side=tk.LEFT, anchor="s", pady=(0, 5))

        self.current_lap_label = tk.Label(
            display_card,
            text="Volta atual: 00:00:00.00",
            bg=BG_CARD,
            fg=FG_MUTED,
            font=("Consolas", 10),
        )
        self.current_lap_label.pack(pady=(10, 0))

        # Action buttons
        btn_row = tk.Frame(container, bg=BG_MAIN)
        btn_row.pack(fill=tk.X, pady=(0, 18))
        btn_row.columnconfigure((0, 1, 2), weight=1, uniform="btns")

        self.start_btn = tk.Button(
            btn_row,
            text="Iniciar",
            command=self.on_toggle,
            bg=ACCENT_START,
            fg=BG_MAIN,
            activebackground=ACCENT_START_HOVER,
            activeforeground=BG_MAIN,
            relief=tk.FLAT,
            cursor="hand2",
            font=("Segoe UI", 11, "bold"),
            pady=10,
        )
        self.start_btn.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.lap_btn = tk.Button(
            btn_row,
            text="Volta",
            command=self.on_lap,
            bg=BTN_DISABLED_BG,
            fg=BTN_DISABLED_FG,
            activebackground=ACCENT_LAP_HOVER,
            activeforeground=BG_MAIN,
            relief=tk.FLAT,
            cursor="hand2",
            font=("Segoe UI", 11, "bold"),
            pady=10,
            state=tk.DISABLED,
        )
        self.lap_btn.grid(row=0, column=1, sticky="ew", padx=6)

        self.reset_btn = tk.Button(
            btn_row,
            text="Zerar",
            command=self.on_reset,
            bg=BTN_DISABLED_BG,
            fg=BTN_DISABLED_FG,
            activebackground=ACCENT_RESET_HOVER,
            activeforeground=FG_PRIMARY,
            relief=tk.FLAT,
            cursor="hand2",
            font=("Segoe UI", 11, "bold"),
            pady=10,
            state=tk.DISABLED,
        )
        self.reset_btn.grid(row=0, column=2, sticky="ew", padx=(6, 0))

        # Laps list section
        laps_header = tk.Frame(container, bg=BG_MAIN)
        laps_header.pack(fill=tk.X, pady=(0, 6))

        tk.Label(
            laps_header,
            text="VOLTAS REGISTRADAS",
            bg=BG_MAIN,
            fg=FG_MUTED,
            font=("Segoe UI", 9, "bold"),
        ).pack(side=tk.LEFT)

        self.laps_count_label = tk.Label(
            laps_header,
            text="0 voltas",
            bg=BG_MAIN,
            fg=FG_MUTED,
            font=("Segoe UI", 9),
        )
        self.laps_count_label.pack(side=tk.RIGHT)

        table_frame = tk.Frame(
            container,
            bg=BG_CARD,
            highlightbackground="#334155",
            highlightthickness=1,
        )
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("volta", "parcial", "total")
        self.laps_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            style="Laps.Treeview",
            selectmode="browse",
        )
        self.laps_tree.heading("volta", text="#", anchor=tk.CENTER)
        self.laps_tree.heading("parcial", text="Tempo da Volta", anchor=tk.CENTER)
        self.laps_tree.heading("total", text="Tempo Total", anchor=tk.CENTER)

        self.laps_tree.column("volta", width=60, anchor=tk.CENTER, stretch=False)
        self.laps_tree.column("parcial", width=160, anchor=tk.CENTER)
        self.laps_tree.column("total", width=160, anchor=tk.CENTER)

        self.laps_tree.tag_configure("fastest", foreground=FASTEST_COLOR)
        self.laps_tree.tag_configure("slowest", foreground=SLOWEST_COLOR)
        self.laps_tree.tag_configure("alt", background=BG_ROW_ALT)

        scrollbar = ttk.Scrollbar(
            table_frame, orient=tk.VERTICAL, command=self.laps_tree.yview
        )
        self.laps_tree.configure(yscrollcommand=scrollbar.set)

        self.laps_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Keyboard shortcuts footer
        tk.Label(
            container,
            text="Atalhos: Espaço (Iniciar/Pausar)  •  V (Volta)  •  R (Zerar)",
            bg=BG_MAIN,
            fg=FG_MUTED,
            font=("Segoe UI", 8),
        ).pack(pady=(12, 0))

    def _bind_shortcuts(self) -> None:
        self.root.bind("<space>", lambda _e: self.on_toggle())
        self.root.bind("<KeyPress-v>", lambda _e: self.on_lap())
        self.root.bind("<KeyPress-V>", lambda _e: self.on_lap())
        self.root.bind("<KeyPress-r>", lambda _e: self.on_reset())
        self.root.bind("<KeyPress-R>", lambda _e: self.on_reset())

    def on_toggle(self) -> None:
        running = self.engine.toggle()
        if running:
            self._schedule_tick()
        else:
            self._cancel_tick()
        self._refresh_view()

    def on_lap(self) -> None:
        if not self.engine.is_running and self.engine.elapsed_seconds() == 0.0:
            return
        self.engine.lap()
        self._rebuild_laps_table()
        self._refresh_view()

    def on_reset(self) -> None:
        self._cancel_tick()
        self.engine.reset()
        self._rebuild_laps_table()
        self._refresh_view()

    def _schedule_tick(self) -> None:
        if self._after_id is None:
            self._after_id = self.root.after(REFRESH_INTERVAL_MS, self._on_tick)

    def _cancel_tick(self) -> None:
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
            self._after_id = None

    def _on_tick(self) -> None:
        self._after_id = None
        self._update_time_labels()
        if self.engine.is_running:
            self._schedule_tick()

    def _update_time_labels(self) -> None:
        elapsed = self.engine.elapsed_seconds()
        formatted = format_time(elapsed)
        hms, centi = formatted.split(".")
        self.main_time_label.config(text=hms)
        self.centi_label.config(text=f".{centi}")

        laps = self.engine.laps
        last_total = laps[-1].total_seconds if laps else 0.0
        current_lap = max(0.0, elapsed - last_total)
        self.current_lap_label.config(text=f"Volta atual: {format_time(current_lap)}")

    def _refresh_view(self) -> None:
        self._update_time_labels()
        running = self.engine.is_running
        elapsed = self.engine.elapsed_seconds()

        if running:
            self.status_label.config(text="Em execução", fg=ACCENT_START)
            self.start_btn.config(
                text="Pausar",
                bg=ACCENT_PAUSE,
                fg=BG_MAIN,
                activebackground=ACCENT_PAUSE_HOVER,
            )
        elif elapsed > 0.0:
            self.status_label.config(text="Pausado", fg=ACCENT_PAUSE)
            self.start_btn.config(
                text="Retomar",
                bg=ACCENT_START,
                fg=BG_MAIN,
                activebackground=ACCENT_START_HOVER,
            )
        else:
            self.status_label.config(text="Pronto", fg=FG_MUTED)
            self.start_btn.config(
                text="Iniciar",
                bg=ACCENT_START,
                fg=BG_MAIN,
                activebackground=ACCENT_START_HOVER,
            )

        can_lap = running or elapsed > 0.0
        self._set_button_enabled(self.lap_btn, can_lap, ACCENT_LAP, BG_MAIN)

        can_reset = (not running and elapsed > 0.0) or running or bool(self.engine.laps)
        self._set_button_enabled(self.reset_btn, can_reset, ACCENT_RESET, FG_PRIMARY)

        count = len(self.engine.laps)
        suffix = "volta" if count == 1 else "voltas"
        self.laps_count_label.config(text=f"{count} {suffix}")

    @staticmethod
    def _set_button_enabled(
        button: tk.Button, enabled: bool, active_bg: str, active_fg: str
    ) -> None:
        if enabled:
            button.config(state=tk.NORMAL, bg=active_bg, fg=active_fg)
        else:
            button.config(
                state=tk.DISABLED, bg=BTN_DISABLED_BG, fg=BTN_DISABLED_FG
            )

    def _rebuild_laps_table(self) -> None:
        self.laps_tree.delete(*self.laps_tree.get_children())
        laps = self.engine.laps
        if not laps:
            return

        fastest_idx, slowest_idx = self._extremes_indices(laps)
        # Show most recent lap at the top
        for pos, lap in enumerate(reversed(laps)):
            tags: list[str] = []
            if pos % 2 == 1:
                tags.append("alt")
            if lap.index == fastest_idx:
                tags.append("fastest")
            elif lap.index == slowest_idx:
                tags.append("slowest")

            self.laps_tree.insert(
                "",
                tk.END,
                values=(
                    f"{lap.index:02d}",
                    format_time(lap.lap_seconds),
                    format_time(lap.total_seconds),
                ),
                tags=tuple(tags),
            )

    @staticmethod
    def _extremes_indices(laps: tuple[LapRecord, ...]) -> tuple[int | None, int | None]:
        if len(laps) < 2:
            return None, None
        fastest = min(laps, key=lambda item: item.lap_seconds)
        slowest = max(laps, key=lambda item: item.lap_seconds)
        if fastest.lap_seconds == slowest.lap_seconds:
            return None, None
        return fastest.index, slowest.index


def main() -> None:
    root = tk.Tk()
    CronometroApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
