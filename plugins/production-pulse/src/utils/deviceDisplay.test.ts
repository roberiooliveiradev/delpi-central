import { describe, expect, it } from "vitest";

import type { DeviceListItem } from "../types/device";
import {
  formatCounterPeriodDelta,
  formatDeviceDetailDescription,
  formatPrimaryMetric,
  formatRelativeTime,
  placementLabel,
  resolveViewportBucket,
} from "./deviceDisplay";
import { applyClientFilters, groupDevices } from "./deviceGrouping";

const baseDevice = (overrides: Partial<DeviceListItem> = {}): DeviceListItem => ({
  id: "d1",
  branch: "01",
  name: "ESP A",
  ipAddress: "192.168.20.2",
  driverKey: "esp8266_counter_v1",
  roleKey: "pulse_counter",
  enabled: true,
  pollIntervalSeconds: 30,
  lastSeenAt: "2026-09-01T12:00:00.000Z",
  lastMetrics: { counter: 1284 },
  lastError: null,
  status: "online",
  online: true,
  graceSeconds: 60,
  binding: null,
  ...overrides,
});

describe("deviceDisplay", () => {
  it("formats primary metric with unit", () => {
    expect(formatPrimaryMetric(baseDevice())).toBe("1.284 gol");
  });

  it("formats counter period delta for counters only", () => {
    expect(
      formatCounterPeriodDelta(
        baseDevice({ periodDeltas: { day: { counter: 42 }, shift: { counter: 7 } } }),
        "day",
      ),
    ).toBe("+42");
    expect(formatCounterPeriodDelta(baseDevice({ roleKey: "process_gauge" }), "day")).toBeNull();
  });

  it("hides standalone placement object label to avoid duplicating device name", () => {
    const device = baseDevice({
      name: "ESP8266 - TESTE",
      binding: {
        id: "b1",
        deviceId: "d1",
        anchorType: "standalone",
        placementLabel: "ESP8266 - TESTE",
        placementKey: "s:d1",
        workCenterCode: null,
        workCenterName: null,
        machineCode: null,
        machineLabel: null,
        equipmentLabel: null,
        areaLabel: null,
        resourceCode: null,
        toolCode: null,
        notes: null,
      },
    });
    expect(placementLabel(device)).toBe("—");
    expect(formatDeviceDetailDescription(device)).toBe("192.168.20.2");
  });

  it("formats relative time", () => {
    const now = Date.parse("2026-09-01T12:00:12.000Z");
    expect(formatRelativeTime("2026-09-01T12:00:00.000Z", now)).toBe("12 s");
  });

  it("resolves viewport buckets", () => {
    expect(resolveViewportBucket(640)).toBe("mobile");
    expect(resolveViewportBucket(900)).toBe("tablet");
    expect(resolveViewportBucket(1280)).toBe("desktop");
  });
});

describe("deviceGrouping", () => {
  it("filters by status client-side", () => {
    const devices = [
      baseDevice({ id: "a", status: "online" }),
      baseDevice({ id: "b", status: "offline", online: false }),
    ];
    expect(applyClientFilters(devices, { status: "offline", anchorType: "" })).toHaveLength(1);
  });

  it("groups by work center placement", () => {
    const devices = [
      baseDevice({
        id: "a",
        binding: {
          id: "b1",
          deviceId: "a",
          anchorType: "work_center",
          placementLabel: "CT-53 · Usinagem",
          placementKey: "wc:01:ct-53",
          workCenterCode: "CT-53",
          workCenterName: "Usinagem",
          machineCode: null,
          machineLabel: null,
          equipmentLabel: null,
          areaLabel: null,
          resourceCode: null,
          toolCode: null,
          notes: null,
        },
      }),
      baseDevice({ id: "b", status: "no_binding" }),
    ];
    const groups = groupDevices(devices, "work_center");
    expect(groups).toHaveLength(2);
    expect(groups[0]?.title).toContain("CT-53");
    expect(groups[1]?.title).toBe("Sem amarração");
  });

  it("groups standalone devices by device name", () => {
    const devices = [
      baseDevice({
        id: "a",
        name: "Ventilador A",
        binding: {
          id: "b1",
          deviceId: "a",
          anchorType: "standalone",
          placementLabel: "",
          placementKey: "s:a",
          workCenterCode: null,
          workCenterName: null,
          machineCode: null,
          machineLabel: null,
          equipmentLabel: null,
          areaLabel: null,
          resourceCode: null,
          toolCode: null,
          notes: null,
        },
      }),
    ];
    const groups = groupDevices(devices, "work_center");
    expect(groups).toHaveLength(1);
    expect(groups[0]?.title).toBe("Ventilador A");
  });
});
