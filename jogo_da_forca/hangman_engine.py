"""Pure game logic for the Portuguese Hangman (Jogo da Forca) game."""

from dataclasses import dataclass
from enum import Enum
import random
import unicodedata


@dataclass(frozen=True)
class WordEntry:
    """A word and its category hint."""

    word: str
    hint: str


DEFAULT_TURN_SECONDS = 20

DEFAULT_WORDS: tuple[WordEntry, ...] = (
    # Tecnologia (10)
    WordEntry("COMPUTADOR", "Tecnologia"),
    WordEntry("TECLADO", "Tecnologia"),
    WordEntry("MONITOR", "Tecnologia"),
    WordEntry("INTERNET", "Tecnologia"),
    WordEntry("ALGORITMO", "Tecnologia"),
    WordEntry("SERVIDOR", "Tecnologia"),
    WordEntry("APLICATIVO", "Tecnologia"),
    WordEntry("PROCESSADOR", "Tecnologia"),
    WordEntry("ROTEADOR", "Tecnologia"),
    WordEntry("IMPRESSORA", "Tecnologia"),
    # Frutas e Alimentos (10)
    WordEntry("ABACAXI", "Fruta tropical"),
    WordEntry("CHOCOLATE", "Doce popular"),
    WordEntry("MORANGO", "Fruta vermelha"),
    WordEntry("MELANCIA", "Fruta grande"),
    WordEntry("MARACUJÁ", "Fruta ácida"),
    WordEntry("TANGERINA", "Fruta cítrica"),
    WordEntry("PANQUECA", "Alimento"),
    WordEntry("LASANHA", "Prato italiano"),
    WordEntry("BRIGADEIRO", "Doce brasileiro"),
    WordEntry("CROISSANT", "Padaria"),
    # Animais (10)
    WordEntry("ELEFANTE", "Animal terrestre"),
    WordEntry("BORBOLETA", "Inseto colorido"),
    WordEntry("CROCODILO", "Réptil"),
    WordEntry("PINGUIM", "Ave polar"),
    WordEntry("CANGURU", "Marsupial"),
    WordEntry("GOLFINHO", "Mamífero marinho"),
    WordEntry("TARTARUGA", "Animal com casco"),
    WordEntry("CAMALEÃO", "Réptil que muda de cor"),
    WordEntry("FLAMINGO", "Ave pernalta"),
    WordEntry("RINOCERONTE", "Animal com chifre"),
    # Ciência e Espaço (10)
    WordEntry("ASTRONOMIA", "Ciência dos astros"),
    WordEntry("TELESCÓPIO", "Instrumento óptico"),
    WordEntry("GRAVIDADE", "Força física"),
    WordEntry("CONSTELAÇÃO", "Grupo de estrelas"),
    WordEntry("SATÉLITE", "Corpo em órbita"),
    WordEntry("MICROSCÓPIO", "Instrumento de laboratório"),
    WordEntry("MOLÉCULA", "Química"),
    WordEntry("LABORATÓRIO", "Local de pesquisa"),
    WordEntry("METEORITO", "Rocha espacial"),
    WordEntry("PLANETÁRIO", "Espaço científico"),
    # Transportes (10)
    WordEntry("BICICLETA", "Meio de transporte"),
    WordEntry("HELICÓPTERO", "Transporte aéreo"),
    WordEntry("SUBMARINO", "Transporte aquático"),
    WordEntry("MOTOCICLETA", "Veículo de duas rodas"),
    WordEntry("LOCOMOTIVA", "Transporte ferroviário"),
    WordEntry("AERONAVE", "Aviação"),
    WordEntry("PATINETE", "Mobilidade urbana"),
    WordEntry("CARAVELA", "Embarcação antiga"),
    WordEntry("TELEFÉRICO", "Transporte por cabo"),
    WordEntry("AMBULÂNCIA", "Veículo de emergência"),
    # Natureza e Geografia (10)
    WordEntry("MONTANHA", "Formação geográfica"),
    WordEntry("CACHOEIRA", "Queda d'água"),
    WordEntry("ARQUIPÉLAGO", "Conjunto de ilhas"),
    WordEntry("VULCÃO", "Formação geológica"),
    WordEntry("DESERTO", "Bioma seco"),
    WordEntry("FLORESTA", "Bioma com muitas árvores"),
    WordEntry("PENÍNSULA", "Formação costeira"),
    WordEntry("TEMPESTADE", "Fenômeno climático"),
    WordEntry("HORIZONTE", "Paisagem"),
    WordEntry("OCEANO", "Grande massa de água"),
    # Música e Arte (10)
    WordEntry("ORQUESTRA", "Conjunto musical"),
    WordEntry("SAXOFONE", "Instrumento de sopro"),
    WordEntry("VIOLONCELO", "Instrumento de cordas"),
    WordEntry("PARTITURA", "Leitura musical"),
    WordEntry("ESCULTURA", "Arte visual"),
    WordEntry("AQUARELA", "Técnica de pintura"),
    WordEntry("TEATRO", "Artes cênicas"),
    WordEntry("MELODIA", "Música"),
    WordEntry("ACORDEÃO", "Instrumento musical"),
    WordEntry("HARMONIA", "Teoria musical"),
    # Lugares e Construções (10)
    WordEntry("BIBLIOTECA", "Lugar cheio de livros"),
    WordEntry("OBSERVATÓRIO", "Local para ver o céu"),
    WordEntry("AQUÁRIO", "Local com peixes"),
    WordEntry("FAROL", "Sinalização marítima"),
    WordEntry("CASTELO", "Construção medieval"),
    WordEntry("AEROPORTO", "Terminal de voos"),
    WordEntry("CATEDRAL", "Construção histórica"),
    WordEntry("UNIVERSIDADE", "Ensino superior"),
    WordEntry("ESTÁDIO", "Arena esportiva"),
    WordEntry("MUSEU", "Espaço cultural"),
    # Objetos do Dia a Dia (10)
    WordEntry("LANTERNA", "Iluminação portátil"),
    WordEntry("BÚSSOLA", "Orientação geográfica"),
    WordEntry("MOCHILA", "Objeto para carregar itens"),
    WordEntry("TERMÔMETRO", "Medição de temperatura"),
    WordEntry("CALENDÁRIO", "Organização do tempo"),
    WordEntry("ENVELOPE", "Correspondência"),
    WordEntry("AMPULHETA", "Medidor de tempo antigo"),
    WordEntry("ESPELHO", "Objeto reflexivo"),
    WordEntry("TRAVESSEIRO", "Item de descanso"),
    WordEntry("TESOURA", "Objeto de corte"),
    # Profissões e Esportes (10)
    WordEntry("ASTRONAUTA", "Profissão espacial"),
    WordEntry("ARQUITETO", "Profissão de projetos"),
    WordEntry("JORNALISTA", "Profissão de comunicação"),
    WordEntry("ENGENHEIRO", "Profissão técnica"),
    WordEntry("BOMBEIRO", "Profissão de resgate"),
    WordEntry("BASQUETE", "Esporte com cesta"),
    WordEntry("NATAÇÃO", "Esporte aquático"),
    WordEntry("GINÁSTICA", "Esporte olímpico"),
    WordEntry("MARATONA", "Corrida de longa distância"),
    WordEntry("ESGRIMA", "Esporte com florete"),
)


