import { describe, expect, it } from "vitest";

import { resolveOperatorRefreshIntervalMs } from "./operatorRefreshInterval";

describe("resolveOperatorRefreshIntervalMs", () => {
  it("delega para o resolver canônico de live refresh", () => {
    expect(resolveOperatorRefreshIntervalMs(500)).toBe(500);
    expect(resolveOperatorRefreshIntervalMs(1)).toBe(50);
  });
});
