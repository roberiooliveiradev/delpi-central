import { describe, expect, it } from "vitest";

import {
  buildFilterSearchParams,
  defaultLmpsFilterState,
  readLmpsFilters,
} from "./filterUrl";

describe("filtros na URL — round-trip e semântica legada", () => {
  it("serializa os mesmos query keys do MFE legado", () => {
    const query = buildFilterSearchParams({
      dateStart: "2026-10-01",
      dateEnd: "2026-10-31",
      competence: "2026-10",
      branches: ["01", "02"],
      listingTypes: ["LMP", "Amostra"],
      statuses: ["Atrasado"],
    });
    const params = new URLSearchParams(query);
    expect(params.get("start_date")).toBe("2026-10-01");
    expect(params.get("end_date")).toBe("2026-10-31");
    expect(params.get("competence")).toBe("2026-10");
    expect(params.get("branch")).toBe("01,02");
    expect(params.get("listing_type")).toBe("LMP,Amostra");
    expect(params.get("status")).toBe("Atrasado");
  });

  it("round-trip preserva seleções múltiplas (CSV)", () => {
    const state = {
      dateStart: "2026-10-01",
      dateEnd: "2026-10-15",
      competence: "",
      branches: ["01", "02"],
      listingTypes: ["LMP"],
      statuses: ["Atrasado", "Pontual"],
    };
    const restored = readLmpsFilters(
      buildFilterSearchParams(state),
    );
    expect(restored.branches).toEqual(["01", "02"]);
    expect(restored.listingTypes).toEqual(["LMP"]);
    expect(restored.statuses).toEqual(["Atrasado", "Pontual"]);
    expect(restored.dateStart).toBe("2026-10-01");
    expect(restored.dateEnd).toBe("2026-10-15");
  });

  it("query vazia retorna o estado padrão (mês corrente)", () => {
    const defaults = defaultLmpsFilterState();
    const parsed = readLmpsFilters("");
    expect(parsed).toEqual(defaults);
    expect(parsed.branches).toEqual([]);
  });

  it("parâmetros inválidos são ignorados com defaults honestos", () => {
    const parsed = readLmpsFilters("?start_date=lixo&competence=abc");
    expect(parsed.dateStart).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(parsed.competence ?? "").not.toBe("abc");
  });
});
