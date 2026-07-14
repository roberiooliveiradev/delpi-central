import { describe, expect, it, vi } from "vitest";

import {
  clearInputPartsFreeLayoutFrames,
  bindInputPartPointer,
  resolveInputBlockPaintCssVars,
  resolveInputContrastBackground,
  resolveInputPartFrame,
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
    expect(vars["--tdp-input-control-border" as keyof typeof vars]).toBe("#000000");
    expect(vars["--tdp-block-box-shadow" as keyof typeof vars]).toBeTruthy();
    expect(vars.color).toBe("#000000");
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
    } as unknown as Parameters<NonNullable<typeof bind.onPointerDown>>[0]);
    expect(stopPropagation).toHaveBeenCalled();
    expect(onPartPointerDown).toHaveBeenCalled();
    expect(onPartMovePointerDown).toHaveBeenCalled();
  });
});
