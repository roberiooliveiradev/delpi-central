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
      groupRotation: 0,
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

  it("após girar, resize pelo chrome (startFrame=chrome) mantém razões e live≡release", () => {
    const aspect = 16 / 9;
    const start = [
      { id: "a", frame: { x: 10, y: 20, w: 20, h: 15 }, rotation: 0 },
      { id: "b", frame: { x: 45, y: 25, w: 25, h: 20 }, rotation: 0 },
    ];
    const rotated = resolveWorldFrames(
      applyGroupRotate(
        beginGroupGesture({ members: start, slideAspect: aspect })!,
        40,
      ),
    );
    const members = [...rotated.entries()].map(([id, update]) => ({
      id,
      frame: update.frame,
      rotation: update.rotation,
    }));
    const chrome = resolveGroupChromeFromMembers({
      members: members.map((m) => ({ frame: m.frame, rotation: m.rotation })),
      slideAspect: aspect,
    });
    const gesture = beginGroupGesture({
      members,
      slideAspect: aspect,
      interactionStartFrame: chrome.frame,
      resizeHandle: "se",
    });
    expect(gesture!.dragFromChrome).toBe(true);
    expect(gesture!.group.rotation).toBeCloseTo(40, 5);

    const nextChrome = {
      ...chrome.frame,
      w: chrome.frame.w * 1.5,
      h: chrome.frame.h * 1.5,
    };
    const scaled = applyGroupScale(gesture!, nextChrome, { lockAspect: true });
    const live = resolveWorldFrames(scaled);
    const release = resolveWorldFrames(scaled);
    const a = live.get("a")!;
    const b = live.get("b")!;
    expect(a.frame.w / b.frame.w).toBeCloseTo(20 / 25, 5);
    expect(release.get("a")!.frame).toEqual(a.frame);
    expect(a.rotation).toBeCloseTo(40, 5);
    expect(b.rotation).toBeCloseTo(40, 5);
  });

  it("round-trip identidade após rotação + move", () => {
    const aspect = 16 / 9;
    const start = [
      { id: "a", frame: { x: 10, y: 20, w: 20, h: 15 }, rotation: 0 },
      { id: "b", frame: { x: 45, y: 25, w: 25, h: 20 }, rotation: 0 },
    ];
    let gesture = beginGroupGesture({ members: start, slideAspect: aspect })!;
    gesture = applyGroupRotate(gesture, 25);
    const chrome = resolveGroupChrome(gesture);
    gesture = beginGroupGesture({
      members: [...resolveWorldFrames(gesture).entries()].map(([id, u]) => ({
        id,
        frame: u.frame,
        rotation: u.rotation,
      })),
      slideAspect: aspect,
      interactionStartFrame: chrome.frame,
    })!;
    const before = resolveWorldFrames(gesture);
    const moved = applyGroupMove(gesture, {
      ...gesture.interactionStartFrame,
      x: gesture.interactionStartFrame.x + 3,
      y: gesture.interactionStartFrame.y + 2,
    });
    const after = resolveWorldFrames(moved);
    for (const id of ["a", "b"] as const) {
      expect(after.get(id)!.frame.x - before.get(id)!.frame.x).toBeCloseTo(3, 5);
      expect(after.get(id)!.frame.y - before.get(id)!.frame.y).toBeCloseTo(2, 5);
      expect(after.get(id)!.rotation).toBe(before.get(id)!.rotation);
    }
  });

  it("preserva ângulo pai no release com rotações locais diferentes", () => {
    const aspect = 16 / 9;
    const start = [
      { id: "card", frame: { x: 10, y: 20, w: 40, h: 30 }, rotation: 0 },
      { id: "tag", frame: { x: 20, y: 15, w: 18, h: 6 }, rotation: 12 },
    ];
    const gesture = applyGroupRotate(
      beginGroupGesture({
        members: start,
        slideAspect: aspect,
        groupRotation: 0,
      })!,
      35,
    );
    const baked = [...resolveWorldFrames(gesture).entries()].map(([id, update]) => ({
      id,
      frame: update.frame,
      rotation: update.rotation,
    }));

    /* Reabre/reseleciona após o pointerup usando o contrato persistido. */
    const restored = beginGroupGesture({
      members: baked,
      slideAspect: aspect,
      groupRotation: 35,
    })!;
    expect(restored.group.rotation).toBeCloseTo(35, 5);
    expect(restored.localFrames.get("card")!.rotation).toBeCloseTo(0, 5);
    expect(restored.localFrames.get("tag")!.rotation).toBeCloseTo(12, 5);

    const roundTrip = resolveWorldFrames(restored);
    for (const member of baked) {
      const update = roundTrip.get(member.id)!;
      expect(update.frame.x).toBeCloseTo(member.frame.x, 5);
      expect(update.frame.y).toBeCloseTo(member.frame.y, 5);
      expect(update.rotation).toBeCloseTo(member.rotation, 5);
    }
  });

  it("migra grupo legado sem metadata pelo ângulo do membro dominante", () => {
    const gesture = beginGroupGesture({
      members: [
        {
          id: "card",
          frame: { x: 10, y: 20, w: 50, h: 40 },
          rotation: 28,
        },
        {
          id: "tag-local",
          frame: { x: 20, y: 15, w: 16, h: 6 },
          rotation: 40,
        },
      ],
      slideAspect: 16 / 9,
    })!;
    expect(gesture.group.rotation).toBe(28);
    expect(gesture.localFrames.get("card")!.rotation).toBe(0);
    expect(gesture.localFrames.get("tag-local")!.rotation).toBe(12);
  });
});

