import { Euler } from "three";
import { TimelinePlayer } from "../animation/sequence-player";
import type {
  AvatarController,
  AvatarSource,
  HandPose,
  HandSide,
  LoadedAvatar,
} from "../types/avatar";
import type { AvatarSequence } from "../animation/sequence-player";

/**
 * Three.js implementation of the platform-neutral avatar controller.
 * Electron is deliberately absent from this module.
 */
export class ThreeAvatarController implements AvatarController {
  private currentModel: LoadedAvatar | null = null;
  private readonly timeline = new TimelinePlayer();

  get model(): LoadedAvatar | null {
    return this.currentModel;
  }

  setModel(model: LoadedAvatar | null): void {
    this.currentModel = model;
  }

  setBoneRotation(
    boneName: string,
    rotation: Euler | readonly [number, number, number],
  ): void {
    const bone = this.currentModel?.root.getObjectByName(boneName);
    if (!bone) return;
    if (rotation instanceof Euler) {
      bone.rotation.copy(rotation);
    } else {
      bone.rotation.set(rotation[0], rotation[1], rotation[2]);
    }
  }

  setHandPose(_side: HandSide, _pose: HandPose): void {
    // The hand and finger bone mapping is avatar-specific and will be supplied
    // by a future VRM humanoid rig profile. The public API is stable already.
  }

  setExpression(name: string, weight: number): void {
    this.currentModel?.vrm?.expressionManager?.setValue(name, weight);
  }

  play(sequence: AvatarSequence): void {
    this.timeline.play(sequence);
  }

  update(deltaSeconds: number): void {
    this.timeline.update(deltaSeconds);
    this.currentModel?.vrm?.update(deltaSeconds);
  }

  dispose(): void {
    this.timeline.pause();
    this.currentModel = null;
  }
}

export type { AvatarSource };
