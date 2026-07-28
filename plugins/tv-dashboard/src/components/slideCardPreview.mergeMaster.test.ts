import { describe, expect, it } from "vitest";

import type { PlaylistMasterConfig } from "../api/tvDashboardApi";
import { mergeMasterConfigs } from "../components/slideCardPreview";

describe("mergeMasterConfigs", () => {
  it("retorna undefined quando nenhum master está enabled", () => {
    expect(
      mergeMasterConfigs(
        { enabled: false, background: { type: "color", value: "#111" } },
        { enabled: false },
      ),
    ).toBeUndefined();
  });

  it("usa só o master da playlist quando a seção não está enabled", () => {
    const playlist: PlaylistMasterConfig = {
      enabled: true,
      background: { type: "color", value: "#0f172a" },
    };
    expect(mergeMasterConfigs(playlist, { enabled: false })).toEqual(playlist);
  });

  it("seção enabled sobrescreve fundo da playlist", () => {
    const merged = mergeMasterConfigs(
      {
        enabled: true,
        background: { type: "color", value: "#0f172a" },
        logo: { assetId: "logo-pl", position: "top-right" },
      },
      {
        enabled: true,
        background: { type: "color", value: "#112233" },
      },
    );
    expect(merged?.enabled).toBe(true);
    expect(merged?.background).toEqual({ type: "color", value: "#112233" });
    expect(merged?.logo).toEqual({ assetId: "logo-pl", position: "top-right" });
  });
});
