import { describe, expect, it } from "vitest";

import {
  buildSectionView,
  partialBannerMessage,
  sourceLabel,
} from "./homeViewModel";
import type { HomeItem, HomeSection } from "../../types/home";

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

describe("buildSectionView", () => {
  it("available → itens como TaskItemPresentation com rota autorizada", () => {
    const section: HomeSection = {
      status: "available",
      items: [ITEM],
      total: 7,
    };
    const view = buildSectionView(section);
    expect(view.kind).toBe("items");
    expect(view.items).toHaveLength(1);
    expect(view.items[0].route).toBe("/apps/my-requests");
    expect(view.items[0].actions?.canOpen).toBe(true);
    expect(view.items[0].sourceLabel).toBe("Solicitações");
    expect(view.items[0].statusLabel).toBe("Em análise");
    expect(view.totalLabel).toBe("1 de 7");
  });

  it("href fora de /apps/ não vira ação acionável", () => {
    const section: HomeSection = {
      status: "available",
      items: [{ ...ITEM, href: "https://externo.invalid/x" }],
    };
    const view = buildSectionView(section);
    expect(view.items[0].route).toBeNull();
    expect(view.items[0].actions?.canOpen).toBe(false);
  });

  it("sem href → item sem ação (não inventa link)", () => {
    const section: HomeSection = {
      status: "available",
      items: [{ ...ITEM, href: null }],
    };
    const view = buildSectionView(section);
    expect(view.items[0].route).toBeNull();
    expect(view.items[0].actions?.canOpen).toBe(false);
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
    expect(view.items).toHaveLength(0);
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

  it("not_implemented → capacidade futura claramente identificada", () => {
    const view = buildSectionView({ status: "not_implemented", items: [] });
    expect(view.kind).toBe("not_implemented");
    expect(view.message).toContain("próxima etapa");
  });
});

describe("partialBannerMessage", () => {
  it("partial → banner honesto; available/unavailable → nulo", () => {
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
