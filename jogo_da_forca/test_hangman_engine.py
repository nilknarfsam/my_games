"""Unit tests for the Jogo da Forca game engine."""

import random
import unittest

from hangman_engine import (
    DEFAULT_TURN_SECONDS,
    DEFAULT_WORDS,
    GuessOutcome,
    HangmanEngine,
    WordEntry,
    normalize_letter,
    normalize_word,
)


class TestHangmanWordBank(unittest.TestCase):
    def test_default_word_bank_has_hundred_unique_valid_words(self) -> None:
        self.assertEqual(DEFAULT_TURN_SECONDS, 20)
        self.assertEqual(len(DEFAULT_WORDS), 100)

        normalized_words = set()
        for entry in DEFAULT_WORDS:
            norm = normalize_word(entry.word)
            self.assertEqual(len(entry.word), len(norm))
            self.assertTrue(all("A" <= ch <= "Z" for ch in norm), entry.word)
            self.assertTrue(entry.hint.strip())
            normalized_words.add(norm)

        self.assertEqual(len(normalized_words), 100)


class TestNormalization(unittest.TestCase):
    def test_normalize_letter_strips_accents_and_uppercases(self) -> None:
        self.assertEqual(normalize_letter("a"), "A")
        self.assertEqual(normalize_letter("ç"), "C")
        self.assertEqual(normalize_letter("Á"), "A")

    def test_invalid_letter_raises(self) -> None:
        with self.assertRaises(ValueError):
            normalize_letter("1")
        with self.assertRaises(ValueError):
            normalize_letter("AB")


class TestHangmanEngine(unittest.TestCase):
    def test_win_flow_with_accented_word(self) -> None:
        words = (WordEntry("VULCÃO", "Geologia"),)
        engine = HangmanEngine(words=words, rng=random.Random(42))

        self.assertEqual(engine.masked_word(), "_ _ _ _ _ _")
        self.assertEqual(engine.guess("a"), GuessOutcome.HIT)
        self.assertEqual(engine.masked_word(), "_ _ _ _ Ã _")
        self.assertEqual(engine.guess("A"), GuessOutcome.ALREADY_GUESSED)

        for ch in ("v", "u", "l", "c", "o"):
            engine.guess(ch)

        self.assertTrue(engine.is_won)
        self.assertTrue(engine.is_over)
        self.assertEqual(engine.guess("x"), GuessOutcome.GAME_OVER)

    def test_loss_flow(self) -> None:
        words = (WordEntry("SOL", "Astro"),)
        engine = HangmanEngine(words=words, max_errors=3, rng=random.Random(1))

        self.assertEqual(engine.guess("a"), GuessOutcome.MISS)
        self.assertEqual(engine.guess("b"), GuessOutcome.MISS)
        self.assertFalse(engine.is_lost)
        self.assertEqual(engine.guess("c"), GuessOutcome.MISS)
        self.assertTrue(engine.is_lost)
        self.assertTrue(engine.is_over)
        self.assertEqual(engine.remaining_attempts, 0)

    def test_timeout_counts_as_error_and_can_lose_game(self) -> None:
        words = (WordEntry("SOL", "Astro"),)
        engine = HangmanEngine(words=words, max_errors=2, rng=random.Random(1))

        self.assertEqual(engine.record_timeout(), GuessOutcome.TIMEOUT)
        self.assertEqual(engine.timeouts, 1)
        self.assertEqual(engine.errors, 1)
        self.assertFalse(engine.is_lost)

        self.assertEqual(engine.record_timeout(), GuessOutcome.TIMEOUT)
        self.assertEqual(engine.timeouts, 2)
        self.assertEqual(engine.errors, 2)
        self.assertTrue(engine.is_lost)
        self.assertEqual(engine.record_timeout(), GuessOutcome.GAME_OVER)

        engine.new_game()
        self.assertEqual(engine.timeouts, 0)
        self.assertEqual(engine.errors, 0)

    def test_new_game_avoids_immediate_repeat(self) -> None:
        words = (WordEntry("UM", "Numero"), WordEntry("DOIS", "Numero"))
        engine = HangmanEngine(words=words, rng=random.Random(7))
        first = engine.word
        second = engine.new_game().word
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
