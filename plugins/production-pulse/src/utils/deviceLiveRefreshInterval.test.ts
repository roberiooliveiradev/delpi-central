import { describe, expect, it } from "vitest";

import { resolveDeviceLiveRefreshIntervalMs } from "./deviceLiveRefreshInterval";

describe("resolveDeviceLiveRefreshIntervalMs", () => {
  it("segue pollIntervalMs do device acima do piso de UI", () => {
    expect(resolveDeviceLiveRefreshIntervalMs(500)).toBe(500);
    expect(resolveDeviceLiveRefreshIntervalMs(30_000)).toBe(30_000);
  });

  it("aplica piso liveUiRefreshMs quando poll é menor", () => {
    expect(resolveDeviceLiveRefreshIntervalMs(1)).toBe(50);
  });

  it("usa default quando intervalo ausente", () => {
    expect(resolveDeviceLiveRefreshIntervalMs(undefined)).toBe(30_000);
    expect(resolveDeviceLiveRefreshIntervalMs(null)).toBe(30_000);
  });

  it("respeita máximo canônico", () => {
    expect(resolveDeviceLiveRefreshIntervalMs(999_999)).toBe(300_000);
  });
});
