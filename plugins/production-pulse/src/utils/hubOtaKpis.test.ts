import { describe, expect, it } from "vitest";

import type { FirmwareListItem } from "../api/productionPulseApi";
import type { DeviceListItem } from "../types/device";
import {
  computeHubOtaKpis,
  countLinkedDevices,
  countOutdatedDevices,
  countPublishedFirmwares,
  latestPublishedVersionByFamily,
} from "./hubOtaKpis";

function firmware(
  partial: Partial<FirmwareListItem> &
    Pick<FirmwareListItem, "id" | "firmwareKey" | "version">,
): FirmwareListItem {
  return {
    driverKey: partial.firmwareKey,
    displayName: partial.firmwareKey,
    lifecycle: "published",
    hasSource: true,
    hasArtifact: true,
    artifactSha256: null,
    artifactSizeBytes: null,
    releaseNotes: null,
    minCompatibleVersion: null,
    publishedAt: "2026-01-01T00:00:00Z",
    createdAt: "2026-01-01T00:00:00Z",
    archivedAt: null,
    ...partial,
  };
}

function device(
  partial: Partial<DeviceListItem> & Pick<DeviceListItem, "id" | "name">,
): DeviceListItem {
  return {
    branch: "01",
    ipAddress: "10.0.0.1",
    controllerCode: null,
    firmwareSource: null,
    driverKey: "counter",
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

const CATALOG: FirmwareListItem[] = [
  firmware({ id: "c1", firmwareKey: "counter", version: "1.0.0" }),
  firmware({
    id: "c2",
    firmwareKey: "counter",
    version: "1.3.0",
    publishedAt: "2026-03-01T00:00:00Z",
  }),
  firmware({ id: "g1", firmwareKey: "gauge", version: "2.0.0" }),
  firmware({ id: "d1", firmwareKey: "draft_only", version: "0.1.0", lifecycle: "draft", publishedAt: null }),
  firmware({
    id: "a1",
    firmwareKey: "legacy",
    version: "9.0.0",
    archivedAt: "2026-04-01T00:00:00Z",
  }),
];

describe("hubOtaKpis", () => {
  it("conta só versões publicadas e não arquivadas", () => {
    expect(countPublishedFirmwares(CATALOG)).toBe(3);
  });

  it("resolve a última versão publicada por família", () => {
    const latest = latestPublishedVersionByFamily(CATALOG);
    expect(latest.get("counter")).toBe("1.3.0");
    expect(latest.get("gauge")).toBe("2.0.0");
    expect(latest.has("draft_only")).toBe(false);
    expect(latest.has("legacy")).toBe(false);
  });

  it("conta vinculados só pelo vínculo explícito", () => {
    const devices = [
      device({ id: "d1", name: "A", assignedFirmwareKey: "counter" }),
      // herança por driver não é vínculo
      device({ id: "d2", name: "B", assignedFirmwareKey: null, driverKey: "counter" }),
      device({ id: "d3", name: "C", assignedFirmwareKey: "   " }),
    ];
    expect(countLinkedDevices(devices)).toBe(1);
  });

  it("desatualizado exige versão publicada diferente da instalada", () => {
    const devices = [
      // caso original: instalada antiga
      device({
        id: "d1",
        name: "A",
        assignedFirmwareKey: "counter",
        installedFirmwareVersion: "1.0.0",
      }),
      // caso irmão: outra família também atrasada
      device({
        id: "d2",
        name: "B",
        assignedFirmwareKey: "gauge",
        installedFirmwareVersion: null,
      }),
      // negativo: já na última publicada
      device({
        id: "d3",
        name: "C",
        assignedFirmwareKey: "counter",
        installedFirmwareVersion: "1.3.0",
      }),
      // negativo: família sem versão publicada
      device({
        id: "d4",
        name: "D",
        assignedFirmwareKey: "draft_only",
        installedFirmwareVersion: "0.0.1",
      }),
      // negativo: sem vínculo explícito
      device({
        id: "d5",
        name: "E",
        assignedFirmwareKey: null,
        driverKey: "counter",
        installedFirmwareVersion: "1.0.0",
      }),
    ];
    expect(countOutdatedDevices(devices, CATALOG)).toBe(2);
  });

  it("agrega jobs em andamento e falhas do resumo da API", () => {
    const kpis = computeHubOtaKpis({
      firmwares: CATALOG,
      devices: [device({ id: "d1", name: "A", assignedFirmwareKey: "counter" })],
      updateSummary: {
        branch: "01",
        firmwareKey: null,
        total: 4,
        updated: 1,
        updating: 2,
        failed: 1,
      },
    });
    expect(kpis).toEqual({
      publishedFirmwares: 3,
      linkedDevices: 1,
      outdatedDevices: 1,
      updatingDevices: 2,
      failedDevices: 1,
    });
  });

  it("sem resumo da API, atualização e falhas ficam em zero", () => {
    const kpis = computeHubOtaKpis({ firmwares: [], devices: [], updateSummary: null });
    expect(kpis.updatingDevices).toBe(0);
    expect(kpis.failedDevices).toBe(0);
  });
});
