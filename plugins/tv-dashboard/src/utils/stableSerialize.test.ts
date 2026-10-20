import { describe, expect, it } from "vitest";

import { stableEquals, stableSerialize } from "./stableSerialize";

describe("stableSerialize / stableEquals", () => {
  it("objetos com mesma chave em ordem diferente são iguais", () => {
    expect(stableEquals({ a: 1, b: 2 }, { b: 2, a: 1 })).toBe(true);
    expect(stableSerialize({ b: 2, a: 1 })).toBe(stableSerialize({ a: 1, b: 2 }));
  });

  it("normalização profunda em objetos aninhados", () => {
    const a = { style: { color: "#fff", paint: { kind: "solid" } }, x: 1 };
    const b = { x: 1, style: { paint: { kind: "solid" }, color: "#fff" } };
    expect(stableEquals(a, b)).toBe(true);
  });

  it("ordem de array é relevante — conteúdo diferente detectado", () => {
    expect(stableEquals([1, 2], [2, 1])).toBe(false);
    expect(stableEquals({ a: 1 }, { a: 2 })).toBe(false);
  });

  it("chave ausente (undefined) não cria diff — null explícito é conteúdo", () => {
    expect(stableEquals({ a: undefined }, {})).toBe(true);
    // null serializa e é semântico — campo presente ≠ campo ausente.
    expect(stableEquals({ a: null }, {})).toBe(false);
  });
});