class GuessOutcome(str, Enum):
    """Result of evaluating a guessed letter or timeout."""

    HIT = "hit"
    MISS = "miss"
    TIMEOUT = "timeout"
    ALREADY_GUESSED = "already_guessed"
    GAME_OVER = "game_over"


def normalize_letter(raw: str) -> str:
    """Normalize a single character to an uppercase ASCII A-Z letter."""
    cleaned = raw.strip()
    if len(cleaned) != 1:
        raise ValueError("Informe apenas uma letra.")
    decomposed = unicodedata.normalize("NFD", cleaned)
    ascii_chars = [ch for ch in decomposed if unicodedata.category(ch) != "Mn"]
    letter = "".join(ascii_chars).upper()
    if len(letter) != 1 or not ("A" <= letter <= "Z"):
        raise ValueError("Informe uma letra válida de A a Z.")
    return letter


def normalize_word(word: str) -> str:
    """Normalize a word to uppercase ASCII A-Z characters."""
    decomposed = unicodedata.normalize("NFD", word.strip())
    ascii_chars = [ch for ch in decomposed if unicodedata.category(ch) != "Mn"]
    return "".join(ascii_chars).upper()


class HangmanEngine:
    """State machine for a single round of Hangman."""

    def __init__(
        self,
        words: tuple[WordEntry, ...] = DEFAULT_WORDS,
        max_errors: int = 6,
        rng: random.Random | None = None,
    ) -> None:
        if not words:
            raise ValueError("A lista de palavras não pode estar vazia.")
        if max_errors < 1:
            raise ValueError("max_errors deve ser pelo menos 1.")

        self._words = words
        self._max_errors = max_errors
        self._rng = rng or random.Random()
        self._previous_word: str | None = None

        self._entry = WordEntry("", "")
        self._normalized_word = ""
        self._guessed: set[str] = set()
        self._wrong: list[str] = []
        self._timeouts = 0
        self.new_game()

    @property
    def max_errors(self) -> int:
        return self._max_errors

    @property
    def word(self) -> str:
        return self._entry.word

    @property
    def hint(self) -> str:
        return self._entry.hint

    @property
    def timeouts(self) -> int:
        return self._timeouts

    @property
    def errors(self) -> int:
        return len(self._wrong) + self._timeouts

    @property
    def remaining_attempts(self) -> int:
        return max(0, self._max_errors - self.errors)

    @property
    def guessed_letters(self) -> frozenset[str]:
        return frozenset(self._guessed)

    @property
    def wrong_letters(self) -> tuple[str, ...]:
        return tuple(self._wrong)

    @property
    def is_won(self) -> bool:
        return all(ch in self._guessed for ch in self._normalized_word)

    @property
    def is_lost(self) -> bool:
        return self.errors >= self._max_errors and not self.is_won

    @property
    def is_over(self) -> bool:
        return self.is_won or self.is_lost

    def new_game(self, entry: WordEntry | None = None) -> WordEntry:
        """Start a new round, picking a random word without immediate repeat."""
        if entry is None:
            candidates = [
                item for item in self._words if item.word != self._previous_word
            ]
            pool = candidates if candidates else list(self._words)
            entry = self._rng.choice(pool)

        self._entry = entry
        self._normalized_word = normalize_word(entry.word)
        self._previous_word = entry.word
        self._guessed.clear()
        self._wrong.clear()
        self._timeouts = 0
        return entry

    def masked_word(self) -> str:
        """Return the word with unguessed letters replaced by underscores."""
        chars = [
            orig if norm in self._guessed else "_"
            for orig, norm in zip(self._entry.word, self._normalized_word)
        ]
        return " ".join(chars)

    def guess(self, raw_letter: str) -> GuessOutcome:
        """Evaluate a guessed letter and update game state."""
        if self.is_over:
            return GuessOutcome.GAME_OVER

        letter = normalize_letter(raw_letter)
        if letter in self._guessed:
            return GuessOutcome.ALREADY_GUESSED

        self._guessed.add(letter)
        if letter in self._normalized_word:
            return GuessOutcome.HIT

        self._wrong.append(letter)
        return GuessOutcome.MISS

    def record_timeout(self) -> GuessOutcome:
        """Count a 20-second turn expiration as an error."""
        if self.is_over:
            return GuessOutcome.GAME_OVER
        self._timeouts += 1
        return GuessOutcome.TIMEOUT
