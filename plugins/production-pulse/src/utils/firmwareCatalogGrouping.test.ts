import { describe, expect, it } from "vitest";

import type { FirmwareListItem } from "../api/productionPulseApi";
import { groupFirmwareCatalogByFamily, firmwareSiblingsForFamily } from "./firmwareCatalogGrouping";

function fw(
  partial: Partial<FirmwareListItem> &
    Pick<FirmwareListItem, "id" | "firmwareKey" | "version">,
): FirmwareListItem {
  return {
    driverKey: partial.firmwareKey,
    displayName: partial.displayName ?? partial.firmwareKey,
    lifecycle: partial.lifecycle ?? "published",
    hasSource: true,
    hasArtifact: true,
    artifactSha256: null,
    artifactSizeBytes: 1024,
    releaseNotes: null,
    minCompatibleVersion: null,
    publishedAt: partial.publishedAt ?? "2026-01-01T00:00:00Z",
    createdAt: "2026-01-01T00:00:00Z",
    archivedAt: partial.archivedAt ?? null,
    ...partial,
  };
}

describe("groupFirmwareCatalogByFamily", () => {
  it("groups multiple versions under one family (newest first)", () => {
    const items = [
      fw({
        id: "a1",
        firmwareKey: "esp8266_counter_v1",
        version: "0.1.0",
        publishedAt: "2026-01-01T00:00:00Z",
      }),
      fw({
        id: "a2",
        firmwareKey: "esp8266_counter_v1",
        version: "1.0.0",
        publishedAt: "2026-03-01T00:00:00Z",
      }),
      fw({
        id: "b1",
        firmwareKey: "esp32c3_counter_v1",
        version: "0.2.0",
        publishedAt: "2026-02-01T00:00:00Z",
      }),
    ];

    const groups = groupFirmwareCatalogByFamily(items);
    expect(groups.map((g) => g.firmwareKey)).toEqual([
      "esp32c3_counter_v1",
      "esp8266_counter_v1",
    ]);
    expect(groups[1].versionCount).toBe(2);
    expect(groups[1].versions.map((v) => v.version)).toEqual(["1.0.0", "0.1.0"]);
    expect(groups[1].latestPublishedId).toBe("a2");
    expect(groups[1].defaultExpanded).toBe(false);
  });

  it("keeps archived-only families and null latestPublished", () => {
    const items = [
      fw({
        id: "old",
        firmwareKey: "legacy_fw",
        version: "0.0.1",
        lifecycle: "archived",
        archivedAt: "2026-04-01T00:00:00Z",
        publishedAt: "2025-01-01T00:00:00Z",
      }),
    ];

    const groups = groupFirmwareCatalogByFamily(items);
    expect(groups).toHaveLength(1);
    expect(groups[0].latestPublished).toBeNull();
    expect(groups[0].latestPublishedId).toBeNull();
    expect(groups[0].versions[0].id).toBe("old");
  });

  it("returns empty for empty catalog", () => {
    expect(groupFirmwareCatalogByFamily([])).toEqual([]);
  });

  it("filters by search query and marks defaultExpanded", () => {
    const items = [
      fw({
        id: "a1",
        firmwareKey: "esp8266_counter_v1",
        version: "0.1.3",
        displayName: "Teste de Gravação",
        publishedAt: "2026-01-02T00:00:00Z",
      }),
      fw({
        id: "a0",
        firmwareKey: "esp8266_counter_v1",
        version: "0.1.0",
        publishedAt: "2026-01-01T00:00:00Z",
      }),
      fw({
        id: "b1",
        firmwareKey: "esp32c3_counter_v1",
        version: "0.2.0",
        publishedAt: "2026-01-03T00:00:00Z",
      }),
    ];

    const byVersion = groupFirmwareCatalogByFamily(items, { query: "0.1.3" });
    expect(byVersion).toHaveLength(1);
    expect(byVersion[0].firmwareKey).toBe("esp8266_counter_v1");
    expect(byVersion[0].defaultExpanded).toBe(true);
    // Família inteira permanece visível (contexto), não só a versão que bateu a busca.
    expect(byVersion[0].versions.map((v) => v.version)).toEqual(["0.1.3", "0.1.0"]);

    const none = groupFirmwareCatalogByFamily(items, { query: "does-not-exist" });
    expect(none).toEqual([]);
  });

  it("prefers published header over draft without publishedAt", () => {
    const items = [
      fw({
        id: "draft",
        firmwareKey: "fam_a",
        version: "2.0.0",
        lifecycle: "draft",
        publishedAt: null,
        createdAt: "2026-06-01T00:00:00Z",
      }),
      fw({
        id: "pub",
        firmwareKey: "fam_a",
        version: "1.0.0",
        lifecycle: "published",
        publishedAt: "2026-05-01T00:00:00Z",
      }),
    ];

    const [group] = groupFirmwareCatalogByFamily(items);
    expect(group.latest.id).toBe("pub");
    expect(group.latestPublishedId).toBe("pub");
    expect(group.versions.map((v) => v.id)).toEqual(["pub", "draft"]);
  });
});

describe("firmwareSiblingsForFamily", () => {
  it("returns newest-first siblings for one family only", () => {
    const items = [
      fw({
        id: "a1",
        firmwareKey: "fam_a",
        version: "0.1.0",
        publishedAt: "2026-01-01T00:00:00Z",
      }),
      fw({
        id: "a2",
        firmwareKey: "fam_a",
        version: "1.0.0",
        publishedAt: "2026-02-01T00:00:00Z",
      }),
      fw({
        id: "b1",
        firmwareKey: "fam_b",
        version: "9.0.0",
        publishedAt: "2026-03-01T00:00:00Z",
      }),
    ];
    const siblings = firmwareSiblingsForFamily(items, "fam_a");
    expect(siblings.map((s) => s.id)).toEqual(["a2", "a1"]);
  });

  it("returns empty when family has no versions", () => {
    expect(firmwareSiblingsForFamily([], "missing")).toEqual([]);
  });
});
