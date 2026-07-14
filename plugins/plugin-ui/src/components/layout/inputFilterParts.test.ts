import { describe, expect, it, vi } from "vitest";

import {
  clearInputPartsFreeLayoutFrames,
  bindInputPartPointer,
  findInputContentPartNearPoint,
  resolveInputBlockPaintCssVars,
  resolveInputContrastBackground,
  resolveInputControlPaintCssVars,
  resolveInputPartFrame,
  clampInputPartFrame,
  resolveInputPartLayoutStyle,
  seedInputPartsFreeLayoutFrames,
} from "./inputFilterParts";

describe("inputFilterParts paint vs fundo do bloco", () => {
  it("contraste usa fill da moldura, depois do bloco, depois superfície do deck", () => {
    expect(
      resolveInputContrastBackground(
        { frame: { style: { fill: "#0f172a" } } },
        { backgroundColor: "#ffffff" },
      ),
    ).toBe("#0f172a");
    expect(
      resolveInputContrastBackground(undefined, { fill: "#fef3c7" }),
    ).toBe("#fef3c7");
    expect(resolveInputContrastBackground(undefined, undefined)).toMatch(/^#/);
  });

  it("CSS vars resolvem fg escuro em superfície clara (não herda tema host)", () => {
    const vars = resolveInputBlockPaintCssVars("#ffffff");
    expect(vars["--tdp-input-surface" as keyof typeof vars]).toBe("#ffffff");
    expect(vars["--tdp-input-fg" as keyof typeof vars]).toBe("#000000");
    expect(vars["--tdp-input-border" as keyof typeof vars]).toBe(
      vars["--tdp-input-muted" as keyof typeof vars],
    );
    expect(vars["--tdp-block-box-shadow" as keyof typeof vars]).toBeTruthy();
    expect(vars.color).toBe("#000000");
  });

  it("control.style vira CSS vars da caixa nativa (fill/stroke)", () => {
    const vars = resolveInputControlPaintCssVars({
      style: { fill: "#fef3c7", stroke: "#b45309", strokeWidth: 2, borderRadius: 8 },
    });
    expect(vars["--tdp-input-control-surface" as keyof typeof vars]).toBe("#fef3c7");
    expect(vars["--tdp-input-control-border" as keyof typeof vars]).toBe("#b45309");
    expect(vars["--tdp-input-control-border-width" as keyof typeof vars]).toBe("2px");
    expect(vars["--tdp-input-control-radius" as keyof typeof vars]).toBe("8px");
  });

  it("layout da parte control não pinta fill/stroke no host (só vars no nativo)", () => {
    const css = resolveInputPartLayoutStyle(
      { style: { fill: "#fef3c7", stroke: "#000", strokeWidth: 2 } },
      { partKind: "control" },
    );
    expect(css.background).toBeUndefined();
    expect(css.backgroundColor).toBeUndefined();
    expect(css.border).toBeUndefined();
  });

  it("paint de fundo no control não aplica alignSelf flex-start (não desloca na linha)", () => {
    const css = resolveInputPartLayoutStyle(
      { style: { fill: "#a78bfa" } },
      { partKind: "control" },
    );
    expect(css.alignSelf).toBeUndefined();
    expect(css.flex).toBeUndefined();
  });

  it("frame retarget: ponto perto do control resolve a parte de conteúdo", () => {
    const root = document.createElement("div");
    root.className = "tdp-comunicado__input-block";
    const control = document.createElement("span");
    control.setAttribute("data-input-part", "control");
    Object.defineProperty(control, "getBoundingClientRect", {
      value: () => ({ left: 100, top: 40, right: 220, bottom: 70, width: 120, height: 30 }),
    });
    root.appendChild(control);
    // Clique no outline (fora do box, dentro do pad).
    expect(findInputContentPartNearPoint(root, 100 - 4, 55)).toEqual({ kind: "control" });
    expect(findInputContentPartNearPoint(root, 10, 10)).toBeNull();
  });

  it("CSS vars resolvem fg claro em superfície escura", () => {
    const vars = resolveInputBlockPaintCssVars("#0f172a");
    expect(vars["--tdp-input-fg" as keyof typeof vars]).toBe("#ffffff");
    expect(vars.color).toBe("#ffffff");
  });

  it("layout de parte com cor auto segue contraste da caixa", () => {
    const light = resolveInputPartLayoutStyle(
      { style: { color: "auto" } },
      { partKind: "label", contrastBackground: "#ffffff" },
    );
    expect(light.color).toBe("#000000");
    const dark = resolveInputPartLayoutStyle(
      { style: { color: "auto" } },
      { partKind: "label", contrastBackground: "#003866" },
    );
    expect(dark.color).toBe("#ffffff");
  });
});

describe("inputFilterParts free-layout", () => {
  it("seed aplica frames em lote, não só numa parte", () => {
    const seeded = seedInputPartsFreeLayoutFrames({
      label: { visible: true },
      badge: { visible: true },
      control: { visible: true },
    });
    expect(resolveInputPartFrame(seeded.label)).not.toBeNull();
    expect(resolveInputPartFrame(seeded.badge)).not.toBeNull();
    expect(resolveInputPartFrame(seeded.control)).not.toBeNull();
  });

  it("clear remove frames e preserva visibilidade", () => {
    const seeded = seedInputPartsFreeLayoutFrames({
      label: { visible: true },
      control: { visible: true },
    });
    const cleared = clearInputPartsFreeLayoutFrames(seeded);
    expect(resolveInputPartFrame(cleared.label)).toBeNull();
    expect(resolveInputPartFrame(cleared.control)).toBeNull();
    expect(cleared.label?.visible).toBe(true);
  });

  it("bindInputPartPointer isola pointer do bloco (stopPropagation)", () => {
    const onPartPointerDown = vi.fn();
    const onPartMovePointerDown = vi.fn();
    const bind = bindInputPartPointer(
      { kind: "badge" },
      {
        selectedPart: { kind: "badge" },
        onPartPointerDown,
        onPartMovePointerDown,
      },
    );
    const stopPropagation = vi.fn();
    bind.onPointerDown?.({
      stopPropagation,
      target: document.createElement("span"),
    } as unknown as Parameters<NonNullable<typeof bind.onPointerDown>>[0]);
    expect(stopPropagation).toHaveBeenCalled();
    expect(onPartPointerDown).toHaveBeenCalled();
    expect(onPartMovePointerDown).toHaveBeenCalled();
  });

  it("bindInputPartPointer no control selecionado inicia drag da caixa (foco se sem arraste)", () => {
    const onPartPointerDown = vi.fn();
    const onPartMovePointerDown = vi.fn();
    const bind = bindInputPartPointer(
      { kind: "control" },
      {
        selectedPart: { kind: "control" },
        onPartPointerDown,
        onPartMovePointerDown,
      },
    );
    const stopPropagation = vi.fn();
    const preventDefault = vi.fn();
    const input = document.createElement("input");
    bind.onPointerDown?.({
      stopPropagation,
      preventDefault,
      target: input,
    } as unknown as Parameters<NonNullable<typeof bind.onPointerDown>>[0]);
    expect(stopPropagation).toHaveBeenCalled();
    expect(preventDefault).toHaveBeenCalled();
    expect(onPartPointerDown).toHaveBeenCalledWith({ kind: "control" }, expect.anything());
    expect(onPartMovePointerDown).toHaveBeenCalledWith({ kind: "control" }, expect.anything());
  });

  it("bindInputPartPointer na moldura redireciona clique perto do control", () => {
    const onPartPointerDown = vi.fn();
    const onPartMovePointerDown = vi.fn();
    const root = document.createElement("div");
    root.setAttribute("data-input-part", "frame");
    const control = document.createElement("span");
    control.setAttribute("data-input-part", "control");
    Object.defineProperty(control, "getBoundingClientRect", {
      value: () => ({ left: 50, top: 20, right: 150, bottom: 50, width: 100, height: 30 }),
    });
    root.appendChild(control);
    const bind = bindInputPartPointer(
      { kind: "frame" },
      {
        selectedPart: { kind: "control" },
        onPartPointerDown,
        onPartMovePointerDown,
      },
    );
    bind.onPointerDown?.({
      stopPropagation: vi.fn(),
      preventDefault: vi.fn(),
      target: root,
      currentTarget: root,
      clientX: 48,
      clientY: 35,
    } as unknown as Parameters<NonNullable<typeof bind.onPointerDown>>[0]);
    expect(onPartPointerDown).toHaveBeenCalledWith({ kind: "control" }, expect.anything());
    expect(onPartMovePointerDown).toHaveBeenCalledWith({ kind: "control" }, expect.anything());
  });

  it("bindInputPartPointer no control nativo sem seleção seleciona a parte", () => {
    const onPartPointerDown = vi.fn();
    const onPartMovePointerDown = vi.fn();
    const bind = bindInputPartPointer(
      { kind: "control" },
      {
        selectedPart: null,
        onPartPointerDown,
        onPartMovePointerDown,
      },
    );
    const stopPropagation = vi.fn();
    const preventDefault = vi.fn();
    const input = document.createElement("input");
    bind.onPointerDown?.({
      stopPropagation,
      preventDefault,
      target: input,
    } as unknown as Parameters<NonNullable<typeof bind.onPointerDown>>[0]);
    expect(stopPropagation).toHaveBeenCalled();
    expect(preventDefault).toHaveBeenCalled();
    expect(onPartPointerDown).toHaveBeenCalledWith({ kind: "control" }, expect.anything());
    expect(onPartMovePointerDown).not.toHaveBeenCalled();
  });
});

describe("inputFilterParts containment", () => {
  it("frame % no layout nunca ultrapassa a moldura (max 100% + min 0)", () => {
    const css = resolveInputPartLayoutStyle(
      { frame: { x: 10, y: 20, w: 80, h: 50 } },
      { partKind: "control" },
    );
    expect(css.position).toBe("absolute");
    expect(css.width).toBe("80%");
    expect(css.height).toBe("50%");
    expect(css.maxWidth).toBe("100%");
    expect(css.maxHeight).toBe("100%");
    expect(css.minWidth).toBe(0);
    expect(css.overflow).toBe("hidden");
  });

  it("clampInputPartFrame mantém x+w e y+h dentro de 0–100", () => {
    const clipped = clampInputPartFrame({ x: 90, y: 90, w: 50, h: 50 });
    expect(clipped.x + (clipped.w ?? 0)).toBeLessThanOrEqual(100);
    expect(clipped.y + (clipped.h ?? 0)).toBeLessThanOrEqual(100);
  });

});
