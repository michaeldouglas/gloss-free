import { Grid, OrbitControls } from "@react-three/drei";
import { Canvas, useFrame } from "@react-three/fiber";
import type { AvatarController, LoadedAvatar } from "../types/avatar";
import { LiviAvatar, type LiviAvatarDiagnostics } from "./LiviAvatar";

interface AvatarSceneProps {
  controller: AvatarController;
  model: LoadedAvatar | null;
  onDiagnostics?: (diagnostics: LiviAvatarDiagnostics) => void;
}

function AvatarScene({ controller, model, onDiagnostics }: AvatarSceneProps) {
  useFrame((_state, delta) => controller.update(delta));

  return (
    <>
      <color attach="background" args={["#0b1020"]} />
      <ambientLight intensity={1.4} />
      <directionalLight position={[3, 5, 4]} intensity={2.5} />
      <directionalLight position={[-3, 2, -2]} intensity={0.8} color="#8ba4ff" />
      <Grid
        args={[10, 10]}
        cellColor="#263558"
        sectionColor="#526aa5"
        fadeDistance={8}
        fadeStrength={1.5}
        position={[0, -1, 0]}
      />
      {model ? (
        <primitive object={model.root} />
      ) : (
        <LiviAvatar onDiagnostics={onDiagnostics} />
      )}
      <OrbitControls makeDefault target={[0, 1, 0]} />
    </>
  );
}

interface AvatarCanvasProps extends AvatarSceneProps {
  className?: string;
}

export function AvatarCanvas({ controller, model, className }: AvatarCanvasProps) {
  return (
    <div className={className ?? "avatar-canvas"}>
      <Canvas camera={{ position: [0, 1.3, 3.2], fov: 35 }} dpr={[1, 2]}>
        <AvatarScene controller={controller} model={model} />
      </Canvas>
    </div>
  );
}
