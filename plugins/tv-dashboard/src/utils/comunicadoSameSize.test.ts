import { describe, expect, it } from "vitest";

import { createBlock, createShapeBlock } from "@delpi/tv-dashboard-presentation";

import {
  canApplySameSize,
  resizeComunicadoBlocksSameSize,
  resolveSameSizePrimaryId,
} from "./comunicadoSameSize";

describe("resizeComunicadoBlocksSameSize", () => {
  it("copia largura do primário (último id) sem mudar x/y", () => {
    const a = createBlock("text", "A");
    const b = createBlock("text", "B");
    a.frame = { x: 10, y: 20, w: 40, h: 12 };
    b.frame = { x: 50, y: 30, w: 10, h: 8 };
    const next = resizeComunicadoBlocksSameSize([a, b], [b.id, a.id], "width");
    const na = next.find((block) => block.id === a.id)!;
    const nb = next.find((block) => block.id === b.id)!;
    expect(na.frame).toEqual(a.frame);
    expect(nb.frame).toEqual({ x: 50, y: 30, w: 40, h: 8 });
  });

  it("copia altura do primário", () => {
    const a = createBlock("text", "A");
    const b = createBlock("text", "B");
    a.frame = { x: 0, y: 0, w: 10, h: 30 };
    b.frame = { x: 20, y: 5, w: 16, h: 8 };
    const next = resizeComunicadoBlocksSameSize([a, b], [b.id, a.id], "height");
    expect(next.find((block) => block.id === b.id)?.frame.h).toBe(30);
    expect(next.find((block) => block.id === b.id)?.frame.w).toBe(16);
    expect(next.find((block) => block.id === a.id)?.frame).toEqual(a.frame);
  });

  it("copia largura e altura no eixo both", () => {
    const a = createBlock("text", "A");
    const b = createBlock("text", "B");
    a.frame = { x: 0, y: 0, w: 22, h: 11 };
    b.frame = { x: 8, y: 9, w: 5, h: 5 };
    const next = resizeComunicadoBlocksSameSize([a, b], [b.id, a.id], "both");
    expect(next.find((block) => block.id === b.id)?.frame).toEqual({
      x: 8,
      y: 9,
      w: 22,
      h: 11,
    });
  });

  it("redimensiona membros do grupo, não a bbox", () => {
    const a = createBlock("text", "A");
    const b = createBlock("text", "B");
    a.groupId = "g1";
    b.groupId = "g1";
    a.frame = { x: 0, y: 0, w: 30, h: 20 };
    b.frame = { x: 10, y: 10, w: 8, h: 8 };
    const next = resizeComunicadoBlocksSameSize([a, b], [b.id, a.id], "both");
    expect(next.find((block) => block.id === b.id)?.frame).toEqual({
      x: 10,
      y: 10,
      w: 30,
      h: 20,
    });
  });

  it("ignora linhas como alvo e como referência", () => {
    const box = createBlock("text", "A");
    const line = createShapeBlock("line");
    box.frame = { x: 0, y: 0, w: 24, h: 12 };
    line.frame = { x: 40, y: 0, w: 50, h: 4 };
    expect(canApplySameSize([box, line], [box.id, line.id])).toBe(false);
    expect(resolveSameSizePrimaryId([box, line], [box.id, line.id])).toBe(box.id);
    const next = resizeComunicadoBlocksSameSize([box, line], [box.id, line.id], "both");
    expect(next.find((block) => block.id === line.id)?.frame).toEqual(line.frame);
    expect(next.find((block) => block.id === box.id)?.frame).toEqual(box.frame);
  });

  it("não habilita com um único bloco", () => {
    const a = createBlock("text", "A");
    expect(canApplySameSize([a], [a.id])).toBe(false);
  });
});
