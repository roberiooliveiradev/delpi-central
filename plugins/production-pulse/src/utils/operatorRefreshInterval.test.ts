import { describe, expect, it } from "vitest";

import { resolveOperatorRefreshIntervalMs } from "./operatorRefreshInterval";

describe("resolveOperatorRefreshIntervalMs", () => {
  it("respeita poll de 1 ms sem forçar piso artificial", () => {
    expect(resolveOperatorRefreshIntervalMs(1)).toBe(1);
  });

  it("usa default 30_000 ms quando intervalo ausente", () => {
    expect(resolveOperatorRefreshIntervalMs(undefined)).toBe(30_000);
    expect(resolveOperatorRefreshIntervalMs(null)).toBe(30_000);
  });

  it("não desce abaixo do mínimo canônico nem passa do máximo", () => {
    expect(resolveOperatorRefreshIntervalMs(0)).toBe(1);
    expect(resolveOperatorRefreshIntervalMs(999_999)).toBe(300_000);
  });
});
