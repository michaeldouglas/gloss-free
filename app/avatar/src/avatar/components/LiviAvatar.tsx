import { useGLTF } from "@react-three/drei";
import { Box3, Group, Vector3 } from "three";
import { useEffect, useLayoutEffect, useMemo, useRef } from "react";
import type { GLTF } from "three/examples/jsm/loaders/GLTFLoader.js";

export const LIVI_AVATAR_URL = "/avatars/avatar.glb";

export interface LiviAvatarDiagnostics {
  nodes: number;
  meshes: number;
  materials: number;
  textures: number;
  bones: number;
  skeletons: number;
  skins: number;
  animations: number;
}

interface GltfJson {
  nodes?: unknown[];
  meshes?: unknown[];
  materials?: unknown[];
  textures?: unknown[];
  skins?: Array<{ joints?: number[] }>;
  animations?: unknown[];
}

interface LiviAvatarProps {
  onDiagnostics?: (diagnostics: LiviAvatarDiagnostics) => void;
}

function inspectGltf(gltf: GLTF): LiviAvatarDiagnostics {
  const json = (gltf.parser as unknown as { json?: GltfJson }).json;
  const skins = json?.skins ?? [];
  const bones = new Set(skins.flatMap((skin) => skin.joints ?? []));

  return {
    nodes: json?.nodes?.length ?? 0,
    meshes: json?.meshes?.length ?? 0,
    materials: json?.materials?.length ?? 0,
    textures: json?.textures?.length ?? 0,
    bones: bones.size,
    skeletons: skins.length,
    skins: skins.length,
    animations: json?.animations?.length ?? gltf.animations.length,
  };
}

/** Loads and renders the repository's primary static GLB avatar. */
export function LiviAvatar({ onDiagnostics }: LiviAvatarProps) {
  const gltf = useGLTF(LIVI_AVATAR_URL) as GLTF;
  const groupRef = useRef<Group | null>(null);
  const diagnostics = useMemo(() => inspectGltf(gltf), [gltf]);

  useEffect(() => {
    console.info("[LiviAvatar] avatar.glb diagnostics", diagnostics);
    onDiagnostics?.(diagnostics);
  }, [diagnostics, onDiagnostics]);

  useLayoutEffect(() => {
    const group = groupRef.current;
    if (!group) return;

    const bounds = new Box3().setFromObject(gltf.scene);
    const size = bounds.getSize(new Vector3());
    const center = bounds.getCenter(new Vector3());
    const largestDimension = Math.max(size.x, size.y, size.z);
    if (largestDimension === 0) return;

    const scale = 2 / largestDimension;
    group.scale.setScalar(scale);
    group.position.set(
      -center.x * scale,
      -bounds.min.y * scale - 1,
      -center.z * scale,
    );
  }, [gltf.scene]);

  return (
    <group ref={groupRef} name="livi-avatar">
      <primitive object={gltf.scene} />
    </group>
  );
}

useGLTF.preload(LIVI_AVATAR_URL);
