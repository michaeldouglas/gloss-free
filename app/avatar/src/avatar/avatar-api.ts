import type {
  LiviController,
  LiviExpressionState,
  LiviFinger,
  LiviFingerJoint,
  LiviHandShape,
  LiviPoint,
  LiviPose,
  LiviPart,
  LiviSegment,
  LiviSequence,
  LiviSide,
  LiviTransform,
} from "./2d/livi-types";

/** Public imperative API for browser integrations and future Libras engines. */
export interface LiviJavaScriptApi {
  readonly controller: LiviController;
  readonly getState: LiviController["getState"];
  readonly setPose: (pose: LiviPose) => void;
  readonly setSegmentRotation: (segment: LiviSegment, degrees: number) => void;
  readonly setPartTransform: (part: LiviPart, transform: Partial<LiviTransform>) => void;
  readonly setHandShape: (side: LiviSide, shape: LiviHandShape) => void;
  readonly setFingerCurl: (side: LiviSide, finger: LiviFinger, curl: number) => void;
  readonly setFingerJointRotation: (side: LiviSide, finger: LiviFinger, joint: LiviFingerJoint, degrees: number) => void;
  readonly setHandPose: LiviController["setHandPose"];
  readonly moveHand: (side: LiviSide, target: LiviPoint) => void;
  readonly setExpression: (name: keyof LiviExpressionState, value: number) => void;
  readonly lookAt: (horizontal: number, vertical: number) => void;
  readonly blink: (side?: LiviSide, durationMs?: number) => void;
  readonly execute: (sequence: LiviSequence) => void;
  readonly sign: (name: string) => boolean;
  readonly resetPose: () => void;
}

export function createLiviJavaScriptApi(controller: LiviController): LiviJavaScriptApi {
  return {
    controller,
    getState: controller.getState.bind(controller),
    setPose: controller.setPose.bind(controller),
    setSegmentRotation: controller.setSegmentRotation.bind(controller),
    setPartTransform: controller.setPartTransform.bind(controller),
    setHandShape: controller.setHandShape.bind(controller),
    setFingerCurl: controller.setFingerCurl.bind(controller),
    setFingerJointRotation: controller.setFingerJointRotation.bind(controller),
    setHandPose: controller.setHandPose.bind(controller),
    moveHand: controller.moveHand.bind(controller),
    setExpression: controller.setExpression.bind(controller),
    lookAt: controller.lookAt.bind(controller),
    blink: controller.blink.bind(controller),
    execute: controller.execute.bind(controller),
    sign: controller.sign.bind(controller),
    resetPose: controller.resetPose.bind(controller),
  };
}
