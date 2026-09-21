import { describe, expect, it } from "vitest";

import { buildPortalHomeEvents, buildPortalHomeHighlights } from "./portalHomeSignals";

describe("portalHomeSignals", () => {
  it("omite highlights sem resumo e sem loading", () => {
    expect(buildPortalHomeHighlights({ loading: false, resumo: null })).toEqual([]);
  });

  it("usa economia, horas e soluções já existentes no resumo", () => {
    const tiles = buildPortalHomeHighlights({
      loading: false,
      resumo: {
        solucoes_implementadas: 4,
        economia_liquida_total: 1200,
        economia_bruta_total: 2000,
        horas_economizadas_total: 8.5,
        roi_medio: 1.2,
      },
      contextLabel: "Consolidado (todas as unidades) · 01/09/2026 — 21/09/2026",
    });
    expect(tiles.map((item) => item.id)).toEqual(["net-economy", "hours", "solutions"]);
    expect(tiles.every((item) => item.loading !== true)).toBe(true);
    expect(tiles.every((item) => item.description?.includes("todas as unidades"))).toBe(true);
  });

  it("mostra só eventos comprovados", () => {
    expect(buildPortalHomeEvents({ vencimentos: null, alertas: [] })).toEqual([]);
    expect(
      buildPortalHomeEvents({
        vencimentos: {
          janela_dias: 90,
          total_vencendo: 2,
          vencendo: [],
        },
        alertas: [{ processo_id: "p1" } as never],
      }).map((item) => item.id),
    ).toEqual(["revisions-due", "negative-net"]);
  });
});
