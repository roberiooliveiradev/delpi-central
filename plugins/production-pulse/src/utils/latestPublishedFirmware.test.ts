import { describe, expect, it } from "vitest";

import type { FirmwareListItem } from "../api/productionPulseApi";
import { latestPublishedFirmwareForFamily } from "./latestPublishedFirmware";

function fw(partial: Partial<FirmwareListItem> & Pick<FirmwareListItem, "id" | "version">): FirmwareListItem {
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

describe("latestPublishedFirmwareForFamily", () => {
  it("returns newest published by release order", () => {
    const items = [
      fw({ id: "old", version: "0.1.3", publishedAt: "2026-01-01T00:00:00Z" }),
      fw({ id: "new", version: "1.0.0", publishedAt: "2026-02-01T00:00:00Z" }),
      fw({
        id: "draft",
        version: "1.1.0",
        lifecycle: "draft",
        publishedAt: null,
        hasArtifact: false,
      }),
    ];
    expect(latestPublishedFirmwareForFamily(items, "esp8266_counter_v1")?.id).toBe("new");
  });

  it("ignores other families and archived", () => {
    const items = [
      fw({
        id: "arch",
        version: "2.0.0",
        publishedAt: "2026-03-01T00:00:00Z",
        archivedAt: "2026-03-02T00:00:00Z",
        lifecycle: "archived",
      }),
      fw({ id: "ok", version: "1.0.0", publishedAt: "2026-02-01T00:00:00Z" }),
      fw({
        id: "other",
        version: "9.0.0",
        firmwareKey: "other_family",
        publishedAt: "2026-04-01T00:00:00Z",
      }),
    ];
    expect(latestPublishedFirmwareForFamily(items, "esp8266_counter_v1")?.id).toBe("ok");
  });

  it("returns null when no published row", () => {
    expect(latestPublishedFirmwareForFamily([], "esp8266_counter_v1")).toBeNull();
  });
});
