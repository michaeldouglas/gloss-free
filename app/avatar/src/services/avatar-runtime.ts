import { AvatarLoader } from "../avatar/loaders/vrm-loader";
import { ThreeAvatarController } from "../avatar/controllers/avatar-controller";
import type { AvatarController, AvatarSource, LoadedAvatar } from "../avatar/types/avatar";

export class AvatarRuntime {
  readonly loader = new AvatarLoader();
  readonly controller: AvatarController = new ThreeAvatarController();

  async load(source: AvatarSource): Promise<LoadedAvatar> {
    const model = await this.loader.load(source);
    this.controller.setModel(model);
    return model;
  }

  dispose(): void {
    this.controller.dispose();
  }
}
