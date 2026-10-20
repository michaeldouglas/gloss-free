import {
  LIVI_HAND_SHAPES,
  type LiviArmState,
  type LiviController,
  type LiviExpressionState,
  type LiviFinger,
  type LiviFingerJoint,
  type LiviFingerJoints,
  type LiviFingerState,
  type LiviHandState,
  type LiviHandShape,
  type LiviKeyframe,
  type LiviLegState,
  type LiviPoint,
  type LiviPose,
  type LiviPart,
  type LiviSegment,
  type LiviSequence,
  type LiviSide,
  type LiviState,
  type LiviTransform,
} from "./livi-types";

const SHOULDER = { left: { x: 145, y: 238 }, right: { x: 255, y: 238 } } as const;
const UPPER_ARM_LENGTH = 82;
const FOREARM_LENGTH = 74;
const MIN_HAND_DISTANCE = 18;

const DEFAULT_FINGERS: LiviFingerState = {
  thumb: 0.12,
  index: 0.05,
  middle: 0.05,
  ring: 0.05,
  pinky: 0.08,
};

const DEFAULT_JOINTS: LiviFingerJoints = {
  base: 0,
  middle: 0,
  tip: 0,
  spread: 0,
};

const LIVI_PARTS: readonly LiviPart[] = [
  "body",
  "torso",
  "neck",
  "head",
  "leftUpperArm",
  "leftForearm",
  "leftHand",
  "rightUpperArm",
  "rightForearm",
  "rightHand",
  "leftThigh",
  "leftShin",
  "leftFoot",
  "rightThigh",
  "rightShin",
  "rightFoot",
  "hair",
  "leftEye",
  "rightEye",
  "leftBrow",
  "rightBrow",
  "nose",
  "mouth",
  "leftEar",
  "rightEar",
  "badge",
];

const IDENTITY_TRANSFORM: LiviTransform = {
  x: 0,
  y: 0,
  rotation: 0,
  scaleX: 1,
  scaleY: 1,
};

function defaultTransforms(): Record<LiviPart, LiviTransform> {
  return Object.fromEntries(LIVI_PARTS.map((part) => [part, { ...IDENTITY_TRANSFORM }])) as Record<LiviPart, LiviTransform>;
}

function defaultJoints(): LiviHandState["joints"] {
  return {
    thumb: { ...DEFAULT_JOINTS },
    index: { ...DEFAULT_JOINTS },
    middle: { ...DEFAULT_JOINTS },
    ring: { ...DEFAULT_JOINTS },
    pinky: { ...DEFAULT_JOINTS },
  };
}

