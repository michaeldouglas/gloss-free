import { useSyncExternalStore } from "react";
import {
  LIVI_FINGERS,
  type LiviController,
  type LiviFinger,
  type LiviFingerJoint,
  type LiviSegment,
  type LiviSide,
  type LiviState,
} from "../2d/livi-types";

interface LiviControlsProps {
  controller: LiviController;
}

function useStateSnapshot(controller: LiviController): LiviState {
  return useSyncExternalStore(
    controller.subscribe.bind(controller),
    controller.getState.bind(controller),
    controller.getState.bind(controller),
  );
}

function Range({ label, value, min, max, step = 1, onChange }: { label: string; value: number; min: number; max: number; step?: number; onChange: (value: number) => void }) {
  return (
    <label className="livi-range">
      <span>{label}</span>
      <input type="range" min={min} max={max} step={step} value={value} onChange={(event) => onChange(Number(event.target.value))} />
      <output>{Math.round(value * 100) / 100}</output>
    </label>
  );
}

function SegmentRanges({ controller, segments }: { controller: LiviController; segments: readonly { name: string; segment: LiviSegment; min: number; max: number }[] }) {
  const state = useStateSnapshot(controller);
  return (
    <div className="livi-control-grid">
      {segments.map(({ name, segment, min, max }) => {
        const value = segment === "torso" ? state.torsoRotation : segment === "head" ? state.headRotation : segment === "neck" ? state.neckRotation : segment.includes("UpperArm") ? state.arms[segment.startsWith("left") ? "left" : "right"].upperArm : segment.includes("Forearm") ? state.arms[segment.startsWith("left") ? "left" : "right"].forearm : segment.includes("Wrist") ? state.arms[segment.startsWith("left") ? "left" : "right"].wrist : segment.includes("Thigh") ? state.legs[segment.startsWith("left") ? "left" : "right"].thigh : segment.includes("Shin") ? state.legs[segment.startsWith("left") ? "left" : "right"].shin : state.legs[segment.startsWith("left") ? "left" : "right"].ankle;
        return <Range key={segment} label={name} value={value} min={min} max={max} onChange={(next) => controller.setSegmentRotation(segment, next)} />;
      })}
    </div>
  );
}

function HandControls({ controller, side }: { controller: LiviController; side: LiviSide }) {
  const state = useStateSnapshot(controller);
  const hand = state.hands[side];
  const target = state.arms[side].handTarget;
  return (
    <div className="livi-hand-controls">
      <div className="livi-button-row">
        {(["open", "flat", "point", "l", "fist"] as const).map((shape) => (
          <button key={shape} type="button" className={hand.shape === shape ? "is-selected" : ""} onClick={() => controller.setHandShape(side, shape)}>{shape}</button>
        ))}
      </div>
      {LIVI_FINGERS.map((finger) => (
        <Range key={finger} label={finger} value={hand.fingers[finger]} min={0} max={1} step={0.01} onChange={(value) => controller.setFingerCurl(side, finger, value)} />
      ))}
      <details className="livi-joint-editor">
        <summary>articular cada falange</summary>
        {LIVI_FINGERS.map((finger) => (
          <div key={finger} className="livi-finger-joints">
            <strong>{finger}</strong>
            {(["base", "middle", "tip", "spread"] as const).map((joint: LiviFingerJoint) => {
              const limit = joint === "spread" ? 35 : 120;
              return (
                <Range
                  key={joint}
                  label={joint}
                  value={hand.joints[finger][joint]}
                  min={-limit}
                  max={limit}
                  onChange={(value) => controller.setFingerJointRotation(side, finger, joint, value)}
                />
              );
            })}
          </div>
        ))}
      </details>
      <p className="livi-control-help">Mover a mão no plano SVG (cinemática de dois segmentos).</p>
      <Range label="mão X" value={target.x} min={35} max={365} onChange={(x) => controller.moveHand(side, { x, y: target.y })} />
      <Range label="mão Y" value={target.y} min={185} max={500} onChange={(y) => controller.moveHand(side, { x: target.x, y })} />
      <Range label="pulso" value={state.arms[side].wrist} min={-90} max={90} onChange={(wrist) => controller.setHandPose(side, { wrist })} />
    </div>
  );
}

const ARM_SEGMENTS = [
  { name: "braço E", segment: "leftUpperArm" as const, min: -180, max: 180 },
  { name: "antebraço E", segment: "leftForearm" as const, min: -180, max: 180 },
  { name: "braço D", segment: "rightUpperArm" as const, min: -180, max: 180 },
  { name: "antebraço D", segment: "rightForearm" as const, min: -180, max: 180 },
] as const;

