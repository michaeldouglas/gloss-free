import { describe, expect, it } from "vitest";
import { Livi2DController } from "../../src/avatar/2d/livi-controller";

describe("Livi2DController", () => {
  it("controla segmentos, dedos e expressão no runtime SVG", () => {
    const controller = new Livi2DController();

    controller.setSegmentRotation("rightUpperArm", -54);
    controller.setFingerCurl("right", "index", 1);
    controller.setExpression("smile", 1);

    expect(controller.state.arms.right.upperArm).toBe(-54);
    expect(controller.state.hands.right.fingers.index).toBe(1);
    expect(controller.state.expression.smile).toBe(1);
  });

  it("expõe controle individual das falanges e transformação livre das partes", () => {
    const controller = new Livi2DController();

    controller.setFingerJointRotation("right", "index", "middle", 48);
    controller.setFingerJointRotation("right", "index", "tip", -12);
    controller.setPartTransform("rightHand", { x: 14, y: -8, rotation: 22, scaleX: 1.2 });
    controller.setExpression("browLeft", -0.7);

    expect(controller.state.hands.right.joints.index.middle).toBe(48);
    expect(controller.state.hands.right.joints.index.tip).toBe(-12);
    expect(controller.state.transforms.rightHand).toMatchObject({ x: 14, y: -8, rotation: 22, scaleX: 1.2, scaleY: 1 });
    expect(controller.state.expression.browLeft).toBe(-0.7);
  });

  it("resolve a posição da mão com cinemática planar de dois segmentos", () => {
    const controller = new Livi2DController();

    controller.moveHand("left", { x: 92, y: 305 });

    expect(controller.state.arms.left.handTarget).toEqual({ x: 92, y: 305 });
    expect(controller.state.arms.left.upperArm).not.toBe(-18);
    expect(Number.isFinite(controller.state.arms.left.forearm)).toBe(true);
  });

  it("interpola uma sequência e disponibiliza sinais de demonstração", () => {
    const controller = new Livi2DController();

    controller.execute({
      duration: 1_000,
      keyframes: [
        { at: 0, pose: { headRotation: 0 } },
        { at: 1_000, pose: { headRotation: 30 } },
      ],
    });
    controller.update(0.5);

    expect(controller.state.headRotation).toBeCloseTo(15);
    expect(controller.sign("hello")).toBe(true);
    expect(controller.sign("unknown-sign")).toBe(false);
  });

  it("fecha e reabre um olho durante o piscar", () => {
    const controller = new Livi2DController();

    controller.blink("right", 100);
    controller.update(0.05);
    expect(controller.state.expression.blinkRight).toBeGreaterThan(0);

    controller.update(0.1);
    expect(controller.state.expression.blinkRight).toBe(0);
  });
});
