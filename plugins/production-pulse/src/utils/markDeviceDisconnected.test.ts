import { describe, expect, it } from "vitest";

import type { DeviceListItem } from "../types/device";
import { markDeviceDisconnected } from "./markDeviceDisconnected";

function base(overrides: Partial<DeviceListItem> = {}): DeviceListItem {
  return {
    id: "dev-1",
    branch: "01",
    name: "IoT",
    ipAddress: "10.0.0.1",
    controllerCode: null,
    firmwareSource: null,
    driverKey: "esp8266_counter_v1",
    roleKey: "counter",
    enabled: true,
    pollIntervalMs: 30_000,
    lastSeenAt: "2026-09-17T12:00:00Z",
    lastMetrics: {},
    lastError: null,
    status: "online",
    online: true,
    graceSeconds: 60,
    binding: null,
    ...overrides,
  };
}

describe("markDeviceDisconnected", () => {
  it("marca online como offline (positivo)", () => {
    const next = markDeviceDisconnected(base());
    expect(next.status).toBe("offline");
    expect(next.online).toBe(false);
    expect(next.id).toBe("dev-1");
  });

  it("irmão: já offline permanece offline", () => {
    const next = markDeviceDisconnected(base({ status: "offline", online: false }));
    expect(next.status).toBe("offline");
    expect(next.online).toBe(false);
  });

  it("negativo: disabled / no_binding não viram offline", () => {
    expect(markDeviceDisconnected(base({ status: "disabled", online: false })).status).toBe(
      "disabled",
    );
    expect(markDeviceDisconnected(base({ status: "no_binding", online: false })).status).toBe(
      "no_binding",
    );
  });
});
