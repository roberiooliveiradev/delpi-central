import { describe, expect, it } from "vitest";

import { demandStatusBadge, demandStatusOptions, isDemandActionable } from "./demandStatus";

describe("demandStatus", () => {
  it("marca atraso como crítico e cobertura por estoque como resolvida", () => {
    expect(demandStatusBadge("late").variant).toBe("danger");
    expect(demandStatusBadge("covered_by_stock").variant).toBe("success");
  });

  it("distingue cobertura por OP de falta de cobertura", () => {
    expect(demandStatusBadge("covered_by_order").variant).toBe("info");
    expect(demandStatusBadge("at_risk").variant).toBe("warning");
  });

  it("cai em sem cobertura quando o status vem vazio ou desconhecido", () => {
    expect(demandStatusBadge(null).label).toBe(demandStatusBadge("at_risk").label);
    expect(demandStatusBadge("unknown").variant).toBe("warning");
  });

  it("descarta status fora do contrato ao montar as opções do filtro", () => {
    const options = demandStatusOptions(["late", "hacked", "covered_by_order"]);
    expect(options.map((option) => option.value)).toEqual(["late", "covered_by_order"]);
  });

  it("aponta só as linhas que exigem ação do PCP", () => {
    expect(isDemandActionable({ status: "late" })).toBe(true);
    expect(isDemandActionable({ status: "at_risk" })).toBe(true);
    expect(isDemandActionable({ status: "covered_by_order" })).toBe(false);
    expect(isDemandActionable({ status: "covered_by_stock" })).toBe(false);
  });
});
