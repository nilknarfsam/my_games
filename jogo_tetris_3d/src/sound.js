export class SoundEngine {
  constructor() {
    this.ctx = null;
    this.muted = false;
  }

  #ensureContext() {
    if (this.muted) return null;
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return null;
      this.ctx = new AudioCtx();
    }
    if (this.ctx.state === 'suspended') {
      this.ctx.resume().catch(() => {});
    }
    return this.ctx;
  }

  toggleMute() {
    this.muted = !this.muted;
    return this.muted;
  }

  #tone(freq, duration, type = 'sine', gainVal = 0.08, delay = 0, slideTo = null) {
    const ctx = this.#ensureContext();
    if (!ctx) return;
    const now = ctx.currentTime + delay;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, now);
    if (slideTo) {
      osc.frequency.exponentialRampToValueAtTime(slideTo, now + duration);
    }
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.linearRampToValueAtTime(gainVal, now + 0.01);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + duration);

    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + duration + 0.02);
  }

  move() {
    this.#tone(320, 0.05, 'triangle', 0.05, 0, 360);
  }

  rotate() {
    this.#tone(460, 0.07, 'sine', 0.07, 0, 620);
  }

  softDrop() {
    this.#tone(200, 0.04, 'sine', 0.035, 0, 160);
  }

  hardDrop() {
    this.#tone(170, 0.12, 'triangle', 0.12, 0, 65);
    this.#tone(340, 0.06, 'sine', 0.05, 0, 120);
  }

  hold() {
    this.#tone(420, 0.07, 'sine', 0.06, 0, 520);
  }

  clear(linesCount) {
    const chords = {
      1: [523.25, 659.25],
      2: [523.25, 659.25, 783.99],
      3: [523.25, 659.25, 783.99, 987.77],
      4: [523.25, 659.25, 783.99, 1046.5, 1318.5],
    };
    const notes = chords[linesCount] ?? chords[1];
    notes.forEach((freq, i) => {
      this.#tone(freq, linesCount === 4 ? 0.24 : 0.16, 'triangle', 0.09, i * 0.045);
    });
  }

  levelUp() {
    [440, 554.37, 659.25, 880].forEach((freq, i) => {
      this.#tone(freq, 0.15, 'sine', 0.08, i * 0.06);
    });
  }

  gameOver() {
    [340, 277, 220, 146.8].forEach((freq, i) => {
      this.#tone(freq, 0.22, 'sawtooth', 0.06, i * 0.11);
    });
  }
}
