import { describe, expect, it } from "vitest";

import { resolveOperatorRefreshIntervalMs } from "./operatorRefreshInterval";

describe("resolveOperatorRefreshIntervalMs", () => {
  it("respeita poll de 500 ms sem forçar piso de 5 s", () => {
    expect(resolveOperatorRefreshIntervalMs(500)).toBe(500);
  });

  it("usa default 30_000 ms quando intervalo ausente", () => {
    expect(resolveOperatorRefreshIntervalMs(undefined)).toBe(30_000);
    expect(resolveOperatorRefreshIntervalMs(null)).toBe(30_000);
  });

  it("não desce abaixo do mínimo canônico nem passa do máximo", () => {
    expect(resolveOperatorRefreshIntervalMs(100)).toBe(500);
    expect(resolveOperatorRefreshIntervalMs(999_999)).toBe(300_000);
  });
});
