import { describe, expect, it } from "vitest";

import {
  applyGroupMove,
  applyGroupRotate,
  applyGroupRotationOnce,
  applyGroupScale,
  beginGroupGesture,
  resolveGroupChrome,
  resolveGroupChromeFromMembers,
  resolveWorldFrames,
} from "./stageGroupGesture";

const ASPECT_16_9 = 16 / 9;

describe("stageGroupGesture", () => {
  const twoMembers = [
    { id: "a", frame: { x: 10, y: 10, w: 20, h: 20 }, rotation: 0 },
    { id: "b", frame: { x: 40, y: 10, w: 10, h: 10 }, rotation: 0 },
  ];

  it("begin + resolve identidade (sem mover) preserva frames", () => {
    const gesture = beginGroupGesture({
      members: twoMembers,
      slideAspect: 1,
      interactionStartFrame: { x: 10, y: 10, w: 40, h: 20 },
    });
    expect(gesture).not.toBeNull();
    const world = resolveWorldFrames(gesture!);
    expect(world.get("a")!.frame.x).toBeCloseTo(10, 5);
    expect(world.get("a")!.frame.w).toBeCloseTo(20, 5);
    expect(world.get("b")!.frame.x).toBeCloseTo(40, 5);
    expect(world.get("b")!.frame.w).toBeCloseTo(10, 5);
  });

  it("scale canto ×2: live ≡ resolve (razões relativas; sem dw absoluto)", () => {
    const gesture = beginGroupGesture({
      members: twoMembers,
      slideAspect: 1,
      interactionStartFrame: { x: 10, y: 10, w: 40, h: 20 },
      resizeHandle: "se",
    });
    expect(gesture!.dragFromChrome).toBe(true);
    const scaled = applyGroupScale(gesture!, { x: 10, y: 10, w: 80, h: 40 }, { lockAspect: true });
    const world = resolveWorldFrames(scaled);
    const a = world.get("a")!;
    const b = world.get("b")!;
    expect(a.frame.w).toBeCloseTo(40, 5);
    expect(a.frame.h).toBeCloseTo(40, 5);
    expect(b.frame.w).toBeCloseTo(20, 5);
    expect(b.frame.h).toBeCloseTo(20, 5);
    expect(a.frame.w / b.frame.w).toBeCloseTo(20 / 10, 5);
    // Mesma API no “release” — não há segundo algoritmo
    const again = resolveWorldFrames(scaled);
    expect(again.get("a")!.frame).toEqual(a.frame);
    expect(again.get("b")!.frame).toEqual(b.frame);
  });

  it("rotate 90° com aspect 16/9 preserva distância visual dos centros", () => {
    const members = [
      { id: "a", frame: { x: 0, y: 40, w: 20, h: 20 }, rotation: 0 },
      { id: "b", frame: { x: 80, y: 40, w: 20, h: 20 }, rotation: 0 },
    ];
    const gesture = beginGroupGesture({
      members,
      slideAspect: ASPECT_16_9,
      interactionStartFrame: { x: 0, y: 40, w: 100, h: 20 },
    });
    const rotated = applyGroupRotate(gesture!, 90);
    const world = resolveWorldFrames(rotated);
    const aY = world.get("a")!.frame.y + world.get("a")!.frame.h / 2;
    expect(aY).toBeCloseTo(50 - 40 * ASPECT_16_9, 4);
    expect(world.get("a")!.rotation).toBe(90);
    expect(world.get("b")!.rotation).toBe(90);
  });

  it("resolveGroupChrome.rotation === rotation world dos membros", () => {
    const gesture = beginGroupGesture({
      members: twoMembers,
      slideAspect: 1,
      interactionStartFrame: { x: 10, y: 10, w: 40, h: 20 },
    });
    const rotated = applyGroupRotate(gesture!, 45);
    const chrome = resolveGroupChrome(rotated);
    const world = resolveWorldFrames(rotated);
    expect(chrome.rotation).toBe(45);
    expect(world.get("a")!.rotation).toBe(45);
    expect(world.get("b")!.rotation).toBe(45);
  });

  it("move aplica o mesmo deslocamento a todos via group.frame", () => {
    const gesture = beginGroupGesture({
      members: twoMembers,
      slideAspect: 1,
      interactionStartFrame: { x: 10, y: 10, w: 40, h: 20 },
    });
    const moved = applyGroupMove(gesture!, { x: 15, y: 12, w: 40, h: 20 });
    const world = resolveWorldFrames(moved);
    expect(world.get("a")!.frame.x).toBeCloseTo(15, 5);
    expect(world.get("a")!.frame.y).toBeCloseTo(12, 5);
    expect(world.get("b")!.frame.x).toBeCloseTo(45, 5);
    expect(world.get("b")!.frame.y).toBeCloseTo(12, 5);
  });

  it("applyGroupRotationOnce (menu) orbita e soma rotação", () => {
    const next = applyGroupRotationOnce({
      members: [
        { id: "a", frame: { x: 0, y: 40, w: 20, h: 20 }, rotation: 0 },
        { id: "b", frame: { x: 80, y: 40, w: 20, h: 20 }, rotation: 10 },
      ],
      deltaDeg: 90,
      slideAspect: 1,
    });
    // rotações diferentes → chrome AABB; begin ainda orbita em torno do union
    expect(next.get("a")!.rotation).toBe(90);
    expect(next.get("b")!.rotation).toBe(100);
  });

  it("delta de rotação a partir de hit com rotação ≠ group", () => {
    const gesture = beginGroupGesture({
      members: [
        { id: "a", frame: { x: 10, y: 10, w: 20, h: 20 }, rotation: 10 },
        { id: "b", frame: { x: 40, y: 10, w: 10, h: 10 }, rotation: 0 },
      ],
      slideAspect: 1,
      interactionStartFrame: { x: 10, y: 10, w: 20, h: 20 },
      interactionStartRotation: 10,
    });
    expect(gesture!.startGroupRotation).toBe(0);
    expect(gesture!.interactionStartRotation).toBe(10);
    const pointerDelta = 25 - 10; // patch 25 a partir de start 10
    const next = applyGroupRotate(gesture!, gesture!.startGroupRotation + pointerDelta);
    const world = resolveWorldFrames(next);
    expect(world.get("a")!.rotation).toBe(25);
    expect(world.get("b")!.rotation).toBe(15);
  });

  it("chrome idle com rotação comum reconstrói frame + rotation", () => {
    const members = [
      { frame: { x: 40, y: 10, w: 20, h: 20 }, rotation: 90 },
      { frame: { x: 40, y: 70, w: 20, h: 20 }, rotation: 90 },
    ];
    const chrome = resolveGroupChromeFromMembers({ members, slideAspect: 1 });
    expect(chrome.rotation).toBe(90);
    expect(chrome.frame.w).toBeGreaterThan(0);
    expect(chrome.frame.h).toBeGreaterThan(0);
  });
});
