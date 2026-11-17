import { describe, expect, it } from "vitest";

import { BALANCING_METHODS } from "./methodCatalog";

describe("BALANCING_METHODS (catálogo V3)", () => {
  it("preserva os seis métodos M1–M6 em ordem", () => {
    expect(BALANCING_METHODS.map((m) => m.id)).toEqual([
      "m1",
      "m2",
      "m3",
      "m4",
      "m5",
      "m6",
    ]);
  });

  it("M1 disponível e M5 Yamazumi implementado nesta release", () => {
    expect(BALANCING_METHODS.find((m) => m.id === "m1")?.status).toBe(
      "available",
    );
    expect(BALANCING_METHODS.find((m) => m.id === "m5")?.status).toBe(
      "implemented",
    );
  });

  it("métodos sem suporte declaram requisitos — nunca cálculo inerte", () => {
    const unsupported = BALANCING_METHODS.filter(
      (m) => m.status === "planned" || m.status === "limited",
    );
    expect(unsupported.length).toBeGreaterThanOrEqual(3);
    for (const m of unsupported) {
      expect(m.requirements?.length ?? m.summary.length).toBeTruthy();
    }
  });
});
