import { useEffect, useSyncExternalStore } from "react";
import type {
  LiviArmState,
  LiviController,
  LiviFinger,
  LiviFingerJoints,
  LiviHandState,
  LiviSide,
  LiviState,
  LiviTransform,
} from "../2d/livi-types";

interface LiviAvatar2DProps {
  controller: LiviController;
  className?: string;
  debug?: boolean;
}

const SHOULDER = { left: { x: 145, y: 238 }, right: { x: 255, y: 238 } } as const;
const HIP = { left: { x: 176, y: 414 }, right: { x: 224, y: 414 } } as const;

function useLiviState(controller: LiviController): LiviState {
  return useSyncExternalStore(
    controller.subscribe.bind(controller),
    controller.getState.bind(controller),
    controller.getState.bind(controller),
  );
}

function useControllerClock(controller: LiviController): void {
  useEffect(() => {
    let previous = performance.now();
    let frame = 0;
    const tick = (now: number) => {
      const delta = Math.min(0.05, (now - previous) / 1000);
      previous = now;
      controller.update(delta);
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [controller]);
}

function withTransform(base: string, transform: LiviTransform): string {
  return `${base} translate(${transform.x} ${transform.y}) rotate(${transform.rotation}) scale(${transform.scaleX} ${transform.scaleY})`;
}

const DEFAULT_JOINTS: LiviFingerJoints = { base: 0, middle: 0, tip: 0, spread: 0 };

function Arm({ side, arm, hand }: {
  side: LiviSide;
  arm: LiviArmState & { transform: LiviTransform; forearmTransform: LiviTransform; handTransform: LiviTransform };
  hand: LiviHandState;
}) {
  const shoulder = SHOULDER[side];
  const mirror = side === "left" ? -1 : 1;
  return (
    <g data-part={`${side}-arm`} transform={withTransform(`translate(${shoulder.x} ${shoulder.y}) rotate(${arm.upperArm})`, arm.transform)}>
      <path className="livi-sleeve-shadow" d="M-23-10 C-27 18-26 57-18 86 Q0 98 18 86 C26 57 27 18 23-10Z" />
      <path className="livi-sleeve" d="M-20-9 C-23 19-22 55-15 82 Q0 91 15 82 C22 55 23 19 20-9Z" />
      <path className="livi-sleeve-highlight" d="M-13-6 C-16 26-14 55-9 72" />
      <g data-part={`${side}-forearm`} transform={withTransform(`translate(0 78) rotate(${arm.forearm})`, arm.forearmTransform)}>
        <path className="livi-sleeve-shadow" d="M-19-7 C-24 19-23 52-15 77 Q0 87 15 77 C23 52 24 19 19-7Z" />
        <path className="livi-sleeve livi-sleeve--forearm" d="M-16-6 C-20 19-19 50-12 73 Q0 81 12 73 C19 50 20 19 16-6Z" />
        <path className="livi-sleeve-highlight" d="M-10 0 C-13 23-11 48-7 63" />
        <path className="livi-cuff" d="M-13 64 Q0 73 13 64 L13 78 Q0 86-13 78Z" />
        <g data-part={`${side}-hand`} transform={withTransform(`translate(0 75) rotate(${arm.wrist}) scale(${mirror} 1)`, arm.handTransform)}>
          <path className="livi-wrist-skin" d="M-13-8 Q0-14 13-8 L15 10 Q0 17-15 10Z" />
          <LiviHand hand={hand} />
        </g>
      </g>
    </g>
  );
}

const FINGER_LAYOUT: Record<LiviFinger, { x: number; y: number; rotate: number }> = {
  thumb: { x: -23, y: 23, rotate: -53 },
  index: { x: -16, y: 3, rotate: -8 },
  middle: { x: -5, y: -3, rotate: -2 },
  ring: { x: 6, y: -1, rotate: 4 },
  pinky: { x: 16, y: 4, rotate: 11 },
};

function LiviHand({ hand }: { hand: LiviHandState }) {
  return (
    <g className="livi-hand" data-hand-shape={hand.shape}>
      <ellipse className="livi-palm-shadow" cx="0" cy="22" rx="29" ry="32" />
      <ellipse className="livi-palm" cx="0" cy="19" rx="27" ry="31" />
      <path className="livi-palm-highlight" d="M-20 13 Q-7-4 12 0 Q25 6 22 21 Q10 12-4 14 Q-13 16-20 25Z" />
      {(Object.keys(FINGER_LAYOUT) as LiviFinger[]).map((finger) => {
        const layout = FINGER_LAYOUT[finger];
        const joints = hand.joints?.[finger] ?? DEFAULT_JOINTS;
        return (
          <g key={finger} data-finger={finger} transform={`translate(${layout.x} ${layout.y}) rotate(${layout.rotate + joints.spread + joints.base})`}>
            <path className="livi-finger" d="M-6 2 C-7-8-7-21-5-31 Q0-36 5-31 C7-21 7-8 6 2Z" />
            <g transform={`translate(0 -28) rotate(${joints.middle})`}>
              <path className="livi-finger" d="M-5 1 C-6-6-6-16-4-24 Q0-28 4-24 C6-16 6-6 5 1Z" />
              <g transform={`translate(0 -21) rotate(${joints.tip})`}>
                <path className="livi-finger" d="M-4 1 C-5-5-5-12-3-18 Q0-21 3-18 C5-12 5-5 4 1Z" />
                <path className="livi-finger-highlight" d="M-1-16 Q0-19 1-16 L1-3" />
              </g>
            </g>
          </g>
        );
      })}
    </g>
  );
}

function Leg({ side, state }: {
  side: LiviSide;
  state: LiviState["legs"][LiviSide] & { transform: LiviTransform; shinTransform: LiviTransform; footTransform: LiviTransform };
}) {
  const hip = HIP[side];
  return (
    <g data-part={`${side}-leg`} transform={withTransform(`translate(${hip.x} ${hip.y}) rotate(${state.thigh})`, state.transform)}>
      <path className="livi-trouser" d="M-20-4 Q0-11 20-4 L22 94 Q0 108-22 94Z" />
      <g data-part={`${side}-shin`} transform={withTransform(`translate(0 94) rotate(${state.shin})`, state.shinTransform)}>
        <path className="livi-trouser livi-trouser--leg" d="M-17 0 Q0 7 17 0 L16 94 Q0 101-16 94Z" />
        <g data-part={`${side}-foot`} transform={withTransform(`translate(0 90) rotate(${state.ankle})`, state.footTransform)}>
          <path className="livi-shoe" d="M-15 0 C-15 15-25 25-41 30 C-49 33-48 44-38 46 L19 46 C28 46 29 35 22 30 L12 22 L12 0Z" />
        </g>
      </g>
    </g>
  );
}

function Eye({ side, blink, lookAt, transform }: { side: LiviSide; blink: number; lookAt: LiviState["lookAt"]; transform: LiviTransform }) {
  const x = side === "left" ? -21 : 21;
  const open = 1 - blink;
  return (
    <g data-part={`${side}-eye`} transform={withTransform(`translate(${x} -9)`, transform)}>
      <g transform={`scale(1 ${Math.max(0.12, open)})`}>
        <path className="livi-eye-white" d="M-13 0 Q-3-10 10-1 Q-1 10-13 0Z" />
        <ellipse className="livi-eye-iris" cx={lookAt.x * 4} cy={lookAt.y * 3} rx="5" ry="5.5" />
        <ellipse className="livi-eye-pupil" cx={lookAt.x * 4} cy={lookAt.y * 3} rx="2" ry="3" />
        <path className="livi-eyelash" d="M-12-1 Q-2-11 10-2" />
      </g>
      <path className="livi-eyelid" d={`M-13 0 Q-2 ${-9 * open} 10 0`} />
    </g>
  );
}

function Head({ state }: { state: LiviState }) {
  const { expression, lookAt } = state;
  const smileHeight = 34 + expression.smile * 10 + expression.mouthCorner * 10;
  const mouthWidth = 17 + expression.mouthWidth * 9;
  return (
    <g data-part="head" transform={withTransform(`translate(200 139) rotate(${state.headRotation}) rotate(${state.headTilt} 0 0)`, state.transforms.head)}>
      <path className="livi-hair-back" transform={withTransform("", state.transforms.hair)} d="M-57 35 C-81 4-76-54-30-72 C24-95 75-61 72-9 C82 39 77 90 59 126 Q43 143 35 104 L-38 106 Q-49 145-63 125 C-79 90-79 58-57 35Z" />
      <path className="livi-face-shadow" d="M-48-4 Q-47-61 0-65 Q47-61 48-4 L43 38 Q34 61 0 68 Q-34 61-43 38Z" />
      <path className="livi-face" d="M-46-7 Q-45-58 0-61 Q45-58 46-7 L41 34 Q31 59 0 65 Q-31 59-41 34Z" />
      <path className="livi-hair-cap" transform={withTransform("", state.transforms.hair)} d="M-49-12 C-57-58-27-75 3-72 C39-71 57-48 49-9 C38-26 25-37 6-40 C-12-42-31-33-49-12Z" />
      <g data-part="leftBrow" transform={withTransform("", state.transforms.leftBrow)}><path className="livi-eyebrow" d={`M-34-27 Q-22 ${-31 - (expression.browRaise + expression.browLeft) * 5} -9-27`} /></g>
      <g data-part="rightBrow" transform={withTransform("", state.transforms.rightBrow)}><path className="livi-eyebrow" d={`M9-27 Q22 ${-31 - (expression.browRaise + expression.browRight) * 5} 34-27`} /></g>
      <Eye side="left" blink={expression.blinkLeft} lookAt={lookAt} transform={state.transforms.leftEye} />
      <Eye side="right" blink={expression.blinkRight} lookAt={lookAt} transform={state.transforms.rightEye} />
      <g data-part="nose" transform={withTransform("", state.transforms.nose)}>
        <path className="livi-nose-shape" d="M-3-10 C-8 6-10 17-4 23 Q2 28 8 22 Q11 19 7 15 L3 12 L4-2Z" />
        <path className="livi-nostril" d="M-3 21 Q0 24 3 21" />
      </g>
      <g data-part="mouth" transform={withTransform("", state.transforms.mouth)}>
        <path className="livi-mouth-open" d={`M-${mouthWidth} 32 Q0 ${smileHeight + 4} ${mouthWidth} 32 Q0 ${40 + expression.mouthOpen * 8} -${mouthWidth} 32Z`} opacity={expression.mouthOpen} />
        <path className="livi-lip-upper" d={`M-${mouthWidth} 32 Q-${mouthWidth / 2} ${25 - expression.smile * 3} 0 31 Q${mouthWidth / 2} ${25 - expression.smile * 3} ${mouthWidth} 32 Q${mouthWidth / 2} ${35 + expression.mouthCorner * 3} 0 34 Q-${mouthWidth / 2} ${35 + expression.mouthCorner * 3} -${mouthWidth} 32Z`} />
        <path className="livi-lip-lower" d={`M-${mouthWidth} 32 Q0 ${47 + expression.mouthOpen * 4} ${mouthWidth} 32 Q0 ${39 + expression.mouthOpen * 6} -${mouthWidth} 32Z`} />
      </g>
      <g data-part="leftEar" transform={withTransform("", state.transforms.leftEar)}><path className="livi-ear" d="M-45-3 Q-60-4-57 15 Q-54 28-43 22Z" /></g>
      <g data-part="rightEar" transform={withTransform("", state.transforms.rightEar)}><path className="livi-ear" d="M45-3 Q60-4 57 15 Q54 28 43 22Z" /></g>
      <path className="livi-hair-lock livi-hair-lock--left" transform={withTransform("", state.transforms.hair)} d="M-46-38 C-66-4-63 39-53 92 Q-48 114-35 91 L-34 29Z" />
      <path className="livi-hair-lock livi-hair-lock--right" transform={withTransform("", state.transforms.hair)} d="M46-38 C66-4 63 39 53 92 Q48 114 35 91 L34 29Z" />
      <path className="livi-hair-strand" transform={withTransform("", state.transforms.hair)} d="M-30-57 Q-14-74 4-69" />
      <path className="livi-hair-strand" transform={withTransform("", state.transforms.hair)} d="M9-68 Q29-61 42-43" />
    </g>
  );
}

function DebugRig({ state }: { state: LiviState }) {
  return (
    <g className="livi-debug-rig" aria-label="Debug do rig">
      {[SHOULDER.left, SHOULDER.right, HIP.left, HIP.right].map((point, index) => <circle key={index} cx={point.x} cy={point.y} r="4" />)}
      <text x="12" y="24">DEBUG RIG</text>
      <text x="12" y="38">torso {state.torsoRotation.toFixed(0)}°</text>
    </g>
  );
}

export function LiviAvatar2D({ controller, className, debug = false }: LiviAvatar2DProps) {
  const state = useLiviState(controller);
  useControllerClock(controller);

  return (
    <div className={className ?? "livi-stage"}>
      <svg className="livi-svg" viewBox="0 0 400 560" role="img" aria-label="Livi, avatar profissional 2D articulada para Libras">
        <defs>
          <linearGradient id="livi-stage-gradient" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stopColor="#122348" /><stop offset="0.55" stopColor="#081329" /><stop offset="1" stopColor="#162952" /></linearGradient>
          <linearGradient id="livi-blazer-gradient" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stopColor="#2b5bb0" /><stop offset="0.52" stopColor="#214c9a" /><stop offset="1" stopColor="#183b7d" /></linearGradient>
          <linearGradient id="livi-blazer-sleeve-gradient" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stopColor="#183d84" /><stop offset="0.48" stopColor="#2b5aa6" /><stop offset="1" stopColor="#17376f" /></linearGradient>
          <linearGradient id="livi-skin-gradient" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stopColor="#f8d2b9" /><stop offset="0.58" stopColor="#efb899" /><stop offset="1" stopColor="#d99379" /></linearGradient>
          <linearGradient id="livi-hair-gradient" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stopColor="#34251f" /><stop offset="0.5" stopColor="#211714" /><stop offset="1" stopColor="#120d0d" /></linearGradient>
          <linearGradient id="livi-lip-gradient" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="#b96f78" /><stop offset="1" stopColor="#8e4e5d" /></linearGradient>
          <filter id="livi-soft-shadow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="3" /></filter>
        </defs>
        <rect width="400" height="560" rx="28" fill="url(#livi-stage-gradient)" />
        <path className="livi-stage-glow" d="M28 518 Q200 430 372 518" />
        <g data-part="livi" transform={withTransform(`rotate(${state.torsoRotation} 200 300)`, state.transforms.body)}>
          <Leg side="left" state={{ ...state.legs.left, transform: state.transforms.leftThigh, shinTransform: state.transforms.leftShin, footTransform: state.transforms.leftFoot }} />
          <Leg side="right" state={{ ...state.legs.right, transform: state.transforms.rightThigh, shinTransform: state.transforms.rightShin, footTransform: state.transforms.rightFoot }} />
          <Arm side="left" arm={{ ...state.arms.left, transform: state.transforms.leftUpperArm, forearmTransform: state.transforms.leftForearm, handTransform: state.transforms.leftHand }} hand={state.hands.left} />
          <Arm side="right" arm={{ ...state.arms.right, transform: state.transforms.rightUpperArm, forearmTransform: state.transforms.rightForearm, handTransform: state.transforms.rightHand }} hand={state.hands.right} />
          <g data-part="torso" transform={withTransform("", state.transforms.torso)}>
            <path className="livi-blazer-shadow" d="M130 438 Q127 280 149 222 Q176 204 200 207 Q224 204 251 222 Q273 280 270 438 Q200 478 130 438Z" />
            <path className="livi-blazer" d="M138 435 Q135 286 155 225 Q178 211 200 213 Q222 211 245 225 Q265 286 262 435 Q200 465 138 435Z" />
            <path className="livi-blouse" d="M180 218 Q200 244 220 218 L213 363 L187 363Z" />
            <path className="livi-lapel livi-lapel--left" d="M177 216 L199 249 L174 300 L151 233Z" />
            <path className="livi-lapel livi-lapel--right" d="M223 216 L201 249 L226 300 L249 233Z" />
            <path className="livi-blazer-opening" d="M200 249 L200 437" />
            <path className="livi-seam" d="M151 335 Q169 327 183 333" />
            <path className="livi-seam" d="M249 335 Q231 327 217 333" />
            <g data-part="badge" transform={withTransform("", state.transforms.badge)}><circle className="livi-badge" cx="200" cy="311" r="9" /><path className="livi-badge-mark" d="M196 311 Q200 305 204 311 Q200 317 196 311Z" /></g>
          </g>
          <g data-part="neck" transform={withTransform(`rotate(${state.neckRotation} 200 212)`, state.transforms.neck)}>
            <path className="livi-neck" d="M183 190 Q200 181 217 190 L218 239 Q200 250 182 239Z" />
            <Head state={state} />
          </g>
        </g>
        {debug ? <DebugRig state={state} /> : null}
        <text className="livi-stage-caption" x="24" y="535">LIVI · AVATAR PARA LIBRAS</text>
      </svg>
    </div>
  );
}
