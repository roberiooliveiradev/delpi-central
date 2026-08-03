import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

describe("playlist dataDefaults editor contract", () => {
  it("painel global persiste dataDefaults e reusa DataParamFields", () => {
    const fields = readFileSync(join(here, "PlaylistDataFiltersFields.tsx"), "utf8");
    expect(fields).toContain("collectPlaylistDataParamSchema");
    expect(fields).toContain("DataParamFields");
    expect(fields).toContain("hydrateDefaultPreset={false}");
    expect(fields).toContain("playlistFiltersEmpty");
  });

  it("filtros do slide usam só operationIds das fontes do slide", () => {
    const panel = readFileSync(join(here, "SlideDataFiltersPanel.tsx"), "utf8");
    expect(panel).toContain("collectFetchableOperationIds");
    expect(panel).toContain("mergeRouteParamSchemas");
    expect(panel).not.toContain("mergeParamSchemas(routes)");
  });

  it("cliente tipa dataDefaults no PATCH de playlist", () => {
    const api = readFileSync(join(here, "../api/tvDashboardApi.ts"), "utf8");
    expect(api).toContain("dataDefaults: Record<string, unknown>");
    expect(api).toMatch(/dataDefaults\?: Record<string, unknown>/);
  });
});