const LEG_SEGMENTS = [
  { name: "coxa E", segment: "leftThigh" as const, min: -60, max: 60 },
  { name: "canela E", segment: "leftShin" as const, min: -90, max: 90 },
  { name: "tornozelo E", segment: "leftAnkle" as const, min: -45, max: 45 },
  { name: "coxa D", segment: "rightThigh" as const, min: -60, max: 60 },
  { name: "canela D", segment: "rightShin" as const, min: -90, max: 90 },
  { name: "tornozelo D", segment: "rightAnkle" as const, min: -45, max: 45 },
] as const;

export function LiviControls({ controller }: LiviControlsProps) {
  const state = useStateSnapshot(controller);
  return (
    <aside className="livi-panel">
      <section className="livi-section livi-section--intro">
        <p className="panel-label">Controlador procedural</p>
        <h2>Livi 2D articulada</h2>
        <p className="livi-control-help">Cada grupo do SVG tem um segmento independente. A API pública está disponível em <code>window.livi</code>.</p>
      </section>

      <section className="livi-section">
        <h3>Corpo e cabeça</h3>
        <SegmentRanges controller={controller} segments={[{ name: "tronco", segment: "torso", min: -40, max: 40 }, { name: "cabeça", segment: "head", min: -45, max: 45 }, { name: "pescoço", segment: "neck", min: -25, max: 25 }]} />
        <Range label="olhar X" value={state.lookAt.x} min={-1} max={1} step={0.01} onChange={(value) => controller.lookAt(value, state.lookAt.y)} />
        <Range label="olhar Y" value={state.lookAt.y} min={-1} max={1} step={0.01} onChange={(value) => controller.lookAt(state.lookAt.x, value)} />
      </section>

      <section className="livi-section">
        <h3>Braços</h3>
        <SegmentRanges controller={controller} segments={ARM_SEGMENTS} />
        <div className="livi-hand-columns">
          <div><h4>Mão esquerda</h4><HandControls controller={controller} side="left" /></div>
          <div><h4>Mão direita</h4><HandControls controller={controller} side="right" /></div>
        </div>
      </section>

      <section className="livi-section">
        <h3>Pernas</h3>
        <SegmentRanges controller={controller} segments={LEG_SEGMENTS} />
      </section>

      <section className="livi-section">
        <h3>Expressão</h3>
        <Range label="sorriso" value={state.expression.smile} min={0} max={1} step={0.01} onChange={(value) => controller.setExpression("smile", value)} />
        <Range label="boca aberta" value={state.expression.mouthOpen} min={0} max={1} step={0.01} onChange={(value) => controller.setExpression("mouthOpen", value)} />
        <Range label="largura da boca" value={state.expression.mouthWidth} min={0} max={1} step={0.01} onChange={(value) => controller.setExpression("mouthWidth", value)} />
        <Range label="canto da boca" value={state.expression.mouthCorner} min={-1} max={1} step={0.01} onChange={(value) => controller.setExpression("mouthCorner", value)} />
        <Range label="bochechas" value={state.expression.cheekRaise} min={0} max={1} step={0.01} onChange={(value) => controller.setExpression("cheekRaise", value)} />
        <Range label="sobrancelhas" value={state.expression.browRaise} min={0} max={1} step={0.01} onChange={(value) => controller.setExpression("browRaise", value)} />
        <Range label="sobrancelha E" value={state.expression.browLeft} min={-1} max={1} step={0.01} onChange={(value) => controller.setExpression("browLeft", value)} />
        <Range label="sobrancelha D" value={state.expression.browRight} min={-1} max={1} step={0.01} onChange={(value) => controller.setExpression("browRight", value)} />
        <div className="livi-button-row"><button type="button" onClick={() => controller.blink("left")}>piscar E</button><button type="button" onClick={() => controller.blink("right")}>piscar D</button></div>
      </section>

      <section className="livi-section">
        <h3>Animações de teste</h3>
        <p className="livi-control-help">São coreografias de demonstração para validar o motor. O vocabulário de Libras será conectado futuramente.</p>
        <div className="livi-button-row"><button type="button" onClick={() => controller.sign("hello")}>olá</button><button type="button" onClick={() => controller.sign("wave")}>acenar</button><button type="button" onClick={() => controller.resetPose()}>resetar</button></div>
      </section>
    </aside>
  );
}
