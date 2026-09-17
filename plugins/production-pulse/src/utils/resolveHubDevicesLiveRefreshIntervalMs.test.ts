import { describe, expect, it } from "vitest";

import { resolveHubDevicesLiveRefreshIntervalMs } from "./resolveHubDevicesLiveRefreshIntervalMs";

describe("resolveHubDevicesLiveRefreshIntervalMs", () => {
  it("usa o menor pollInterval dos IoTs (positivo)", () => {
    expect(
      resolveHubDevicesLiveRefreshIntervalMs([
        { pollIntervalMs: 5_000 },
        { pollIntervalMs: 1_000 },
        { pollIntervalMs: 30_000 },
      ]),
    ).toBe(1_000);
  });

  it("irmão: um único device segue o próprio intervalo", () => {
    expect(resolveHubDevicesLiveRefreshIntervalMs([{ pollIntervalMs: 2_000 }])).toBe(2_000);
  });

  it("negativo: lista vazia usa default canônico", () => {
    expect(resolveHubDevicesLiveRefreshIntervalMs([])).toBe(30_000);
  });
});
