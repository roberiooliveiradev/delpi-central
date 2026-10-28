import { describe, expect, it } from "vitest";

import {
  ENGINEERING_CATALOG,
  filterSectionsByQuery,
  findCatalogRoute,
  searchCatalog,
  visibleSections,
} from "./engineeringRouteCatalog";

describe("visibleSections", () => {
  it("rotas internas sempre visíveis; externas exigem permissão do owner", () => {
    const sections = visibleSections(new Set(), false);
    const ids = sections.flatMap((s) => s.routes.map((r) => r.id));
    expect(ids).toContain("overview");
    expect(ids).toContain("help");
    expect(ids).not.toContain("my_requests");
    expect(ids).not.toContain("lmps");
    expect(ids).not.toContain("dashboard");
  });

  it("permissões do host liberam atalhos externos", () => {
    const sections = visibleSections(
      new Set(["my-requests.access", "dashboard-lmps.view"]),
      false,
    );
    const ids = sections.flatMap((s) => s.routes.map((r) => r.id));
    expect(ids).toContain("my_requests");
    expect(ids).toContain("lmps");
    expect(ids).not.toContain("dashboard");
  });

  it("superadmin vê todo o catálogo", () => {
    const sections = visibleSections(new Set(), true);
    const ids = sections.flatMap((s) => s.routes.map((r) => r.id));
    expect(ids).toContain("dashboard");
    expect(ids).toContain("eva"); // futuro — visível mas desabilitado
  });
});

describe("searchCatalog", () => {
  const sections = visibleSections(new Set(), false);

  it("busca por nome, descrição e keyword, insensível a acento", () => {
    const hits = searchCatalog("visao", sections);
    expect(hits.map((h) => h.id)).toContain("overview");
  });

  it("busca por keyword cadastrada", () => {
    const hits = searchCatalog("inteligencia", sections);
    expect(hits.map((h) => h.id)).toContain("eva");
  });

  it("sem resultado → lista vazia honesta", () => {
    expect(searchCatalog("inexistente-xyz", sections)).toHaveLength(0);
  });

  it("busca não revela recurso proibido", () => {
    const hits = searchCatalog("solicitacoes", sections);
    expect(hits.map((h) => h.id)).not.toContain("my_requests");
  });

  it("hits agrupam pela seção", () => {
    const hit = searchCatalog("ajuda", sections).find(
      (h) => h.id === "help",
    );
    expect(hit?.groupLabel).toBe("Suporte");
  });
});

describe("filterSectionsByQuery", () => {
  const sections = visibleSections(new Set(), true);

  it("query vazia → catálogo completo", () => {
    expect(filterSectionsByQuery(sections, "")).toHaveLength(
      sections.length,
    );
  });

  it("seções sem match são removidas", () => {
    const filtered = filterSectionsByQuery(sections, "lmp");
    expect(filtered.map((s) => s.id).sort()).toEqual([
      "insights",
      "work",
    ]);
  });
});

describe("catalog integrity", () => {
  it("ids únicos e estáveis", () => {
    const ids = ENGINEERING_CATALOG.flatMap((s) =>
      s.routes.map((r) => r.id),
    );
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("destino futuro não tem link operacional", () => {
    const eva = findCatalogRoute("eva");
    expect(eva?.comingSoon).toBe(true);
  });

  it("destinos externos apontam para /apps/ governados", () => {
    for (const section of ENGINEERING_CATALOG) {
      for (const route of section.routes) {
        if (route.target.kind === "external") {
          expect(route.target.href).toMatch(/^\/apps\/[a-z0-9-]+/);
        }
      }
    }
  });
});
