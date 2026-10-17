import { describe, expect, it } from "vitest";
import { detectAvatarFormat } from "../../src/avatar/loaders/vrm-loader";

describe("detectAvatarFormat", () => {
  it.each([
    ["avatar.vrm", "vrm"],
    ["https://example.test/avatar.glb?download=1", "glb"],
    ["avatar.gltf", "gltf"],
  ] as const)("detecta %s como %s", (name, expected) => {
    expect(detectAvatarFormat(name)).toBe(expected);
  });

  it("usa o MIME type quando a origem não tem extensão", () => {
    expect(detectAvatarFormat("avatar", "model/gltf+json")).toBe("gltf");
  });
});
