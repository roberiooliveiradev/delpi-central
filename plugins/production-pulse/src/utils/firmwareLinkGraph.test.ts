import { describe, expect, it } from "vitest";

import type { FirmwareListItem } from "../api/productionPulseApi";
import type { DeviceListItem } from "../types/device";
import {
  buildFirmwareLinkGraph,
  replaceExplicitEdge,
  uniqueFirmwareFamilies,
} from "./firmwareLinkGraph";

function device(partial: Partial<DeviceListItem> & Pick<DeviceListItem, "id" | "name">): DeviceListItem {
  return {
    branch: "01",
    ipAddress: "10.0.0.1",
    controllerCode: null,
    firmwareSource: null,
    driverKey: "esp8266_counter_v1",
    roleKey: "counter",
    enabled: true,
    pollIntervalMs: 5000,
    lastSeenAt: null,
    lastMetrics: {},
    lastError: null,
    status: "offline",
    online: false,
    graceSeconds: 10,
    binding: null,
    ...partial,
  };
}

function firmware(
  partial: Partial<FirmwareListItem> &
    Pick<FirmwareListItem, "id" | "firmwareKey" | "version">,
): FirmwareListItem {
  return {
    driverKey: partial.firmwareKey,
    displayName: "Counter",
    lifecycle: "published",
    hasSource: true,
    hasArtifact: true,
    artifactSha256: "a".repeat(64),
    artifactSizeBytes: 10,
    releaseNotes: null,
    minCompatibleVersion: null,
    publishedAt: "2026-01-01T00:00:00Z",
    createdAt: "2026-01-01T00:00:00Z",
    archivedAt: null,
    ...partial,
  };
}

const familiesCatalog: FirmwareListItem[] = [
  firmware({ id: "1", firmwareKey: "esp8266_counter_v1", version: "1.0.0" }),
  firmware({
    id: "1b",
    firmwareKey: "esp8266_counter_v1",
    version: "1.3.0",
    publishedAt: "2026-03-01T00:00:00Z",
  }),
  firmware({
    id: "2",
    firmwareKey: "esp8266_gauge_v1",
    version: "1.0.0",
    displayName: "Gauge",
  }),
];

describe("firmwareLinkGraph", () => {
  it("picks latestVersion and linkedCount per family", () => {
    const families = uniqueFirmwareFamilies(familiesCatalog, [
      device({
        id: "d1",
        name: "A",
        assignedFirmwareKey: "esp8266_counter_v1",
      }),
    ]);
    const counter = families.find((f) => f.firmwareKey === "esp8266_counter_v1");
    expect(counter?.latestVersion).toBe("1.3.0");
    expect(counter?.linkedCount).toBe(1);
  });

  it("builds explicit solid edge for assignedFirmwareKey", () => {
    const families = uniqueFirmwareFamilies(familiesCatalog);
    const { edges, nodes } = buildFirmwareLinkGraph({
      families,
      devices: [
        device({
          id: "d1",
          name: "A",
          assignedFirmwareKey: "esp8266_counter_v1",
          firmwareKey: "esp8266_counter_v1",
          installedFirmwareVersion: "1.2.0",
          ipAddress: "10.1.1.1",
        }),
      ],
    });
    expect(edges).toEqual([
      {
        id: "e-explicit-d1",
        source: "fw:esp8266_counter_v1",
        target: "dev:d1",
        kind: "explicit",
      },
    ]);
    const deviceNode = nodes.find((n) => n.id === "dev:d1");
    expect(deviceNode?.subtitle).toContain("10.1.1.1");
    expect(deviceNode?.subtitle).toContain("1.2.0");
    expect(deviceNode?.installedFirmwareVersion).toBe("1.2.0");
  });

  it("builds inherited dashed edge when only driver matches", () => {
    const families = uniqueFirmwareFamilies(familiesCatalog);
    const { edges } = buildFirmwareLinkGraph({
      families,
      devices: [
        device({
          id: "d2",
          name: "B",
          assignedFirmwareKey: null,
          firmwareKey: "esp8266_counter_v1",
          driverKey: "esp8266_counter_v1",
        }),
      ],
    });
    expect(edges[0]?.kind).toBe("inherited");
  });

  it("replaceExplicitEdge keeps one solid edge per device", () => {
    const edges = [
      {
        id: "e-explicit-d1",
        source: "fw:esp8266_counter_v1",
        target: "dev:d1",
        kind: "explicit" as const,
      },
    ];
    const next = replaceExplicitEdge(edges, {
      deviceNodeId: "dev:d1",
      firmwareNodeId: "fw:esp8266_gauge_v1",
    });
    expect(next.filter((e) => e.target === "dev:d1" && e.kind === "explicit")).toHaveLength(1);
    expect(next[0]?.source).toBe("fw:esp8266_gauge_v1");
  });
});
