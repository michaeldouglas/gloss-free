export interface TimelineKeyframe {
  at: number;
  value: number;
}

export interface TimelineTrack {
  readonly keyframes: readonly TimelineKeyframe[];
  readonly apply: (value: number) => void;
}

export interface AvatarSequence {
  readonly duration: number;
  readonly tracks: readonly TimelineTrack[];
}

function sampleTrack(track: TimelineTrack, time: number): number {
  const { keyframes } = track;
  if (keyframes.length === 0) return 0;
  if (time <= keyframes[0].at) return keyframes[0].value;

  const last = keyframes[keyframes.length - 1];
  if (time >= last.at) return last.value;

  for (let index = 1; index < keyframes.length; index += 1) {
    const next = keyframes[index];
    const previous = keyframes[index - 1];
    if (time <= next.at) {
      const span = next.at - previous.at;
      const progress = span === 0 ? 1 : (time - previous.at) / span;
      return previous.value + (next.value - previous.value) * progress;
    }
  }

  return last.value;
}

/**
 * Deterministic, renderer-independent timeline playback for future Libras
 * sequences. It intentionally knows nothing about React, SVG or Electron.
 */
export class TimelinePlayer {
  private sequence: AvatarSequence | null = null;
  private elapsed = 0;
  private playing = false;

  load(sequence: AvatarSequence): void {
    this.sequence = sequence;
    this.elapsed = 0;
    this.playing = false;
    this.applyCurrentFrame();
  }

  play(sequence?: AvatarSequence): void {
    if (sequence) this.load(sequence);
    if (this.sequence) this.playing = true;
  }

  pause(): void {
    this.playing = false;
  }

  reset(): void {
    this.elapsed = 0;
    this.playing = false;
    this.applyCurrentFrame();
  }

  get isPlaying(): boolean {
    return this.playing;
  }

  get currentTime(): number {
    return this.elapsed;
  }

  update(deltaSeconds: number): void {
    if (!this.sequence || !this.playing || deltaSeconds <= 0) return;

    this.elapsed = Math.min(this.sequence.duration, this.elapsed + deltaSeconds);
    this.applyCurrentFrame();
    if (this.elapsed >= this.sequence.duration) this.playing = false;
  }

  private applyCurrentFrame(): void {
    if (!this.sequence) return;
    for (const track of this.sequence.tracks) {
      track.apply(sampleTrack(track, this.elapsed));
    }
  }
}
