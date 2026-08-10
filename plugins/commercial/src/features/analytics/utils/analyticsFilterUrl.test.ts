import { describe, expect, it } from "vitest";

import {
  buildAnalyticsOpportunityBackSearch,
  readAnalyticsOpportunitySearch,
} from "./analyticsFilterUrl";

describe("analyticsFilterUrl — busca de oportunidades", () => {
  it("hidrata search da URL com normalização", () => {
    expect(readAnalyticsOpportunitySearch("?search=%20ACME%20")).toBe("ACME");
    expect(readAnalyticsOpportunitySearch("?branch=01")).toBe("");
  });

  it("mantém search e filtros reconhecidos no retorno", () => {
    const back = buildAnalyticsOpportunityBackSearch(
      "?search=ACME&branch=01&customer_segment=weg&nao_permitido=x",
    );
    expect(back).toContain("search=ACME");
    expect(back).toContain("branch=01");
    expect(back).toContain("customer_segment=weg");
    expect(back).not.toContain("nao_permitido");
  });
});
