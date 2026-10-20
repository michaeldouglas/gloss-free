export type LiviSide = "left" | "right";

export type LiviFinger = "thumb" | "index" | "middle" | "ring" | "pinky";

export type LiviFingerJoint = "base" | "middle" | "tip" | "spread";

export type LiviHandShapeName = "open" | "fist" | "point" | "flat" | "l" | "custom";

export type LiviSegment =
  | "torso"
  | "head"
  | "neck"
  | "leftUpperArm"
  | "leftForearm"
  | "leftWrist"
  | "rightUpperArm"
  | "rightForearm"
  | "rightWrist"
  | "leftThigh"
  | "leftShin"
  | "leftAnkle"
  | "rightThigh"
  | "rightShin"
  | "rightAnkle";

export type LiviPart =
  | "body"
  | "torso"
  | "neck"
  | "head"
  | "leftUpperArm"
  | "leftForearm"
  | "leftHand"
  | "rightUpperArm"
  | "rightForearm"
  | "rightHand"
  | "leftThigh"
  | "leftShin"
  | "leftFoot"
  | "rightThigh"
  | "rightShin"
  | "rightFoot"
  | "hair"
  | "leftEye"
  | "rightEye"
  | "leftBrow"
  | "rightBrow"
  | "nose"
  | "mouth"
  | "leftEar"
  | "rightEar"
  | "badge";

export interface LiviPoint {
  x: number;
  y: number;
}

export interface LiviTransform {
  x: number;
  y: number;
  rotation: number;
  scaleX: number;
  scaleY: number;
}

export interface LiviArmState {
  upperArm: number;
  forearm: number;
  wrist: number;
  handTarget: LiviPoint;
}

export interface LiviLegState {
  thigh: number;
  shin: number;
  ankle: number;
}

export type LiviFingerState = Record<LiviFinger, number>;

export interface LiviFingerJoints {
  base: number;
  middle: number;
  tip: number;
  spread: number;
}

export type LiviFingerJointState = Record<LiviFinger, LiviFingerJoints>;

export interface LiviHandState {
  shape: LiviHandShapeName;
  fingers: LiviFingerState;
  joints: LiviFingerJointState;
}

export interface LiviExpressionState {
  smile: number;
  mouthOpen: number;
  mouthWidth: number;
  mouthCorner: number;
  cheekRaise: number;
  browRaise: number;
  browLeft: number;
  browRight: number;
  blinkLeft: number;
  blinkRight: number;
}

export interface LiviState {
  torsoRotation: number;
  headRotation: number;
  headTilt: number;
  neckRotation: number;
  arms: Record<LiviSide, LiviArmState>;
  hands: Record<LiviSide, LiviHandState>;
  legs: Record<LiviSide, LiviLegState>;
  transforms: Record<LiviPart, LiviTransform>;
  expression: LiviExpressionState;
  lookAt: LiviPoint;
}

export interface LiviPose {
  torsoRotation?: number;
  headRotation?: number;
  headTilt?: number;
  neckRotation?: number;
  arms?: Partial<Record<LiviSide, Partial<LiviArmState>>>;
  hands?: Partial<
    Record<
      LiviSide,
      {
        shape?: LiviHandShapeName;
        fingers?: Partial<LiviFingerState>;
        joints?: Partial<Record<LiviFinger, Partial<LiviFingerJoints>>>;
        wrist?: number;
      }
    >
  >;
  legs?: Partial<Record<LiviSide, Partial<LiviLegState>>>;
  transforms?: Partial<Record<LiviPart, Partial<LiviTransform>>>;
  expression?: Partial<LiviExpressionState>;
  lookAt?: Partial<LiviPoint>;
}

export interface LiviKeyframe {
  at: number;
  pose: LiviPose;
}

export interface LiviSequence {
  name?: string;
  duration: number;
  keyframes: readonly LiviKeyframe[];
  loop?: boolean;
}

export type LiviHandShape =
  | LiviHandShapeName
  | Partial<LiviFingerState>;

export interface LiviController {
  readonly state: LiviState;
  getState(): LiviState;
  subscribe(listener: () => void): () => void;
  setPose(pose: LiviPose): void;
  setSegmentRotation(segment: LiviSegment, degrees: number): void;
  setPartTransform(part: LiviPart, transform: Partial<LiviTransform>): void;
  setHandShape(side: LiviSide, shape: LiviHandShape): void;
  setFingerCurl(side: LiviSide, finger: LiviFinger, curl: number): void;
  setFingerJointRotation(side: LiviSide, finger: LiviFinger, joint: LiviFingerJoint, degrees: number): void;
  setHandPose(side: LiviSide, pose: {
    wrist?: number;
    fingers?: Partial<LiviFingerState>;
    joints?: Partial<Record<LiviFinger, Partial<LiviFingerJoints>>>;
  }): void;
  moveHand(side: LiviSide, target: LiviPoint): void;
  setExpression(name: keyof LiviExpressionState, value: number): void;
  lookAt(horizontal: number, vertical: number): void;
  blink(side?: LiviSide, durationMs?: number): void;
  execute(sequence: LiviSequence): void;
  sign(name: string): boolean;
  resetPose(): void;
  update(deltaSeconds: number): void;
}

export const LIVI_FINGERS: readonly LiviFinger[] = [
  "thumb",
  "index",
  "middle",
  "ring",
  "pinky",
];

export const LIVI_HAND_SHAPES: Readonly<Record<LiviHandShapeName, LiviFingerState>> = {
  open: { thumb: 0, index: 0, middle: 0, ring: 0, pinky: 0 },
  fist: { thumb: 0.85, index: 1, middle: 1, ring: 1, pinky: 1 },
  point: { thumb: 0.75, index: 0, middle: 1, ring: 1, pinky: 1 },
  flat: { thumb: 0.15, index: 0.05, middle: 0.05, ring: 0.05, pinky: 0.05 },
  l: { thumb: 0, index: 0, middle: 1, ring: 1, pinky: 1 },
  custom: { thumb: 0, index: 0, middle: 0, ring: 0, pinky: 0 },
};
