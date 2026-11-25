"""Procedural in-memory WAV sound effects using Windows standard library."""

import io
import math
import random
import struct
import wave

try:
    import winsound
except ImportError:  # pragma: no cover - non-Windows fallback
    winsound = None  # type: ignore[assignment]


def _build_wav_bytes(samples: list[float], sample_rate: int = 22050) -> bytes:
    """Encode normalized [-1.0, 1.0] mono PCM samples into an in-memory WAV."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        packed = bytearray()
        for s in samples:
            clamped = max(-1.0, min(1.0, s))
            packed.extend(struct.pack("<h", int(clamped * 32767)))
        wf.writeframes(bytes(packed))
    return buf.getvalue()


def _synth_footstep(base_freq: float, duration: float, volume: float) -> bytes:
    sr = 22050
    n = int(sr * duration)
    rng = random.Random(int(base_freq))
    samples: list[float] = []
    for i in range(n):
        t = i / sr
        env = math.exp(-t * 48.0)
        tone = math.sin(2.0 * math.pi * base_freq * t * (1.0 - t * 2.5))
        grit = rng.uniform(-0.35, 0.35)
        samples.append((tone * 0.7 + grit * 0.3) * env * volume)
    return _build_wav_bytes(samples, sr)


def _synth_gunshot() -> bytes:
    sr = 22050
    n = int(sr * 0.085)
    rng = random.Random(99)
    samples: list[float] = []
    for i in range(n):
        t = i / sr
        env = math.exp(-t * 42.0)
        punch = math.sin(2.0 * math.pi * 150.0 * t * math.exp(-t * 14.0))
        noise = rng.uniform(-1.0, 1.0)
        samples.append((noise * 0.65 + punch * 0.35) * env * 0.55)
    return _build_wav_bytes(samples, sr)


def _synth_reload_click() -> bytes:
    sr = 22050
    n = int(sr * 0.05)
    samples: list[float] = []
    for i in range(n):
        t = i / sr
        env = math.exp(-t * 65.0)
        samples.append(math.sin(2.0 * math.pi * 880.0 * t) * env * 0.35)
    return _build_wav_bytes(samples, sr)


class SoundManager:
    """Non-blocking sound effect player for footsteps, shots, and reloads."""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self._sounds: dict[str, bytes] = {
            "player_step": _synth_footstep(105.0, 0.055, 0.32),
            "enemy_step": _synth_footstep(165.0, 0.055, 0.38),
            "enemy_step_far": _synth_footstep(165.0, 0.050, 0.16),
            "gunshot": _synth_gunshot(),
            "reload": _synth_reload_click(),
        }

    def play(self, name: str) -> None:
        if not self.enabled or winsound is None:
            return
        data = self._sounds.get(name)
        if data is None:
            return
        try:
            winsound.PlaySound(
                data, winsound.SND_MEMORY | winsound.SND_ASYNC
            )
        except RuntimeError:
            pass
