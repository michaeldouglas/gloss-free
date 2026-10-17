import type { Object3D, Euler } from "three";
import type { VRM } from "@pixiv/three-vrm";
import type { AvatarSequence } from "../animation/sequence-player";

export type AvatarFileFormat = "vrm" | "glb" | "gltf";
export type HandSide = "left" | "right";

export type AvatarSource =
  | { kind: "url"; url: string; format?: AvatarFileFormat }
  | { kind: "file"; file: File; format?: AvatarFileFormat };

export interface LoadedAvatar {
  root: Object3D;
  format: AvatarFileFormat;
  vrm?: VRM;
  sourceName?: string;
}

export interface HandPose {
  wrist?: Euler | readonly [number, number, number];
  fingers?: Partial<Record<string, number>>;
}

export interface AvatarController {
  readonly model: LoadedAvatar | null;
  setModel(model: LoadedAvatar | null): void;
  setBoneRotation(
    boneName: string,
    rotation: Euler | readonly [number, number, number],
  ): void;
  setHandPose(side: HandSide, pose: HandPose): void;
  setExpression(name: string, weight: number): void;
  play(sequence: AvatarSequence): void;
  update(deltaSeconds: number): void;
  dispose(): void;
}
