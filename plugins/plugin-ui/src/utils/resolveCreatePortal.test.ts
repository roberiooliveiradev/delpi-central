import { describe, expect, it, vi } from "vitest";

import { resolveCreatePortal } from "./resolveCreatePortal";

describe("resolveCreatePortal", () => {
  it("usa createPortal nomeado quando existe", () => {
    const createPortal = vi.fn();
    expect(resolveCreatePortal({ createPortal })).toBe(createPortal);
  });

  it("cai no default.createPortal (shape do shared MF)", () => {
    const createPortal = vi.fn();
    expect(resolveCreatePortal({ default: { createPortal } })).toBe(createPortal);
  });

  it("prefere named sobre default", () => {
    const named = vi.fn();
    const nested = vi.fn();
    expect(resolveCreatePortal({ createPortal: named, default: { createPortal: nested } })).toBe(
      named,
    );
  });

  it("falha com mensagem clara se React foi registrado no lugar de react-dom", () => {
    expect(() => resolveCreatePortal({ useRef: () => null, useMemo: () => null })).toThrow(
      /createPortal indisponível/,
    );
  });
});
