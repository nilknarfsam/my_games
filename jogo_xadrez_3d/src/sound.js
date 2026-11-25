export class ChessSound {
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

  #tone(freq, duration, type = 'sine', gainVal = 0.07, delay = 0, slideTo = null) {
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
    this.#tone(220, 0.07, 'triangle', 0.08, 0, 140);
  }

  capture() {
    this.#tone(320, 0.09, 'triangle', 0.1, 0, 110);
    this.#tone(520, 0.05, 'sine', 0.05, 0.02, 260);
  }

  castle() {
    this.#tone(240, 0.06, 'triangle', 0.07, 0, 180);
    this.#tone(300, 0.07, 'triangle', 0.07, 0.08, 200);
  }

  check() {
    this.#tone(660, 0.12, 'sine', 0.09, 0, 880);
  }

  gameOver() {
    [440, 554.37, 659.25, 880].forEach((f, i) => {
      this.#tone(f, 0.18, 'triangle', 0.08, i * 0.07);
    });
  }
}
