import { describe, expect, it } from "vitest";

import { formatCivilDate } from "./formatters";

describe("formatCivilDate", () => {
  it("renderiza o último dia do mês sem deslocamento de fuso", () => {
    expect(formatCivilDate("2026-08-31")).toBe("31/08/2026");
    expect(formatCivilDate("2026-09-30")).toBe("30/09/2026");
    expect(formatCivilDate("2028-02-29")).toBe("29/02/2028");
  });

  it("primeiro dia do mês não retrocede para o mês anterior", () => {
    expect(formatCivilDate("2026-10-01")).toBe("01/10/2026");
    expect(formatCivilDate("2026-01-01")).toBe("01/01/2026");
  });

  it("valor nulo vira travessão e entrada inválida retorna como veio", () => {
    expect(formatCivilDate(null)).toBe("—");
    expect(formatCivilDate("")).toBe("—");
    expect(formatCivilDate("invalido")).toBe("invalido");
  });
});
