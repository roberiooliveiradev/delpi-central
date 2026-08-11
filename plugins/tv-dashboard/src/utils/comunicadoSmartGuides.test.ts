import { describe, expect, it } from "vitest";

import {
  inferResizeEdges,
  peerFramesForSmartGuides,
  resizeEdgesFromHandle,
  snapFrameToPeerBlocks,
  snapGroupGestureToPeers,
} from "./comunicadoSmartGuides";
import { beginGroupGesture, resolveWorldFrames } from "./stageGroupGesture";

describe("comunicadoSmartGuides", () => {
  it("encaixa bordas esquerdas no move e emite guia vertical", () => {
    const peer = { x: 10, y: 20, w: 30, h: 15 };
    const frame = { x: 10.5, y: 40, w: 20, h: 10 };
    const { frame: snapped, guides } = snapFrameToPeerBlocks(frame, [peer], "move");
    expect(snapped.x).toBe(10);
    expect(snapped.y).toBe(40);
    expect(guides).toEqual([{ orientation: "v", position: 10 }]);
  });

  it("encaixa centros horizontais", () => {
    const peer = { x: 10, y: 10, w: 40, h: 20 }; // cx = 30
    const frame = { x: 20.4, y: 50, w: 20, h: 10 }; // cx = 30.4
    const { frame: snapped, guides } = snapFrameToPeerBlocks(frame, [peer], "move");
    expect(snapped.x).toBeCloseTo(20, 5);
    expect(guides.some((g) => g.orientation === "v" && g.position === 30)).toBe(true);
  });

  it("encaixa borda direita no resize mantendo a esquerda", () => {
    const peer = { x: 0, y: 0, w: 50, h: 10 }; // right = 50
    const frame = { x: 10, y: 20, w: 39.5, h: 12 };
    const { frame: snapped, guides } = snapFrameToPeerBlocks(frame, [peer], "resize", 0.9, {
      x: "end",
    });
    expect(snapped.x).toBe(10);
    expect(snapped.w).toBe(40);
    expect(guides).toContainEqual({ orientation: "v", position: 50 });
  });

  it("resize na direita não deixa a esquerda alinhada roubar o snap", () => {
    const peer = { x: 10, y: 0, w: 40, h: 10 }; // left=10 right=50
    const frame = { x: 10, y: 20, w: 39.4, h: 12 }; // left already aligned
    const stolen = snapFrameToPeerBlocks(frame, [peer], "resize");
    expect(stolen.guides.some((g) => g.orientation === "v" && g.position === 10)).toBe(true);

    const { frame: snapped, guides } = snapFrameToPeerBlocks(frame, [peer], "resize", 0.9, {
      x: "end",
    });
    expect(snapped.x).toBe(10);
    expect(snapped.w).toBe(40);
    expect(guides).toContainEqual({ orientation: "v", position: 50 });
  });

  it("resize embaixo não deixa o topo alinhado roubar o snap", () => {
    const peer = { x: 0, y: 10, w: 10, h: 40 }; // top=10 bottom=50
    const frame = { x: 20, y: 10, w: 12, h: 39.4 };
    const { frame: snapped, guides } = snapFrameToPeerBlocks(frame, [peer], "resize", 0.9, {
      y: "end",
    });
    expect(snapped.y).toBe(10);
    expect(snapped.h).toBe(40);
    expect(guides).toContainEqual({ orientation: "h", position: 50 });
  });

  it("resizeEdgesFromHandle e inferência vs baseline", () => {
    expect(resizeEdgesFromHandle("resize-e")).toEqual({ x: "end" });
    expect(resizeEdgesFromHandle("se")).toEqual({ x: "end", y: "end" });
    expect(resizeEdgesFromHandle("nw")).toEqual({ x: "start", y: "start" });
    expect(
      inferResizeEdges({ x: 10, y: 10, w: 20, h: 20 }, { x: 10, y: 10, w: 30, h: 20 }),
    ).toEqual({ x: "end" });
  });

  it("snap de grupo no move conserva w/h dos membros", () => {
    const members = [
      { id: "a", frame: { x: 10, y: 10, w: 20, h: 16 }, rotation: 0 },
      { id: "b", frame: { x: 32, y: 10, w: 8, h: 16 }, rotation: 0 },
    ];
    const gesture = beginGroupGesture({
      members,
      slideAspect: 1,
      interactionStartFrame: { x: 10, y: 10, w: 30, h: 16 },
    });
    expect(gesture).not.toBeNull();
    const peer = { x: 10.4, y: 40, w: 12, h: 10 };
    const { gesture: snapped } = snapGroupGestureToPeers(
      gesture!,
      { x: 10.4, y: 12, w: 30, h: 16 },
      [peer],
    );
    const world = resolveWorldFrames(snapped);
    expect(world.get("a")!.frame.w).toBeCloseTo(20, 5);
    expect(world.get("a")!.frame.h).toBeCloseTo(16, 5);
    expect(world.get("b")!.frame.w).toBeCloseTo(8, 5);
    const dxA = world.get("a")!.frame.x - 10;
    const dxB = world.get("b")!.frame.x - 32;
    expect(dxA).toBeCloseTo(dxB, 5);
  });

  it("snap de grupo no resize preserva razões locais", () => {
    const members = [
      { id: "a", frame: { x: 10, y: 10, w: 20, h: 20 }, rotation: 0 },
      { id: "b", frame: { x: 40, y: 10, w: 10, h: 10 }, rotation: 0 },
    ];
    const gesture = beginGroupGesture({
      members,
      slideAspect: 1,
      interactionStartFrame: { x: 10, y: 10, w: 40, h: 20 },
      resizeHandle: "e",
    });
    const peer = { x: 0, y: 0, w: 80, h: 8 };
    const { gesture: snapped } = snapGroupGestureToPeers(
      gesture!,
      { x: 10, y: 10, w: 69.5, h: 20 },
      [peer],
    );
    const world = resolveWorldFrames(snapped);
    expect(world.get("a")!.frame.w / world.get("b")!.frame.w).toBeCloseTo(2, 4);
    expect(world.get("a")!.frame.h).toBeCloseTo(20, 4);
  });

  it("não encaixa fora do limiar", () => {
    const peer = { x: 10, y: 10, w: 20, h: 20 };
    const frame = { x: 50, y: 50, w: 10, h: 10 };
    const { frame: snapped, guides } = snapFrameToPeerBlocks(frame, [peer], "move", 0.5);
    expect(snapped).toEqual(frame);
    expect(guides).toEqual([]);
  });

  it("peerFramesForSmartGuides exclui ids arrastados", () => {
    const blocks = [
      { id: "a", frame: { x: 0, y: 0, w: 10, h: 10 } },
      { id: "b", frame: { x: 20, y: 0, w: 10, h: 10 } },
    ];
    expect(peerFramesForSmartGuides(blocks, new Set(["a"]))).toEqual([blocks[1].frame]);
  });
});
