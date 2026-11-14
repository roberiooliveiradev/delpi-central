import { describe, expect, it } from "vitest";

import {
  buildHeroHighlights,
  buildOverviewRows,
  buildPendingQueueIndicator,
  buildSectionView,
  partialBannerMessage,
  sourceLabel,
} from "./homeViewModel";
import type {
  HomeItem,
  HomeResponse,
  HomeSection,
  HomeSections,
} from "../../types/home";

const ITEM: HomeItem = {
  id: "req-1",
  kind: "request",
  title: "Solicitação 000456",
  status: "submitted",
  status_label: "Em análise",
  date: "2026-10-25",
  href: "/apps/my-requests",
  source: "requests-api",
};

const TASK: HomeItem = {
  id: "task-1",
  kind: "task",
  title: "Revisar LMP 2026/041",
  status: "in_progress",
  status_label: "Em andamento",
  href: "/apps/dashboard-lmps",
  source: "api-delpi",
};

function sectionsWith(
  overrides: Partial<HomeSections>,
): HomeSections {
  const empty: HomeSection = { status: "empty", items: [] };
  return {
    attention: { ...empty },
    tasks: { ...empty },
    lmps: { ...empty },
    requests: { ...empty },
    activity: { ...empty },
    collaboration: { ...empty },
    ...overrides,
  };
}

describe("buildSectionView", () => {
  it("available → itens com total honesto", () => {
    const view = buildSectionView({
      status: "available",
      items: [ITEM],
      total: 7,
    });
    expect(view.kind).toBe("items");
    expect(view.items).toHaveLength(1);
    expect(view.totalLabel).toBe("1 de 7");
  });

  it("empty → estado legítimo de vazio", () => {
    const view = buildSectionView({ status: "empty", items: [] });
    expect(view.kind).toBe("empty");
    expect(view.message).toContain("Nenhum item");
  });

  it("forbidden → acesso negado, nunca erro de conexão", () => {
    const view = buildSectionView({ status: "forbidden", items: [] });
    expect(view.kind).toBe("forbidden");
    expect(view.message).toContain("não tem acesso");
  });

  it("unavailable → indisponibilidade honesta com razão", () => {
    const view = buildSectionView({
      status: "unavailable",
      reason: "timeout",
      items: [],
    });
    expect(view.kind).toBe("unavailable");
    expect(view.message).toContain("não respondeu a tempo");
    expect(view.message).not.toContain("Nenhum item");
  });

  it("not_implemented → capacidade futura identificada", () => {
    const view = buildSectionView({ status: "not_implemented", items: [] });
    expect(view.kind).toBe("not_implemented");
    expect(view.message).toContain("próxima etapa");
  });
});

describe("partialBannerMessage", () => {
  it("partial → banner honesto; demais → nulo", () => {
    expect(partialBannerMessage("partial")).toContain("Algumas fontes");
    expect(partialBannerMessage("available")).toBeNull();
    expect(partialBannerMessage("unavailable")).toBeNull();
  });
});

describe("sourceLabel", () => {
  it("traduz sistemas oficiais e preserva desconhecidos", () => {
    expect(sourceLabel("api-delpi")).toBe("API DELPI");
    expect(sourceLabel("requests-api")).toBe("Solicitações");
    expect(sourceLabel("outro")).toBe("outro");
    expect(sourceLabel(undefined)).toBe("—");
  });
});

describe("buildPendingQueueIndicator", () => {
  it("tasks available com total → ready com contagem oficial", () => {
    const indicator = buildPendingQueueIndicator(
      sectionsWith({
        tasks: { status: "available", items: [TASK], total: 5 },
      }),
    );
    expect(indicator).toEqual({ kind: "ready", total: 5 });
  });

  it("total zero → empty legítimo (não esconde a seção)", () => {
    const indicator = buildPendingQueueIndicator(
      sectionsWith({ tasks: { status: "available", items: [], total: 0 } }),
    );
    expect(indicator).toEqual({ kind: "empty" });
  });

  it("unavailable → estado honesto, nunca zero", () => {
    const indicator = buildPendingQueueIndicator(
      sectionsWith({ tasks: { status: "unavailable", items: [] } }),
    );
    expect(indicator.kind).toBe("unavailable");
  });

  it("forbidden/not_implemented → hidden (sem card sem permissão)", () => {
    for (const status of ["forbidden", "not_implemented"] as const) {
      const indicator = buildPendingQueueIndicator(
        sectionsWith({ tasks: { status, items: [] } }),
      );
      expect(indicator.kind).toBe("hidden");
    }
  });
});

describe("buildHeroHighlights", () => {
  it("tasks sai do hero — o indicador de pendências é a fonte única", () => {
    const sections = sectionsWith({
      tasks: { status: "available", items: [TASK], total: 4 },
      requests: { status: "available", items: [ITEM], total: 2 },
      lmps: { status: "available", items: [TASK], total: 9 },
    });
    const highlights = buildHeroHighlights(sections, false);
    expect(highlights.find((h) => h.id === "tasks")).toBeUndefined();
    expect(highlights.map((h) => h.id)).toEqual(["requests", "lmps"]);
  });

  it("só numera fontes autorizadas — forbidden/unavailable nunca vira 0", () => {
    const sections = sectionsWith({
      requests: { status: "forbidden", items: [] },
      lmps: { status: "available", items: [TASK], total: 9 },
    });
    const highlights = buildHeroHighlights(sections, false);
    expect(highlights).toHaveLength(1);
    expect(highlights[0].id).toBe("lmps");
    expect(highlights[0].value).toBe("9");
  });

  it("empty → 0 legítimo; available sem total usa tamanho da lista", () => {
    const sections = sectionsWith({
      requests: { status: "available", items: [ITEM, ITEM] },
      lmps: { status: "empty", items: [] },
    });
    const highlights = buildHeroHighlights(sections, false);
    const requests = highlights.find((h) => h.id === "requests");
    const lmps = highlights.find((h) => h.id === "lmps");
    expect(requests?.value).toBe("2");
    expect(lmps?.value).toBe("0");
  });
});

describe("buildOverviewRows", () => {
  it("espelha o estado oficial de cada seção sem recomputar authz", () => {
    const home: HomeResponse = {
      schema_version: "1.0",
      generated_at: "2026-10-25T12:00:00Z",
      status: "partial",
      sections: sectionsWith({
        tasks: { status: "available", items: [TASK], total: 3 },
        requests: { status: "forbidden", items: [] },
      }),
    };
    const rows = buildOverviewRows(home);
    const tasks = rows.find((r) => r.key === "tasks");
    const requests = rows.find((r) => r.key === "requests");
    expect(tasks?.statusLabel).toBe("Disponível");
    expect(tasks?.count).toBe(3);
    expect(requests?.statusLabel).toBe("Acesso negado");
    expect(requests?.count).toBeNull();
  });
});
