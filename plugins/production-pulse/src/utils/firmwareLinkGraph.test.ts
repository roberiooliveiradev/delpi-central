import { describe, expect, it } from "vitest";

import type { FirmwareCatalogItem } from "../api/productionPulseApi";
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

const familiesCatalog: FirmwareCatalogItem[] = [
  {
    id: "1",
    firmwareKey: "esp8266_counter_v1",
    driverKey: "esp8266_counter_v1",
    version: "1.0.0",
    displayName: "Counter",
    artifactSha256: "a".repeat(64),
    artifactSizeBytes: 10,
    publishedAt: "2026-01-01T00:00:00Z",
    releaseNotes: null,
    minCompatibleVersion: null,
  },
  {
    id: "2",
    firmwareKey: "esp8266_gauge_v1",
    driverKey: "esp8266_gauge_v1",
    version: "1.0.0",
    displayName: "Gauge",
    artifactSha256: "b".repeat(64),
    artifactSizeBytes: 10,
    publishedAt: "2026-01-01T00:00:00Z",
    releaseNotes: null,
    minCompatibleVersion: null,
  },
];

describe("firmwareLinkGraph", () => {
  it("builds explicit solid edge for assignedFirmwareKey", () => {
    const families = uniqueFirmwareFamilies(familiesCatalog);
    const { edges } = buildFirmwareLinkGraph({
      families,
      devices: [
        device({
          id: "d1",
          name: "A",
          assignedFirmwareKey: "esp8266_counter_v1",
          firmwareKey: "esp8266_counter_v1",
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
