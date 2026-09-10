import { describe, expect, it } from "vitest";

import type { FirmwareListItem } from "../api/productionPulseApi";
import {
  formatFirmwareArtifactBytes,
  firmwareLifecycleLabel,
  summarizeFirmwareCatalogItem,
} from "./firmwareCatalogDisplay";

function baseFirmware(overrides: Partial<FirmwareListItem> = {}): FirmwareListItem {
  return {
    id: "fw-1",
    firmwareKey: "esp8266_counter_v1",
    driverKey: "esp8266_counter_v1",
    version: "0.1.3",
    displayName: "Teste de Gravação",
    lifecycle: "published",
    hasSource: true,
    hasArtifact: true,
    artifactSha256: "abc",
    artifactSizeBytes: 2048,
    releaseNotes: null,
    minCompatibleVersion: null,
    publishedAt: "2026-01-01T00:00:00Z",
    createdAt: "2026-01-01T00:00:00Z",
    archivedAt: null,
    ...overrides,
  };
}

describe("firmwareLifecycleLabel", () => {
  it("maps lifecycle states", () => {
    expect(firmwareLifecycleLabel("draft")).toBe("Rascunho");
    expect(firmwareLifecycleLabel("archived")).toBe("Arquivado");
    expect(firmwareLifecycleLabel("published")).toBe("Publicado");
  });
});

describe("formatFirmwareArtifactBytes", () => {
  it("formats common sizes", () => {
    expect(formatFirmwareArtifactBytes(512)).toBe("512 B");
    expect(formatFirmwareArtifactBytes(2048)).toBe("2.0 KiB");
    expect(formatFirmwareArtifactBytes(null)).toBeNull();
  });
});

describe("summarizeFirmwareCatalogItem", () => {
  it("prefers display name and includes family/version/driver", () => {
    const summary = summarizeFirmwareCatalogItem(baseFirmware());
    expect(summary.title).toBe("Teste de Gravação");
    expect(summary.familyKey).toBe("esp8266_counter_v1");
    expect(summary.version).toBe("0.1.3");
    expect(summary.driverKey).toBe("esp8266_counter_v1");
    expect(summary.hasArtifact).toBe(true);
    expect(summary.artifactSizeLabel).toBe("2.0 KiB");
  });

  it("falls back to firmwareKey when display name empty", () => {
    const summary = summarizeFirmwareCatalogItem(baseFirmware({ displayName: "  " }));
    expect(summary.title).toBe("esp8266_counter_v1");
  });
});
