import { describe, expect, it } from "vitest";
import { resolveAppRoute, routeHref } from "./routing";

describe("rotas de responsáveis e CAPEX", () => {
  it("resolve rota administrativa de responsáveis", () => {
    expect(
      resolveAppRoute("/apps/planejamento-orcamentario/admin/responsaveis"),
    ).toBe("admin-responsaveis");
    expect(routeHref("admin-responsaveis")).toBe(
      "/apps/planejamento-orcamentario/admin/responsaveis",
    );
  });

  it("resolve elaboração CAPEX via alias para centros", () => {
    expect(resolveAppRoute("/apps/planejamento-orcamentario/capex")).toBe("centros");
    expect(
      resolveAppRoute("/apps/planejamento-orcamentario/capex/meus-centros"),
    ).toBe("centros");
  });

  it("resolve categorias CAPEX administrativas", () => {
    expect(
      resolveAppRoute("/apps/planejamento-orcamentario/admin/categorias-capex"),
    ).toBe("admin-categorias-capex");
    expect(routeHref("admin-categorias-capex")).toBe(
      "/apps/planejamento-orcamentario/admin/categorias-capex",
    );
  });

  it("resolve centros de custo administrativos", () => {
    expect(
      resolveAppRoute("/apps/planejamento-orcamentario/admin/centros-de-custo"),
    ).toBe("admin-centros-de-custo");
    expect(routeHref("admin-centros-de-custo")).toBe(
      "/apps/planejamento-orcamentario/admin/centros-de-custo",
    );
  });
});
