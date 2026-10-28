import { describe, expect, it } from "vitest";

import {
  buildEventItems,
  buildHeroHighlights,
  buildOverviewRows,
  buildSectionView,
  eventsSourcesDegraded,
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

describe("buildEventItems", () => {
  it("agrega attention/tasks/requests com href oficial", () => {
    const sections = sectionsWith({
      tasks: { status: "available", items: [TASK] },
      requests: { status: "available", items: [ITEM] },
    });
    const items = buildEventItems(sections, "Abrir", () => {});
    expect(items).toHaveLength(2);
    expect(items[0].actionLabel).toBe("Abrir");
    expect(items[0].onAction).toBeDefined();
  });

  it("href fora de /apps/ não vira ação (não inventa link)", () => {
    const sections = sectionsWith({
      tasks: {
        status: "available",
        items: [{ ...TASK, href: "https://externo.invalid/x" }],
      },
    });
    const items = buildEventItems(sections, "Abrir", () => {});
    expect(items[0].actionLabel).toBeUndefined();
    expect(items[0].onAction).toBeUndefined();
  });

  it("seção forbidden/unavailable não contribui itens", () => {
    const sections = sectionsWith({
      tasks: { status: "forbidden", items: [] },
      requests: { status: "unavailable", items: [] },
    });
    expect(buildEventItems(sections, "Abrir", () => {})).toHaveLength(0);
  });
});

describe("eventsSourcesDegraded", () => {
  it("sinaliza degraded quando fonte falha ou é negada", () => {
    expect(
      eventsSourcesDegraded(
        sectionsWith({ tasks: { status: "forbidden", items: [] } }),
      ),
    ).toBe(true);
    expect(eventsSourcesDegraded(sectionsWith({}))).toBe(false);
  });
});

describe("buildHeroHighlights", () => {
  it("só numera fontes autorizadas — forbidden/unavailable nunca vira 0", () => {
    const sections = sectionsWith({
      tasks: { status: "available", items: [TASK], total: 4 },
      requests: { status: "forbidden", items: [] },
      lmps: { status: "unavailable", items: [] },
    });
    const highlights = buildHeroHighlights(sections, false);
    expect(highlights).toHaveLength(1);
    expect(highlights[0].id).toBe("tasks");
    expect(highlights[0].value).toBe("4");
  });

  it("empty → 0 legítimo; available sem total usa tamanho da lista", () => {
    const sections = sectionsWith({
      tasks: { status: "available", items: [TASK, TASK] },
      lmps: { status: "empty", items: [] },
    });
    const highlights = buildHeroHighlights(sections, false);
    const tasks = highlights.find((h) => h.id === "tasks");
    const lmps = highlights.find((h) => h.id === "lmps");
    expect(tasks?.value).toBe("2");
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
