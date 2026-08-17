import { describe, expect, it } from "vitest";

import { gestaoAprovacoesHref, resolveAppRoute, routeHref } from "./routing";

describe("routing gestao-aprovacoes", () => {
  it("resolve e monta href com query do centro", () => {
    expect(resolveAppRoute("/apps/planejamento-orcamentario/gestao-aprovacoes")).toBe(
      "gestao-aprovacoes",
    );
    expect(routeHref("gestao-aprovacoes")).toBe(
      "/apps/planejamento-orcamentario/gestao-aprovacoes",
    );
    expect(
      gestaoAprovacoesHref({ unitId: "02", costCenterId: "0205" }),
    ).toBe(
      "/apps/planejamento-orcamentario/gestao-aprovacoes?cost_center_id=0205&unit_id=02",
    );
  });
});
