import { describe, expect, it } from "vitest";

import type { FirmwareListItem } from "../api/productionPulseApi";
import {
  formatFirmwareVersionMenuLabel,
  resolveFirmwareVersionRowRoles,
} from "./firmwareVersionLabels";

function fw(
  partial: Partial<FirmwareListItem> & Pick<FirmwareListItem, "id" | "version">,
): FirmwareListItem {
  return {
    firmwareKey: "esp8266_counter_v1",
    driverKey: "esp8266_counter_v1",
    displayName: "ESP8266",
    lifecycle: "published",
    hasSource: true,
    hasArtifact: true,
    artifactSha256: "abc",
    artifactSizeBytes: 10,
    releaseNotes: null,
    minCompatibleVersion: null,
    publishedAt: "2026-01-02T00:00:00Z",
    createdAt: "2026-01-01T00:00:00Z",
    archivedAt: null,
    ...partial,
  };
}

describe("firmwareVersionLabels", () => {
  it("marks latest and installed without ambiguous «atual»", () => {
    const items = [
      fw({ id: "a", version: "0.1.3", publishedAt: "2026-01-01T00:00:00Z" }),
      fw({ id: "b", version: "1.0.0", publishedAt: "2026-02-01T00:00:00Z" }),
    ];
    const roles = resolveFirmwareVersionRowRoles({
      item: items[1],
      familyItems: items,
      installedVersion: "1.0.0",
      selectedId: "b",
    });
    expect(roles).toContain("latest");
    expect(roles).toContain("installed");
    expect(roles).toContain("selected");
    expect(formatFirmwareVersionMenuLabel(items[1], roles)).not.toMatch(/atual/i);
    expect(formatFirmwareVersionMenuLabel(items[1], roles)).toMatch(/Mais recente/);
    expect(formatFirmwareVersionMenuLabel(items[1], roles)).toMatch(/Instalada/);
  });
});
