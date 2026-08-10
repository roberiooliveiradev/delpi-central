import { describe, expect, it } from "vitest";

import { buildPieSlicePath } from "./ChartSeriesPie";

describe("buildPieSlicePath", () => {
  const start = -Math.PI / 2;

  it("fatia parcial (pizza) emite um arco A", () => {
    const d = buildPieSlicePath(50, 50, 40, 0, start, start + Math.PI / 2);
    expect(d.match(/A /g)?.length ?? 0).toBe(1);
    expect(d).toContain(`M 50 50`);
  });

  it("círculo completo (1 categoria, pizza) usa dois semicírculos — path não degenera", () => {
    const d = buildPieSlicePath(50, 50, 40, 0, start, start + Math.PI * 2);
    expect(d.match(/A /g)?.length ?? 0).toBe(2);
    expect(d.startsWith("M 50 50")).toBe(true);
    expect(d.endsWith("Z")).toBe(true);
  });

  it("anel completo (1 categoria, rosca) usa quatro semicírculos", () => {
    const d = buildPieSlicePath(50, 50, 40, 22, start, start + Math.PI * 2);
    expect(d.match(/A /g)?.length ?? 0).toBe(4);
    expect(d.startsWith("M ")).toBe(true);
    expect(d.endsWith("Z")).toBe(true);
  });

  it("rosca parcial mantém um arco externo e um interno", () => {
    const d = buildPieSlicePath(50, 50, 40, 22, start, start + Math.PI);
    expect(d.match(/A /g)?.length ?? 0).toBe(2);
  });
});
