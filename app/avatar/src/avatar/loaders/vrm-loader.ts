import { VRMLoaderPlugin, type VRM } from "@pixiv/three-vrm";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import type { AvatarFileFormat, AvatarSource, LoadedAvatar } from "../types/avatar";

export function detectAvatarFormat(
  nameOrUrl: string,
  contentType?: string,
): AvatarFileFormat {
  const pathname = nameOrUrl.split("?")[0].toLowerCase();
  if (pathname.endsWith(".vrm")) return "vrm";
  if (pathname.endsWith(".gltf")) return "gltf";
  if (pathname.endsWith(".glb")) return "glb";
  if (contentType?.includes("gltf+json")) return "gltf";
  return "glb";
}

export class AvatarLoader {
  async load(source: AvatarSource): Promise<LoadedAvatar> {
    const loader = new GLTFLoader();
    loader.register((parser) => new VRMLoaderPlugin(parser));

    const sourceName = source.kind === "file" ? source.file.name : source.url;
    const format = source.format ?? detectAvatarFormat(sourceName);
    const objectUrl = source.kind === "file" ? URL.createObjectURL(source.file) : null;
    const loadUrl = source.kind === "file" ? objectUrl! : source.url;

    try {
      const gltf = await loader.loadAsync(loadUrl);
      const vrm = gltf.userData.vrm as VRM | undefined;
      return {
        root: vrm?.scene ?? gltf.scene,
        format,
        vrm,
        sourceName,
      };
    } finally {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    }
  }
}