function defaultState(): LiviState {
  return {
    torsoRotation: 0,
    headRotation: 0,
    headTilt: 0,
    neckRotation: 0,
    arms: {
      left: { upperArm: -18, forearm: 8, wrist: 0, handTarget: { x: 130, y: 390 } },
      right: { upperArm: 18, forearm: -8, wrist: 0, handTarget: { x: 270, y: 390 } },
    },
    hands: {
      left: { shape: "open", fingers: { ...DEFAULT_FINGERS }, joints: defaultJoints() },
      right: { shape: "open", fingers: { ...DEFAULT_FINGERS }, joints: defaultJoints() },
    },
    legs: {
      left: { thigh: -3, shin: 4, ankle: 0 },
      right: { thigh: 3, shin: -4, ankle: 0 },
    },
    expression: {
      smile: 0.35,
      mouthOpen: 0,
      mouthWidth: 0.5,
      mouthCorner: 0,
      cheekRaise: 0,
      browRaise: 0,
      browLeft: 0,
      browRight: 0,
      blinkLeft: 0,
      blinkRight: 0,
    },
    transforms: defaultTransforms(),
    lookAt: { x: 0, y: 0 },
  };
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function clampExpression(name: keyof LiviExpressionState, value: number): number {
  return ["mouthCorner", "browLeft", "browRight"].includes(name)
    ? clamp(value, -1, 1)
    : clamp(value, 0, 1);
}

function numberOr(value: number | undefined, fallback: number): number {
  return Number.isFinite(value) ? (value as number) : fallback;
}

function copyState(state: LiviState): LiviState {
  return {
    ...state,
    arms: {
      left: { ...state.arms.left, handTarget: { ...state.arms.left.handTarget } },
      right: { ...state.arms.right, handTarget: { ...state.arms.right.handTarget } },
    },
    hands: {
      left: {
        ...state.hands.left,
        fingers: { ...state.hands.left.fingers },
        joints: Object.fromEntries(Object.entries(state.hands.left.joints).map(([finger, joints]) => [finger, { ...joints }])) as LiviHandState["joints"],
      },
      right: {
        ...state.hands.right,
        fingers: { ...state.hands.right.fingers },
        joints: Object.fromEntries(Object.entries(state.hands.right.joints).map(([finger, joints]) => [finger, { ...joints }])) as LiviHandState["joints"],
      },
    },
    legs: {
      left: { ...state.legs.left },
      right: { ...state.legs.right },
    },
    transforms: Object.fromEntries(Object.entries(state.transforms).map(([part, transform]) => [part, { ...transform }])) as LiviState["transforms"],
    expression: { ...state.expression },
    lookAt: { ...state.lookAt },
  };
}

function mergePoses(base: LiviPose, patch: LiviPose): LiviPose {
  const result: LiviPose = { ...base, ...patch };
  result.arms = { ...base.arms, ...patch.arms };
  result.hands = { ...base.hands, ...patch.hands };
  result.legs = { ...base.legs, ...patch.legs };
  result.transforms = { ...base.transforms, ...patch.transforms };
  result.expression = { ...base.expression, ...patch.expression };
  result.lookAt = {
    x: base.lookAt?.x ?? patch.lookAt?.x ?? 0,
    y: base.lookAt?.y ?? patch.lookAt?.y ?? 0,
  };

  for (const side of ["left", "right"] as const) {
    result.arms[side] = {
      ...base.arms?.[side],
      ...patch.arms?.[side],
      handTarget: {
        x: base.arms?.[side]?.handTarget?.x ?? patch.arms?.[side]?.handTarget?.x ?? 0,
        y: base.arms?.[side]?.handTarget?.y ?? patch.arms?.[side]?.handTarget?.y ?? 0,
      },
    };
    result.hands[side] = {
      ...base.hands?.[side],
      ...patch.hands?.[side],
      fingers: {
        ...base.hands?.[side]?.fingers,
        ...patch.hands?.[side]?.fingers,
      },
      joints: Object.fromEntries(
        (Object.keys({
          ...base.hands?.[side]?.joints,
          ...patch.hands?.[side]?.joints,
        }) as LiviFinger[]).map((finger) => [
          finger,
          {
            ...base.hands?.[side]?.joints?.[finger],
            ...patch.hands?.[side]?.joints?.[finger],
          },
        ]),
      ) as LiviHandState["joints"],
    };
    result.legs[side] = { ...base.legs?.[side], ...patch.legs?.[side] };
  }

  for (const part of LIVI_PARTS) {
    result.transforms[part] = {
      ...base.transforms?.[part],
      ...patch.transforms?.[part],
    };
  }

  return result;
}

function lerp(a: number | undefined, b: number | undefined, progress: number): number | undefined {
  if (a === undefined) return b;
  if (b === undefined) return a;
  return a + (b - a) * progress;
}

function interpolatePoses(from: LiviPose, to: LiviPose, progress: number): LiviPose {
  const result = mergePoses(from, to);
  const numeric = (key: keyof LiviPose) => {
    const fromValue = from[key];
    const toValue = to[key];
    if (typeof fromValue === "number" || typeof toValue === "number") {
      (result as Record<string, unknown>)[key] = lerp(
        fromValue as number | undefined,
        toValue as number | undefined,
        progress,
      );
    }
  };

  numeric("torsoRotation");
  numeric("headRotation");
  numeric("headTilt");
  numeric("neckRotation");

  for (const side of ["left", "right"] as const) {
    const fromArm = from.arms?.[side];
    const toArm = to.arms?.[side];
    const arm = result.arms?.[side];
    if (arm) {
      arm.upperArm = lerp(fromArm?.upperArm, toArm?.upperArm, progress) ?? arm.upperArm;
      arm.forearm = lerp(fromArm?.forearm, toArm?.forearm, progress) ?? arm.forearm;
      arm.wrist = lerp(fromArm?.wrist, toArm?.wrist, progress) ?? arm.wrist;
      if (fromArm?.handTarget || toArm?.handTarget) {
        const target = arm.handTarget ?? { x: 0, y: 0 };
        arm.handTarget = {
          x: lerp(fromArm?.handTarget?.x, toArm?.handTarget?.x, progress) ?? target.x,
          y: lerp(fromArm?.handTarget?.y, toArm?.handTarget?.y, progress) ?? target.y,
        };
      }
    }

    const fromHand = from.hands?.[side];
    const toHand = to.hands?.[side];
    const hand = result.hands?.[side];
    if (hand) {
      const fingers = hand.fingers ?? { ...LIVI_HAND_SHAPES.custom };
      hand.fingers = fingers;
      for (const finger of Object.keys(fingers) as LiviFinger[]) {
        fingers[finger] =
          lerp(fromHand?.fingers?.[finger], toHand?.fingers?.[finger], progress) ??
          fingers[finger];
      }
      const fromJoints = fromHand?.joints;
      const toJoints = toHand?.joints;
      const joints = hand.joints ?? defaultJoints();
      for (const finger of Object.keys(joints) as LiviFinger[]) {
        const fingerJoints = joints[finger] ?? { ...DEFAULT_JOINTS };
        for (const joint of ["base", "middle", "tip", "spread"] as const) {
          fingerJoints[joint] =
            lerp(fromJoints?.[finger]?.[joint], toJoints?.[finger]?.[joint], progress) ??
            fingerJoints[joint];
        }
        joints[finger] = fingerJoints;
      }
      hand.joints = joints;
    }

    const fromLeg = from.legs?.[side];
    const toLeg = to.legs?.[side];
    const leg = result.legs?.[side];
    if (leg) {
      leg.thigh = lerp(fromLeg?.thigh, toLeg?.thigh, progress) ?? leg.thigh;
      leg.shin = lerp(fromLeg?.shin, toLeg?.shin, progress) ?? leg.shin;
      leg.ankle = lerp(fromLeg?.ankle, toLeg?.ankle, progress) ?? leg.ankle;
    }
  }

  const expression = result.expression ?? {};
  result.expression = expression;
  for (const name of [
    "smile",
    "mouthOpen",
    "mouthWidth",
    "mouthCorner",
    "cheekRaise",
    "browRaise",
    "browLeft",
    "browRight",
    "blinkLeft",
    "blinkRight",
  ] as const) {
    expression[name] =
      lerp(from.expression?.[name], to.expression?.[name], progress) ?? expression[name];
  }
  for (const part of LIVI_PARTS) {
    const fromTransform = from.transforms?.[part];
    const toTransform = to.transforms?.[part];
    const transform = result.transforms?.[part] ?? { ...IDENTITY_TRANSFORM };
    for (const key of ["x", "y", "rotation", "scaleX", "scaleY"] as const) {
      transform[key] = lerp(fromTransform?.[key], toTransform?.[key], progress) ?? transform[key];
    }
    result.transforms = result.transforms ?? defaultTransforms();
    result.transforms[part] = transform;
  }
  if (from.lookAt || to.lookAt) {
    result.lookAt = {
      x: lerp(from.lookAt?.x, to.lookAt?.x, progress) ?? result.lookAt?.x ?? 0,
      y: lerp(from.lookAt?.y, to.lookAt?.y, progress) ?? result.lookAt?.y ?? 0,
    };
  }

  return result;
}

function shapeToFingers(shape: LiviHandShape): { shape: "custom" | "open" | "fist" | "point" | "flat" | "l"; fingers: LiviFingerState } {
  if (typeof shape === "string") {
    return { shape, fingers: { ...LIVI_HAND_SHAPES[shape] } };
  }
  return { shape: "custom", fingers: { ...LIVI_HAND_SHAPES.custom, ...shape } };
}

function jointsFromFingers(fingers: LiviFingerState): LiviHandState["joints"] {
  return Object.fromEntries(
    Object.entries(fingers).map(([finger, curl]) => [
      finger,
      {
        base: curl * 70,
        middle: curl * 78,
        tip: curl * 58,
        spread: 0,
      },
    ]),
  ) as LiviHandState["joints"];
}

function solveArm(side: LiviSide, target: LiviPoint): Pick<LiviArmState, "upperArm" | "forearm"> {
  const shoulder = SHOULDER[side];
  const dx = target.x - shoulder.x;
  const dy = target.y - shoulder.y;
  const distance = clamp(Math.hypot(dx, dy), MIN_HAND_DISTANCE, UPPER_ARM_LENGTH + FOREARM_LENGTH - 1);
  const direction = Math.atan2(dx, dy);
  const upperOffset = Math.acos(
    clamp(
      (UPPER_ARM_LENGTH ** 2 + distance ** 2 - FOREARM_LENGTH ** 2) /
        (2 * UPPER_ARM_LENGTH * distance),
      -1,
      1,
    ),
  );
  const bend = side === "left" ? -1 : 1;
  const upperArm = ((direction + bend * upperOffset) * 180) / Math.PI;
  const elbowX = shoulder.x + UPPER_ARM_LENGTH * Math.sin((upperArm * Math.PI) / 180);
  const elbowY = shoulder.y + UPPER_ARM_LENGTH * Math.cos((upperArm * Math.PI) / 180);
  const absoluteForearm = (Math.atan2(target.x - elbowX, target.y - elbowY) * 180) / Math.PI;

  return { upperArm, forearm: absoluteForearm - upperArm };
}

const SIGN_LIBRARY: Readonly<Record<string, LiviSequence>> = {
  hello: {
    name: "hello",
    duration: 1500,
    keyframes: [
      {
        at: 0,
        pose: {
          arms: { right: { upperArm: -62, forearm: 12, wrist: 0 } },
          hands: { right: { shape: "open" } },
          headRotation: 3,
        },
      },
      { at: 500, pose: { arms: { right: { wrist: -24 } } } },
      { at: 820, pose: { arms: { right: { wrist: 24 } } } },
      { at: 1140, pose: { arms: { right: { wrist: -20 } } } },
      {
        at: 1500,
        pose: {
          arms: { right: { upperArm: 18, forearm: -8, wrist: 0 } },
          headRotation: 0,
        },
      },
    ],
  },
  wave: {
    name: "wave",
    duration: 1000,
    keyframes: [
      { at: 0, pose: { arms: { right: { upperArm: -50, forearm: 8 } }, hands: { right: { shape: "open" } } } },
      { at: 250, pose: { arms: { right: { wrist: -28 } } } },
      { at: 500, pose: { arms: { right: { wrist: 28 } } } },
      { at: 750, pose: { arms: { right: { wrist: -28 } } } },
      { at: 1000, pose: { arms: { right: { upperArm: 18, forearm: -8, wrist: 0 } } } },
    ],
  },
};

interface ActiveSequence {
  sequence: LiviSequence;
  frames: readonly LiviKeyframe[];
  elapsed: number;
}

interface BlinkAnimation {
  side: LiviSide;
  elapsed: number;
  duration: number;
}

export class Livi2DController implements LiviController {
  state: LiviState = defaultState();

  private readonly listeners = new Set<() => void>();
  private activeSequence: ActiveSequence | null = null;
  private readonly blinks: BlinkAnimation[] = [];

  getState(): LiviState {
    return this.state;
  }

  subscribe(listener: () => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  setPose(pose: LiviPose): void {
    this.activeSequence = null;
    this.applyPose(pose);
    this.notify();
  }

  setSegmentRotation(segment: LiviSegment, degrees: number): void {
    const value = clamp(numberOr(degrees, 0), -180, 180);
    const direct: Partial<Record<LiviSegment, keyof LiviPose>> = {
      torso: "torsoRotation",
      head: "headRotation",
      neck: "neckRotation",
    };
    if (direct[segment]) {
      this.setPose({ [direct[segment] as string]: value } as LiviPose);
      return;
    }

    const armMatch = /^(left|right)(UpperArm|Forearm|Wrist)$/.exec(segment);
    if (armMatch) {
      const side = armMatch[1] as LiviSide;
      const key = armMatch[2] === "UpperArm" ? "upperArm" : armMatch[2] === "Forearm" ? "forearm" : "wrist";
      this.setPose({ arms: { [side]: { [key]: value } } });
      return;
    }

    const legMatch = /^(left|right)(Thigh|Shin|Ankle)$/.exec(segment);
    if (legMatch) {
      const side = legMatch[1] as LiviSide;
      const key = legMatch[2].toLowerCase() as keyof LiviLegState;
      this.setPose({ legs: { [side]: { [key]: value } } });
    }
  }

  setPartTransform(part: LiviPart, transform: Partial<LiviTransform>): void {
    this.setPose({
      transforms: {
        [part]: {
          x: transform.x,
          y: transform.y,
          rotation: transform.rotation,
          scaleX: transform.scaleX,
          scaleY: transform.scaleY,
        },
      },
    });
  }

  setHandShape(side: LiviSide, shape: LiviHandShape): void {
    const resolved = shapeToFingers(shape);
    this.setPose({ hands: { [side]: { ...resolved, joints: jointsFromFingers(resolved.fingers) } } });
  }

  setFingerCurl(side: LiviSide, finger: LiviFinger, curl: number): void {
    const safeCurl = clamp(curl, 0, 1);
    this.setPose({
      hands: {
        [side]: {
          shape: "custom",
          fingers: { [finger]: safeCurl },
          joints: { [finger]: jointsFromFingers({ [finger]: safeCurl } as LiviFingerState)[finger] },
        },
      },
    });
  }

  setFingerJointRotation(side: LiviSide, finger: LiviFinger, joint: LiviFingerJoint, degrees: number): void {
    const limit = joint === "spread" ? 35 : 120;
    this.setPose({
      hands: {
        [side]: {
          shape: "custom",
          joints: { [finger]: { [joint]: clamp(numberOr(degrees, 0), -limit, limit) } },
        },
      },
    });
  }

  setHandPose(side: LiviSide, pose: {
    wrist?: number;
    fingers?: Partial<LiviFingerState>;
    joints?: Partial<Record<LiviFinger, Partial<LiviFingerJoints>>>;
  }): void {
    this.setPose({ hands: { [side]: { wrist: pose.wrist, fingers: pose.fingers, joints: pose.joints, shape: "custom" } } });
    if (pose.wrist !== undefined) this.setPose({ arms: { [side]: { wrist: pose.wrist } } });
  }

  moveHand(side: LiviSide, target: LiviPoint): void {
    const safeTarget = { x: clamp(target.x, 35, 365), y: clamp(target.y, 185, 500) };
    const solved = solveArm(side, safeTarget);
    this.setPose({ arms: { [side]: { ...solved, handTarget: safeTarget } } });
  }

  setExpression(name: keyof LiviExpressionState, value: number): void {
    this.setPose({ expression: { [name]: clampExpression(name, value) } });
  }

  lookAt(horizontal: number, vertical: number): void {
    this.setPose({ lookAt: { x: clamp(horizontal, -1, 1), y: clamp(vertical, -1, 1) } });
  }

  blink(side: LiviSide = "left", durationMs = 180): void {
    this.activeSequence = null;
    const existing = this.blinks.find((blink) => blink.side === side);
    if (existing) existing.elapsed = 0;
    else this.blinks.push({ side, elapsed: 0, duration: Math.max(80, durationMs) });
    this.applyExpression(side === "left" ? "blinkLeft" : "blinkRight", 1);
    this.notify();
  }

  execute(sequence: LiviSequence): void {
    const frames = this.cumulativeFrames(sequence);
    this.activeSequence = { sequence, frames, elapsed: 0 };
    const first = frames[0];
    if (first) this.applyPose(first.pose);
    this.notify();
  }

  sign(name: string): boolean {
    const sequence = SIGN_LIBRARY[name.trim().toLowerCase()];
    if (!sequence) return false;
    this.execute(sequence);
    return true;
  }

  resetPose(): void {
    this.activeSequence = null;
    this.blinks.length = 0;
    this.state = defaultState();
    this.notify();
  }

  update(deltaSeconds: number): void {
    const delta = Math.max(0, deltaSeconds);
    let changed = false;

    if (this.activeSequence) {
      const active = this.activeSequence;
      active.elapsed += delta * 1000;
      if (active.elapsed >= active.sequence.duration) {
        this.applyPose(active.frames.at(-1)?.pose ?? {});
        if (active.sequence.loop) active.elapsed = 0;
        else this.activeSequence = null;
      } else {
        this.applyPose(this.sampleSequence(active.frames, active.elapsed));
      }
      changed = true;
    }

    for (let index = this.blinks.length - 1; index >= 0; index -= 1) {
      const blink = this.blinks[index];
      blink.elapsed += delta * 1000;
      const progress = clamp(blink.elapsed / blink.duration, 0, 1);
      const value = progress < 0.35 ? progress / 0.35 : 1 - (progress - 0.35) / 0.65;
      this.applyExpression(blink.side === "left" ? "blinkLeft" : "blinkRight", value);
      changed = true;
      if (progress >= 1) this.blinks.splice(index, 1);
    }

    if (changed) this.notify();
  }

  private applyExpression(name: keyof LiviExpressionState, value: number): void {
    const next = copyState(this.state);
    next.expression[name] = clamp(value, 0, 1);
    this.state = next;
  }

  private applyPose(pose: LiviPose): void {
    const next = copyState(this.state);
    if (pose.torsoRotation !== undefined) next.torsoRotation = clamp(pose.torsoRotation, -40, 40);
    if (pose.headRotation !== undefined) next.headRotation = clamp(pose.headRotation, -45, 45);
    if (pose.headTilt !== undefined) next.headTilt = clamp(pose.headTilt, -35, 35);
    if (pose.neckRotation !== undefined) next.neckRotation = clamp(pose.neckRotation, -25, 25);

    for (const side of ["left", "right"] as const) {
      const arm = pose.arms?.[side];
      if (arm) {
        next.arms[side] = {
          ...next.arms[side],
          ...arm,
          upperArm: arm.upperArm === undefined ? next.arms[side].upperArm : clamp(arm.upperArm, -180, 180),
          forearm: arm.forearm === undefined ? next.arms[side].forearm : clamp(arm.forearm, -180, 180),
          wrist: arm.wrist === undefined ? next.arms[side].wrist : clamp(arm.wrist, -90, 90),
          handTarget: { ...next.arms[side].handTarget, ...arm.handTarget },
        };
      }
      const hand = pose.hands?.[side];
      if (hand) {
        next.hands[side] = {
          ...next.hands[side],
          ...hand,
          fingers: { ...next.hands[side].fingers, ...hand.fingers },
          joints: { ...next.hands[side].joints },
        };
        for (const finger of Object.keys(hand.joints ?? {}) as LiviFinger[]) {
          next.hands[side].joints[finger] = {
            ...next.hands[side].joints[finger],
            ...hand.joints?.[finger],
          };
        }
        for (const finger of Object.keys(next.hands[side].fingers) as LiviFinger[]) {
          next.hands[side].fingers[finger] = clamp(next.hands[side].fingers[finger], 0, 1);
          const explicitJoints = hand.joints?.[finger];
          if (!explicitJoints && hand.fingers?.[finger] !== undefined) {
            next.hands[side].joints[finger] = jointsFromFingers(next.hands[side].fingers)[finger];
          }
          for (const joint of ["base", "middle", "tip", "spread"] as const) {
            const limit = joint === "spread" ? 35 : 120;
            next.hands[side].joints[finger][joint] = clamp(next.hands[side].joints[finger][joint], -limit, limit);
          }
        }
      }
      const leg = pose.legs?.[side];
      if (leg) {
        next.legs[side] = {
          ...next.legs[side],
          ...leg,
          thigh: leg.thigh === undefined ? next.legs[side].thigh : clamp(leg.thigh, -60, 60),
          shin: leg.shin === undefined ? next.legs[side].shin : clamp(leg.shin, -90, 90),
          ankle: leg.ankle === undefined ? next.legs[side].ankle : clamp(leg.ankle, -45, 45),
        };
      }
    }

    if (pose.transforms) {
      for (const part of LIVI_PARTS) {
        const transform = pose.transforms[part];
        if (!transform) continue;
        next.transforms[part] = {
          ...next.transforms[part],
          x: transform.x === undefined ? next.transforms[part].x : clamp(transform.x, -250, 250),
          y: transform.y === undefined ? next.transforms[part].y : clamp(transform.y, -250, 250),
          rotation: transform.rotation === undefined ? next.transforms[part].rotation : clamp(transform.rotation, -360, 360),
          scaleX: transform.scaleX === undefined ? next.transforms[part].scaleX : clamp(transform.scaleX, 0.1, 3),
          scaleY: transform.scaleY === undefined ? next.transforms[part].scaleY : clamp(transform.scaleY, 0.1, 3),
        };
      }
    }

    if (pose.expression) {
      next.expression = { ...next.expression, ...pose.expression };
      for (const name of Object.keys(next.expression) as Array<keyof LiviExpressionState>) {
        next.expression[name] = clampExpression(name, next.expression[name]);
      }
    }
    if (pose.lookAt) {
      next.lookAt = {
        x: clamp(numberOr(pose.lookAt.x, next.lookAt.x), -1, 1),
        y: clamp(numberOr(pose.lookAt.y, next.lookAt.y), -1, 1),
      };
    }
    this.state = next;
  }

  private cumulativeFrames(sequence: LiviSequence): LiviKeyframe[] {
    let accumulated: LiviPose = {};
    return [...sequence.keyframes]
      .sort((a, b) => a.at - b.at)
      .map((frame) => {
        accumulated = mergePoses(accumulated, frame.pose);
        return { at: clamp(frame.at, 0, sequence.duration), pose: accumulated };
      });
  }

  private sampleSequence(frames: readonly LiviKeyframe[], elapsed: number): LiviPose {
    if (frames.length === 0) return {};
    if (elapsed <= frames[0].at) return frames[0].pose;
    for (let index = 1; index < frames.length; index += 1) {
      const next = frames[index];
      const previous = frames[index - 1];
      if (elapsed <= next.at) {
        const span = next.at - previous.at || 1;
        return interpolatePoses(previous.pose, next.pose, (elapsed - previous.at) / span);
      }
    }
    return frames.at(-1)?.pose ?? {};
  }

  private notify(): void {
    for (const listener of this.listeners) listener();
  }
}
