import { afterEach, describe, expect, it, vi } from "vitest";

import { resolveCreatePortal, tryResolveCreatePortal } from "./resolveCreatePortal";

afterEach(() => {
  delete (globalThis as Record<string, unknown>).__DELPI_MF_REACT_DOM__;
});

describe("resolveCreatePortal", () => {
  it("usa createPortal nomeado quando existe", () => {
    const createPortal = vi.fn();
    expect(resolveCreatePortal({ createPortal })).toBe(createPortal);
  });

  it("cai no default.createPortal (shape do shared MF)", () => {
    const createPortal = vi.fn();
    expect(resolveCreatePortal({ default: { createPortal } })).toBe(createPortal);
  });

  it("usa global __DELPI_MF_REACT_DOM__ semeado pelo host", () => {
    const createPortal = vi.fn();
    (globalThis as Record<string, unknown>).__DELPI_MF_REACT_DOM__ = { createPortal };
    expect(tryResolveCreatePortal({ useRef: () => null })).toBe(createPortal);
  });

  it("tryResolve retorna null em vez de lançar (não derruba a página)", () => {
    expect(tryResolveCreatePortal({ useRef: () => null })).toBeNull();
  });

  it("resolveCreatePortal falha com mensagem clara se React no lugar de react-dom", () => {
    expect(() => resolveCreatePortal({ useRef: () => null, useMemo: () => null })).toThrow(
      /createPortal indisponível/,
    );
  });
});
