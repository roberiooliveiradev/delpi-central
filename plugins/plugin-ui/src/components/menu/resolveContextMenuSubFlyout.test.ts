import { describe, expect, it } from "vitest";

import { resolveContextMenuSubFlyout } from "./resolveContextMenuSubFlyout";

describe("resolveContextMenuSubFlyout", () => {
  const trigger = {
    left: 100,
    top: 200,
    right: 280,
    bottom: 236,
    width: 180,
    height: 36,
  };

  it("abre à direita quando há espaço", () => {
    const next = resolveContextMenuSubFlyout({
      trigger,
      panelWidth: 220,
      panelHeight: 160,
      viewportWidth: 1200,
      viewportHeight: 800,
    });
    expect(next.side).toBe("right");
    expect(next.left).toBe(trigger.right + 2);
    expect(next.top).toBe(trigger.top);
    expect(next.overflowY).toBe("visible");
    expect(next.maxHeight).toBeUndefined();
  });

  it("flip à esquerda quando não cabe à direita", () => {
    const next = resolveContextMenuSubFlyout({
      trigger: { ...trigger, left: 900, right: 1080 },
      panelWidth: 220,
      panelHeight: 160,
      viewportWidth: 1100,
      viewportHeight: 800,
    });
    expect(next.side).toBe("left");
    expect(next.left).toBeLessThan(900);
    expect(next.overflowY).toBe("visible");
  });

  it("clampa no fundo do viewport quando o flyout ultrapassaria a tela", () => {
    const next = resolveContextMenuSubFlyout({
      trigger: { ...trigger, top: 700, bottom: 736 },
      panelWidth: 220,
      panelHeight: 280,
      viewportWidth: 1200,
      viewportHeight: 800,
      margin: 8,
    });
    expect(next.top + 280).toBeLessThanOrEqual(800 - 8);
    expect(next.top).toBeGreaterThanOrEqual(8);
    expect(next.top).toBeLessThan(700);
    expect(next.overflowY).toBe("visible");
    expect(next.maxHeight).toBeUndefined();
  });

  it("sobe o painel alto perto do fundo para usar o espaço acima (sem scroll se couber)", () => {
    const next = resolveContextMenuSubFlyout({
      trigger: { ...trigger, top: 520, bottom: 556 },
      panelWidth: 220,
      panelHeight: 480,
      viewportWidth: 1200,
      viewportHeight: 800,
      margin: 8,
    });
    expect(next.top).toBeLessThan(520);
    expect(next.top + 480).toBeLessThanOrEqual(800 - 8);
    expect(next.overflowY).toBe("visible");
    expect(next.maxHeight).toBeUndefined();
  });

  it("ativa scroll só quando a altura natural não cabe no viewport", () => {
    const next = resolveContextMenuSubFlyout({
      trigger: { ...trigger, top: 400, bottom: 436 },
      panelWidth: 220,
      panelHeight: 900,
      viewportWidth: 1200,
      viewportHeight: 800,
      margin: 8,
    });
    expect(next.overflowY).toBe("auto");
    expect(next.maxHeight).toBeDefined();
    expect(next.maxHeight!).toBeLessThan(900);
    expect(next.top + (next.maxHeight ?? 0)).toBeLessThanOrEqual(800 - 8 + 1);
  });

  it("não ativa scroll por diferença de 1px (epsilon de layout)", () => {
    const next = resolveContextMenuSubFlyout({
      trigger: { ...trigger, top: 100, bottom: 136 },
      panelWidth: 220,
      panelHeight: 691,
      viewportWidth: 1200,
      viewportHeight: 800,
      margin: 8,
    });
    /* available a partir de top=100: 800-100-8 = 692 → 691 cabe com epsilon */
    expect(next.overflowY).toBe("visible");
    expect(next.maxHeight).toBeUndefined();
  });
});
