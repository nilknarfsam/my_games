"""Tkinter graphical interface for Jogo da Forca with 20s turn timer."""

import math
from time import monotonic
import tkinter as tk
from typing import Callable

from hangman_engine import DEFAULT_TURN_SECONDS, GuessOutcome, HangmanEngine

# Color palette (modern dark slate theme)
BG_MAIN = "#0f172a"
BG_CARD = "#1e293b"
BORDER_SLATE = "#334155"
FG_PRIMARY = "#f8fafc"
FG_MUTED = "#94a3b8"
ACCENT_INFO = "#38bdf8"
ACCENT_WIN = "#10b981"
ACCENT_LOSS = "#ef4444"
ACCENT_WARN = "#f59e0b"
KEY_IDLE_BG = "#334155"
KEY_HIT_BG = "#065f46"
KEY_HIT_FG = "#6ee7b7"
KEY_MISS_BG = "#7f1d1d"
KEY_MISS_FG = "#fca5a5"
GALLOWS_COLOR = "#cbd5e1"
BODY_COLOR = "#f8fafc"

TIMER_POLL_MS = 100

KEYBOARD_ROWS = (
    "QWERTYUIOP",
    "ASDFGHJKL",
    "ZXCVBNM",
)


class ForcaApp:
    """Main Tkinter window controller for Jogo da Forca."""

    def __init__(
        self,
        root: tk.Tk,
        turn_seconds: float = DEFAULT_TURN_SECONDS,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self.root = root
        self.turn_seconds = turn_seconds
        self._clock = clock
        self.engine = HangmanEngine()
        self.wins = 0
        self.losses = 0
        self._round_scored = False
        self._custom_status_msg: tuple[str, str] | None = None
        self._turn_deadline = 0.0
        self._timer_after_id: str | None = None
        self._key_buttons: dict[str, tk.Button] = {}

        self._configure_window()
        self._build_ui()
        self._bind_shortcuts()
        self._reset_turn_timer()
        self._refresh_view()

    def _configure_window(self) -> None:
        self.root.title("Jogo da Forca")
        self.root.geometry("640x740")
        self.root.minsize(560, 660)
        self.root.configure(bg=BG_MAIN)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        container = tk.Frame(self.root, bg=BG_MAIN, padx=24, pady=18)
        container.pack(fill=tk.BOTH, expand=True)

        # Header + Status badge
        header = tk.Frame(container, bg=BG_MAIN)
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text="JOGO DA FORCA",
            bg=BG_MAIN,
            fg=FG_MUTED,
            font=("Segoe UI", 10, "bold"),
        ).pack(side=tk.LEFT)

        self.status_label = tk.Label(
            header,
            text="Jogando",
            bg=BG_CARD,
            fg=ACCENT_INFO,
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=3,
        )
        self.status_label.pack(side=tk.RIGHT)

        # Score, Hint & Countdown bar
        info_bar = tk.Frame(container, bg=BG_MAIN)
        info_bar.pack(fill=tk.X, pady=(10, 10))

        self.hint_label = tk.Label(
            info_bar,
            text="Dica: —",
            bg=BG_CARD,
            fg=ACCENT_INFO,
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=5,
        )
        self.hint_label.pack(side=tk.LEFT)

        self.timer_label = tk.Label(
            info_bar,
            text=f"Tempo: {int(self.turn_seconds):02d}s",
            bg=BG_CARD,
            fg=ACCENT_INFO,
            font=("Consolas", 11, "bold"),
            padx=12,
            pady=5,
        )
        self.timer_label.pack(side=tk.LEFT, padx=(10, 0))

        self.score_label = tk.Label(
            info_bar,
            text="Vitórias: 0  |  Derrotas: 0",
            bg=BG_MAIN,
            fg=FG_MUTED,
            font=("Segoe UI", 9, "bold"),
        )
        self.score_label.pack(side=tk.RIGHT)

        # Countdown progress bar
        self.timer_bar_canvas = tk.Canvas(
            container,
            height=6,
            bg=BG_CARD,
            highlightthickness=0,
        )
        self.timer_bar_canvas.pack(fill=tk.X, pady=(0, 10))
        self.timer_bar_canvas.bind(
            "<Configure>", lambda _e: self._update_timer_display()
        )

        # Main stage card (Canvas + Word)
        stage_card = tk.Frame(
            container,
            bg=BG_CARD,
            highlightbackground=BORDER_SLATE,
            highlightthickness=1,
            padx=18,
            pady=16,
        )
        stage_card.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            stage_card,
            width=260,
            height=210,
            bg=BG_CARD,
            highlightthickness=0,
        )
        self.canvas.pack(pady=(0, 8))

        self.word_label = tk.Label(
            stage_card,
            text="",
            bg=BG_CARD,
            fg=FG_PRIMARY,
            font=("Consolas", 24, "bold"),
        )
        self.word_label.pack(pady=(4, 8))

        self.attempts_label = tk.Label(
            stage_card,
            text="",
            bg=BG_CARD,
            fg=FG_MUTED,
            font=("Segoe UI", 10),
        )
        self.attempts_label.pack()

        self.message_label = tk.Label(
            stage_card,
            text="",
            bg=BG_CARD,
            fg=FG_MUTED,
            font=("Segoe UI", 10, "bold"),
        )
        self.message_label.pack(pady=(8, 0))

        # On-screen keyboard
        kb_frame = tk.Frame(container, bg=BG_MAIN, pady=12)
        kb_frame.pack(fill=tk.X)

        for row_letters in KEYBOARD_ROWS:
            row_frame = tk.Frame(kb_frame, bg=BG_MAIN)
            row_frame.pack(pady=3)
            for ch in row_letters:
                btn = tk.Button(
                    row_frame,
                    text=ch,
                    width=3,
                    command=lambda letter=ch: self.on_guess(letter),
                    bg=KEY_IDLE_BG,
                    fg=FG_PRIMARY,
                    activebackground="#475569",
                    activeforeground=FG_PRIMARY,
                    relief=tk.FLAT,
                    cursor="hand2",
                    font=("Segoe UI", 10, "bold"),
                    pady=6,
                )
                btn.pack(side=tk.LEFT, padx=3)
                self._key_buttons[ch] = btn

        # Action bar
        actions = tk.Frame(container, bg=BG_MAIN)
        actions.pack(fill=tk.X)

        self.new_game_btn = tk.Button(
            actions,
            text="Nova Palavra (Enter)",
            command=self.on_new_game,
            bg=ACCENT_INFO,
            fg=BG_MAIN,
            activebackground="#0284c7",
            activeforeground=BG_MAIN,
            relief=tk.FLAT,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=18,
            pady=9,
        )
        self.new_game_btn.pack()

    def _bind_shortcuts(self) -> None:
        self.root.bind("<KeyPress>", self._on_key_press)
        self.root.bind("<Return>", lambda _e: self.on_new_game())

    def _on_key_press(self, event: tk.Event) -> None:
        if not event.char:
            return
        try:
            self.on_guess(event.char)
        except ValueError:
            pass

    def _on_close(self) -> None:
        self._cancel_timer()
        self.root.destroy()

    def _remaining_turn_seconds(self) -> float:
        if self.engine.is_over:
            return 0.0
        return max(0.0, self._turn_deadline - self._clock())

    def _reset_turn_timer(self) -> None:
        self._cancel_timer()
        if not self.engine.is_over:
            self._turn_deadline = self._clock() + self.turn_seconds
            self._schedule_timer()

    def _schedule_timer(self) -> None:
        if self._timer_after_id is None and not self.engine.is_over:
            self._timer_after_id = self.root.after(
                TIMER_POLL_MS, self._on_timer_tick
            )

    def _cancel_timer(self) -> None:
        if self._timer_after_id is not None:
            self.root.after_cancel(self._timer_after_id)
            self._timer_after_id = None

    def _on_timer_tick(self) -> None:
        self._timer_after_id = None
        if self.engine.is_over:
            self._update_timer_display()
            return

        if self._remaining_turn_seconds() <= 0.0:
            self.on_timeout()
            return

        self._update_timer_display()
        self._schedule_timer()

    def on_timeout(self) -> None:
        """Handle an expired 20-second turn as an error."""
        outcome = self.engine.record_timeout()
        if outcome == GuessOutcome.GAME_OVER:
            self._cancel_timer()
            return

        if self.engine.is_over:
            self._score_round_if_needed()
            self._cancel_timer()
            self._custom_status_msg = None
        else:
            self._custom_status_msg = (
                f"Tempo esgotado ({int(self.turn_seconds)}s)! Contou como erro — próximo turno iniciado.",
                ACCENT_WARN,
            )
            self._reset_turn_timer()

        self._refresh_view()

    def on_guess(self, raw_letter: str) -> None:
        outcome = self.engine.guess(raw_letter)
        if outcome in (GuessOutcome.ALREADY_GUESSED, GuessOutcome.GAME_OVER):
            return

        self._custom_status_msg = None
        if self.engine.is_over:
            self._score_round_if_needed()
            self._cancel_timer()
        else:
            self._reset_turn_timer()

        self._refresh_view()

    def on_new_game(self) -> None:
        self.engine.new_game()
        self._round_scored = False
        self._custom_status_msg = None
        self._reset_turn_timer()
        self._refresh_view()

    def _score_round_if_needed(self) -> None:
        if self._round_scored:
            return
        self._round_scored = True
        if self.engine.is_won:
            self.wins += 1
        elif self.engine.is_lost:
            self.losses += 1

    def _update_timer_display(self) -> None:
        width = max(1, self.timer_bar_canvas.winfo_width())
        self.timer_bar_canvas.delete("all")

        if self.engine.is_over:
            self.timer_label.config(text="Tempo: --", fg=FG_MUTED)
            return

        remaining = self._remaining_turn_seconds()
        secs_int = int(math.ceil(remaining))
        ratio = max(0.0, min(1.0, remaining / self.turn_seconds))

        if secs_int <= 5:
            color = ACCENT_LOSS
        elif secs_int <= 10:
            color = ACCENT_WARN
        else:
            color = ACCENT_INFO

        self.timer_label.config(text=f"Tempo: {secs_int:02d}s", fg=color)
        fill_width = int(width * ratio)
        if fill_width > 0:
            self.timer_bar_canvas.create_rectangle(
                0, 0, fill_width, 6, fill=color, outline=""
            )

    def _refresh_view(self) -> None:
        self.hint_label.config(text=f"Dica: {self.engine.hint}")
        self.score_label.config(
            text=f"Vitórias: {self.wins}  |  Derrotas: {self.losses}"
        )

        if self.engine.is_lost:
            self.word_label.config(
                text=" ".join(self.engine.word), fg=ACCENT_LOSS
            )
        elif self.engine.is_won:
            self.word_label.config(
                text=self.engine.masked_word(), fg=ACCENT_WIN
            )
        else:
            self.word_label.config(
                text=self.engine.masked_word(), fg=FG_PRIMARY
            )

        wrong = ", ".join(self.engine.wrong_letters) or "nenhuma"
        timeout_info = (
            f" ({self.engine.timeouts} por tempo)"
            if self.engine.timeouts > 0
            else ""
        )
        self.attempts_label.config(
            text=(
                f"Erros: {self.engine.errors}/{self.engine.max_errors}"
                f"{timeout_info}   •   Letras erradas: {wrong}"
            )
        )

        if self.engine.is_won:
            self.status_label.config(text="Você venceu!", fg=ACCENT_WIN)
            self.message_label.config(
                text="Parabéns! Pressione Enter ou clique em Nova Palavra para jogar novamente.",
                fg=ACCENT_WIN,
            )
        elif self.engine.is_lost:
            self.status_label.config(text="Fim de jogo", fg=ACCENT_LOSS)
            self.message_label.config(
                text=f"Você perdeu! A palavra era {self.engine.word}.",
                fg=ACCENT_LOSS,
            )
        else:
            self.status_label.config(text="Jogando", fg=ACCENT_INFO)
            if self._custom_status_msg is not None:
                msg_text, msg_color = self._custom_status_msg
                self.message_label.config(text=msg_text, fg=msg_color)
            else:
                self.message_label.config(
                    text=f"Você tem {int(self.turn_seconds)}s por letra! Clique ou digite no teclado.",
                    fg=FG_MUTED,
                )

        self._update_timer_display()
        self._refresh_keyboard()
        self._draw_gallows()

    def _refresh_keyboard(self) -> None:
        guessed = self.engine.guessed_letters
        wrong = set(self.engine.wrong_letters)
        game_over = self.engine.is_over

        for ch, btn in self._key_buttons.items():
            if ch in wrong:
                btn.config(
                    state=tk.DISABLED,
                    bg=KEY_MISS_BG,
                    disabledforeground=KEY_MISS_FG,
                )
            elif ch in guessed:
                btn.config(
                    state=tk.DISABLED,
                    bg=KEY_HIT_BG,
                    disabledforeground=KEY_HIT_FG,
                )
            elif game_over:
                btn.config(
                    state=tk.DISABLED,
                    bg=KEY_IDLE_BG,
                    disabledforeground=FG_MUTED,
                )
            else:
                btn.config(
                    state=tk.NORMAL,
                    bg=KEY_IDLE_BG,
                    fg=FG_PRIMARY,
                )

    def _draw_gallows(self) -> None:
        c = self.canvas
        c.delete("all")

        # Gallows structure
        c.create_line(40, 195, 140, 195, width=4, fill=GALLOWS_COLOR)
        c.create_line(75, 195, 75, 20, width=4, fill=GALLOWS_COLOR)
        c.create_line(75, 20, 175, 20, width=4, fill=GALLOWS_COLOR)
        c.create_line(75, 50, 106, 20, width=3, fill=GALLOWS_COLOR)
        c.create_line(175, 20, 175, 44, width=3, fill=ACCENT_WARN)

        errors = self.engine.errors
        body_color = ACCENT_LOSS if self.engine.is_lost else BODY_COLOR

        if errors >= 1:  # Head
            c.create_oval(
                157, 44, 193, 80, width=3, outline=body_color
            )
            if self.engine.is_lost:
                c.create_line(166, 56, 172, 62, width=2, fill=ACCENT_LOSS)
                c.create_line(172, 56, 166, 62, width=2, fill=ACCENT_LOSS)
                c.create_line(178, 56, 184, 62, width=2, fill=ACCENT_LOSS)
                c.create_line(184, 56, 178, 62, width=2, fill=ACCENT_LOSS)
        if errors >= 2:  # Torso
            c.create_line(175, 80, 175, 136, width=3, fill=body_color)
        if errors >= 3:  # Left arm
            c.create_line(175, 92, 148, 118, width=3, fill=body_color)
        if errors >= 4:  # Right arm
            c.create_line(175, 92, 202, 118, width=3, fill=body_color)
        if errors >= 5:  # Left leg
            c.create_line(175, 136, 152, 174, width=3, fill=body_color)
        if errors >= 6:  # Right leg
            c.create_line(175, 136, 198, 174, width=3, fill=body_color)


def main() -> None:
    root = tk.Tk()
    ForcaApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
