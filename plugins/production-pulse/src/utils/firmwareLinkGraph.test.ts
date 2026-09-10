import { describe, expect, it } from "vitest";

import type { FirmwareListItem } from "../api/productionPulseApi";
import type { DeviceListItem } from "../types/device";
import {
  buildCompatibleDriverKeys,
  buildFirmwareLinkGraph,
  isFirmwareDeviceCompatible,
  replaceExplicitEdge,
  resolveConnectionCandidateState,
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
    expect(counter?.compatibleDriverKeys).toContain("esp8266_counter_v1");
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
    expect(deviceNode?.installedFirmwareVersion).toBe("1.2.0");
    expect(deviceNode?.availableVersion).toBeTruthy();
  });

  it("does not create edge when driver matches but no assignedFirmwareKey", () => {
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
    expect(edges).toHaveLength(0);
    expect(
      isFirmwareDeviceCompatible(
        "esp8266_counter_v1",
        families.find((f) => f.firmwareKey === "esp8266_counter_v1")!.compatibleDriverKeys,
      ),
    ).toBe(true);
  });

  it("treats historical archived driver as compatible for the family", () => {
    const catalog: FirmwareListItem[] = [
      ...familiesCatalog,
      firmware({
        id: "legacy",
        firmwareKey: "esp8266_counter_v1",
        version: "0.9.0",
        driverKey: "esp8266_counter_legacy",
        archivedAt: "2025-01-01T00:00:00Z",
      }),
    ];
    const keys = buildCompatibleDriverKeys(catalog, "esp8266_counter_v1");
    expect(keys).toContain("esp8266_counter_legacy");
    expect(isFirmwareDeviceCompatible("esp8266_counter_legacy", keys)).toBe(true);
    const families = uniqueFirmwareFamilies(catalog);
    expect(families.find((f) => f.firmwareKey === "esp8266_counter_v1")?.compatibleDriverKeys).toContain(
      "esp8266_counter_legacy",
    );
  });

  it("marks gauge driver incompatible with counter family", () => {
    const keys = buildCompatibleDriverKeys(familiesCatalog, "esp8266_counter_v1");
    expect(isFirmwareDeviceCompatible("esp8266_gauge_v1", keys)).toBe(false);
  });

  it("resolveConnectionCandidateState classifies firmware origin candidates", () => {
    const families = uniqueFirmwareFamilies(familiesCatalog);
    const familyByKey = new Map(families.map((f) => [f.firmwareKey, f]));
    const base = {
      linkMode: { origin: "firmware" as const, firmwareKey: "esp8266_counter_v1" },
      familyByKey,
    };
    expect(
      resolveConnectionCandidateState({
        ...base,
        nodeKind: "firmware",
        firmwareKey: "esp8266_counter_v1",
      }),
    ).toBe("origin");
    expect(
      resolveConnectionCandidateState({
        ...base,
        nodeKind: "device",
        deviceId: "d1",
        deviceDriverKey: "esp8266_counter_v1",
        assignedFirmwareKey: null,
      }),
    ).toBe("compatible");
    expect(
      resolveConnectionCandidateState({
        ...base,
        nodeKind: "device",
        deviceId: "d2",
        deviceDriverKey: "esp8266_gauge_v1",
        assignedFirmwareKey: null,
      }),
    ).toBe("incompatible");
    expect(
      resolveConnectionCandidateState({
        ...base,
        nodeKind: "device",
        deviceId: "d3",
        deviceDriverKey: "esp8266_counter_v1",
        assignedFirmwareKey: "esp8266_counter_v1",
      }),
    ).toBe("already-linked");
    expect(
      resolveConnectionCandidateState({
        ...base,
        nodeKind: "device",
        deviceId: "d4",
        deviceDriverKey: "esp8266_counter_v1",
        assignedFirmwareKey: "esp8266_gauge_v1",
      }),
    ).toBe("replace-link");
  });

  it("resolveConnectionCandidateState classifies device origin candidates", () => {
    const families = uniqueFirmwareFamilies(familiesCatalog);
    const familyByKey = new Map(families.map((f) => [f.firmwareKey, f]));
    const base = {
      linkMode: { origin: "device" as const, deviceId: "d1" },
      familyByKey,
      deviceDriverKey: "esp8266_counter_v1",
      assignedFirmwareKey: null as string | null,
    };
    expect(
      resolveConnectionCandidateState({
        ...base,
        nodeKind: "device",
        deviceId: "d1",
      }),
    ).toBe("origin");
    expect(
      resolveConnectionCandidateState({
        ...base,
        nodeKind: "firmware",
        firmwareKey: "esp8266_counter_v1",
      }),
    ).toBe("compatible");
    expect(
      resolveConnectionCandidateState({
        ...base,
        nodeKind: "firmware",
        firmwareKey: "esp8266_gauge_v1",
      }),
    ).toBe("incompatible");
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
