import { describe, expect, it } from "vitest";

import { pessoalHref, resolveAppRoute, routeHref } from "./routing";

describe("routing pessoal", () => {
  it("resolve rota /pessoal", () => {
    expect(resolveAppRoute("/apps/planejamento-orcamentario/pessoal")).toBe("pessoal");
    expect(routeHref("pessoal")).toBe("/apps/planejamento-orcamentario/pessoal");
  });

  it("preserva filial e centro na URL", () => {
    expect(
      pessoalHref({ costCenterId: "205", unitId: "01" }),
    ).toBe(
      "/apps/planejamento-orcamentario/pessoal?cost_center_id=205&unit_id=01",
    );
    expect(
      pessoalHref({ costCenterId: "205", unitId: "02" }),
    ).toBe(
      "/apps/planejamento-orcamentario/pessoal?cost_center_id=205&unit_id=02",
    );
  });
});