describe("applyGroupScale eixos livres (multi-seleção)", () => {
  const members = [
    { id: "a", frame: { x: 10, y: 10, w: 20, h: 10 }, rotation: 0 },
    { id: "b", frame: { x: 10, y: 25, w: 30, h: 10 }, rotation: 0 },
  ];

  it("borda sul: altera só altura do grupo (não trava aspecto)", () => {
    const gesture = beginGroupGesture({
      members,
      slideAspect: 16 / 9,
      interactionStartFrame: { ...members[0]!.frame },
      resizeHandle: "s",
    });
    expect(gesture).not.toBeNull();
    const start = gesture!;
    const startW = start.group.frame.w;
    const startH = start.group.frame.h;
    const tallerMember = {
      ...members[0]!.frame,
      h: members[0]!.frame.h * 1.5,
    };
    const next = applyGroupScale(start, tallerMember);
    expect(next.group.frame.w).toBeCloseTo(startW, 5);
    expect(next.group.frame.h).toBeGreaterThan(startH);
  });

  it("borda leste: altera só largura do grupo", () => {
    const gesture = beginGroupGesture({
      members,
      slideAspect: 16 / 9,
      interactionStartFrame: { ...members[0]!.frame },
      resizeHandle: "e",
    });
    expect(gesture).not.toBeNull();
    const start = gesture!;
    const startW = start.group.frame.w;
    const startH = start.group.frame.h;
    const widerMember = {
      ...members[0]!.frame,
      w: members[0]!.frame.w * 1.5,
    };
    const next = applyGroupScale(start, widerMember);
    expect(next.group.frame.h).toBeCloseTo(startH, 5);
    expect(next.group.frame.w).toBeGreaterThan(startW);
  });

  it("borda com lockAspect: força uniforme", () => {
    const gesture = beginGroupGesture({
      members,
      slideAspect: 16 / 9,
      interactionStartFrame: { ...members[0]!.frame },
      resizeHandle: "s",
    });
    expect(gesture).not.toBeNull();
    const start = gesture!;
    const aspect = start.group.frame.w / start.group.frame.h;
    const next = applyGroupScale(
      start,
      { ...members[0]!.frame, h: members[0]!.frame.h * 2 },
      { lockAspect: true },
    );
    expect(next.group.frame.w / next.group.frame.h).toBeCloseTo(aspect, 4);
  });
});

