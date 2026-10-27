/**
 * RW01 — serialização/validação dos filtros das páginas contextuais.
 * A URL é a fonte recuperável: todo parâmetro é validado na entrada e
 * valores desconhecidos caem em defaults seguros — nunca consulta com
 * estado de outra competência.
 */
import { describe, expect, it } from "vitest";

import {
  parseSettlementsQuery,
  parseStockQuery,
  pickFamilyParams,
  serializeSettlementsQuery,
  serializeStockQuery,
  SETTLEMENT_PARAMS,
  STOCK_PARAMS,
} from "./reportQueryParams";

const OCTOBER = { startDate: "2026-10-01", endDate: "2026-10-31" };

describe("parseSettlementsQuery", () => {
  it("defaults: URL vazia restaura a competência da rota", () => {
    const parsed = parseSettlementsQuery(new URLSearchParams(), OCTOBER);
    expect(parsed).toEqual({
      side: "payable",
      startDate: "2026-10-01",
      endDate: "2026-10-31",
      natureCode: "",
      movementType: "",
      sortBy: "settlement_date",
      sortDir: "desc",
      page: 1,
    });
  });

  it("valores válidos são restaurados integralmente", () => {
    const parsed = parseSettlementsQuery(
      new URLSearchParams(
        "side=receivable&start=2026-10-05&end=2026-10-20" +
          "&nature=100&movement=BA&sort=nature&dir=asc&page=3",
      ),
      OCTOBER,
    );
    expect(parsed).toEqual({
      side: "receivable",
      startDate: "2026-10-05",
      endDate: "2026-10-20",
      natureCode: "100",
      movementType: "BA",
      sortBy: "nature",
      sortDir: "asc",
      page: 3,
    });
  });

  it("datas de outra competência descartam o par inteiro", () => {
    const parsed = parseSettlementsQuery(
      new URLSearchParams("start=2026-05-01&end=2026-05-31"),
      OCTOBER,
    );
    expect(parsed.startDate).toBe("2026-10-01");
    expect(parsed.endDate).toBe("2026-10-31");
  });

  it("par com início após o fim ou formato inválido é descartado", () => {
    for (const query of [
      "start=2026-10-20&end=2026-10-05",
      "start=2026-1&end=2026-10-31",
      "start=abc&end=2026-10-31",
      "start=2026-10-01",
    ]) {
      const parsed = parseSettlementsQuery(
        new URLSearchParams(query),
        OCTOBER,
      );
      expect(parsed.startDate).toBe("2026-10-01");
      expect(parsed.endDate).toBe("2026-10-31");
    }
  });

  it("enums desconhecidos e página inválida caem em defaults", () => {
    const parsed = parseSettlementsQuery(
      new URLSearchParams(
        "side=x&sort=valor&dir=up&page=-4",
      ),
      OCTOBER,
    );
    expect(parsed.side).toBe("payable");
    expect(parsed.sortBy).toBe("settlement_date");
    expect(parsed.sortDir).toBe("desc");
    expect(parsed.page).toBe(1);
  });

  it("round-trip serialização → parse preserva o estado", () => {
    const filters = {
      side: "receivable" as const,
      startDate: "2026-10-05",
      endDate: "2026-10-20",
      natureCode: "100",
      movementType: "BA",
      sortBy: "nature",
      sortDir: "asc" as const,
      page: 4,
    };
    const parsed = parseSettlementsQuery(
      new URLSearchParams(serializeSettlementsQuery(filters)),
      OCTOBER,
    );
    expect(parsed).toEqual(filters);
  });
});

describe("parseStockQuery", () => {
  it("defaults: URL vazia", () => {
    expect(parseStockQuery(new URLSearchParams())).toEqual({
      branch: "all",
      scope: "all_products",
      warehouse: "",
      page: 1,
    });
  });

  it("valores válidos restaurados; enums desconhecidos caem em defaults", () => {
    expect(
      parseStockQuery(
        new URLSearchParams("branch=02&scope=mp_pi_pa&warehouse=04&page=2"),
      ),
    ).toEqual({
      branch: "02",
      scope: "mp_pi_pa",
      warehouse: "04",
      page: 2,
    });
    expect(
      parseStockQuery(
        new URLSearchParams("branch=99&scope=tudo&page=0"),
      ),
    ).toEqual({
      branch: "all",
      scope: "all_products",
      warehouse: "",
      page: 1,
    });
  });

  it("round-trip serialização → parse preserva o estado", () => {
    const filters = {
      branch: "02" as const,
      scope: "mp_pi_pa" as const,
      warehouse: "04",
      page: 3,
    };
    expect(
      parseStockQuery(
        new URLSearchParams(serializeStockQuery(filters)),
      ),
    ).toEqual(filters);
  });
});

describe("pickFamilyParams", () => {
  it("seleciona apenas os parâmetros da família — sem vazamento", () => {
    const search = new URLSearchParams(
      "tab=reports&report=stock&branch=01&warehouse=04&page=2&nature=100",
    );
    const stock = pickFamilyParams(search, STOCK_PARAMS);
    expect(stock.get("branch")).toBe("01");
    expect(stock.get("page")).toBe("2");
    expect(stock.get("nature")).toBeNull();
    expect(stock.get("tab")).toBeNull();

    const settlements = pickFamilyParams(search, SETTLEMENT_PARAMS);
    expect(settlements.get("nature")).toBe("100");
    expect(settlements.get("branch")).toBeNull();
  });
});
