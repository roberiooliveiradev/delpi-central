import { describe, expect, it } from "vitest";

import {
  centrosHref,
  pessoalHref,
  resolveAppRoute,
  routeHref,
} from "./routing";

describe("routing centros (elaboração unificada)", () => {
  it("mapeia /centros, /capex e /pessoal para a rota centros", () => {
    expect(resolveAppRoute("/apps/planejamento-orcamentario/centros")).toBe("centros");
    expect(resolveAppRoute("/apps/planejamento-orcamentario/capex")).toBe("centros");
    expect(resolveAppRoute("/apps/planejamento-orcamentario/pessoal")).toBe("centros");
    expect(routeHref("centros")).toBe("/apps/planejamento-orcamentario/centros");
    expect(routeHref("capex")).toBe("/apps/planejamento-orcamentario/centros");
    expect(routeHref("pessoal")).toBe("/apps/planejamento-orcamentario/centros");
  });

  it("preserva query de filial e CC em centrosHref / aliases", () => {
    expect(centrosHref({ costCenterId: "0205", unitId: "02" })).toBe(
      "/apps/planejamento-orcamentario/centros?cost_center_id=0205&unit_id=02",
    );
    expect(pessoalHref({ costCenterId: "0205", unitId: "02" })).toBe(
      "/apps/planejamento-orcamentario/centros?cost_center_id=0205&unit_id=02",
    );
  });
});
