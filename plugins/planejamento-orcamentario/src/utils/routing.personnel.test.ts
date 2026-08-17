import { describe, expect, it } from "vitest";

import { pessoalHref, resolveAppRoute, routeHref } from "./routing";

describe("routing pessoal", () => {
  it("elaboração /pessoal redireciona semanticamente para centros", () => {
    expect(resolveAppRoute("/apps/planejamento-orcamentario/pessoal")).toBe("centros");
    expect(routeHref("pessoal")).toBe("/apps/planejamento-orcamentario/centros");
  });

  it("preserva filial e centro na URL unificada", () => {
    expect(pessoalHref({ costCenterId: "205", unitId: "01" })).toBe(
      "/apps/planejamento-orcamentario/centros?cost_center_id=205&unit_id=01",
    );
    expect(pessoalHref({ costCenterId: "205", unitId: "02" })).toBe(
      "/apps/planejamento-orcamentario/centros?cost_center_id=205&unit_id=02",
    );
  });
});
