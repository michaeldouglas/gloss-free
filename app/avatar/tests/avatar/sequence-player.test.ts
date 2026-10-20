import { describe, expect, it } from "vitest";
import { TimelinePlayer, type AvatarSequence } from "../../src/avatar/animation/sequence-player";

describe("TimelinePlayer", () => {
  it("interpola keyframes e encerra no fim da sequência", () => {
    const values: number[] = [];
    const sequence: AvatarSequence = {
      duration: 2,
      tracks: [
        {
          keyframes: [
            { at: 0, value: 0 },
            { at: 2, value: 1 },
          ],
          apply: (value) => values.push(value),
        },
      ],
    };
    const player = new TimelinePlayer();

    player.play(sequence);
    player.update(1);
    expect(player.currentTime).toBe(1);
    expect(values.at(-1)).toBe(0.5);

    player.update(2);
    expect(player.currentTime).toBe(2);
    expect(values.at(-1)).toBe(1);
    expect(player.isPlaying).toBe(false);
  });
});
