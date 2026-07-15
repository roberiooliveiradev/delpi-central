import { describe, expect, it } from "vitest";
import { inadimplenciaApiPaths } from "./inadimplenciaApi";
import {
  buildClientesQuery,
  buildMensalQuery,
  buildPeriodQuery,
  buildTitulosQuery,
  queryString,
} from "../utils/queryParams";

describe("inadimplenciaApi paths", () => {
  it("aponta para o prefixo oficial da api-delpi", () => {
    expect(inadimplenciaApiPaths.resumo).toBe(
      "/apps/api-delpi/financeiro/inadimplencia/resumo",
    );
    expect(inadimplenciaApiPaths.mensal).toBe(
      "/apps/api-delpi/financeiro/inadimplencia/mensal",
    );
    expect(inadimplenciaApiPaths.faixasAtraso).toBe(
      "/apps/api-delpi/financeiro/inadimplencia/faixas-atraso",
    );
    expect(inadimplenciaApiPaths.clientes).toBe(
      "/apps/api-delpi/financeiro/inadimplencia/clientes",
    );
    expect(inadimplenciaApiPaths.titulos).toBe(
      "/apps/api-delpi/financeiro/inadimplencia/titulos",
    );
  });
});

describe("query builders", () => {
  it("omite período quando não informado", () => {
    expect(queryString(buildPeriodQuery({}))).toBe("");
  });

  it("serializa período exclusivo", () => {
    const qs = queryString(
      buildPeriodQuery({ startDate: "2025-07-01", endDate: "2026-07-01" }),
    );
    expect(qs).toContain("start_date=2025-07-01");
    expect(qs).toContain("end_date=2026-07-01");
  });

  it("serializa clientes com only_with_delays e busca", () => {
    const params = buildClientesQuery({
      startDate: "2025-07-01",
      endDate: "2026-07-01",
      page: 2,
      pageSize: 20,
      sortBy: "late_amount",
      sortDir: "desc",
      q: "WEG",
      onlyWithDelays: true,
    });
    expect(params.get("page")).toBe("2");
    expect(params.get("only_with_delays")).toBe("true");
    expect(params.get("q")).toBe("WEG");
    expect(params.get("sort_by")).toBe("late_amount");
  });

  it("serializa títulos com status e faixa", () => {
    const params = buildTitulosQuery({
      customerCode: "000001",
      storeCode: "09",
      status: "late",
      delayRange: "ATRASO_ACIMA_30_DIAS",
      page: 1,
    });
    expect(params.get("customer_code")).toBe("000001");
    expect(params.get("store_code")).toBe("09");
    expect(params.get("status")).toBe("late");
    expect(params.get("delay_range")).toBe("ATRASO_ACIMA_30_DIAS");
  });

  it("serializa série mensal com cliente", () => {
    const params = buildMensalQuery({
      startDate: "2025-08-01",
      endDate: "2026-08-01",
      customerCode: "000001",
      storeCode: "09",
    });
    expect(params.get("customer_code")).toBe("000001");
    expect(params.get("store_code")).toBe("09");
  });

  it("serializa série mensal com lista de clientes", () => {
    const params = buildMensalQuery({
      startDate: "2025-08-01",
      endDate: "2026-08-01",
      customers: ["000001/09", "000179/01"],
      customerCode: "ignored",
    });
    expect(params.get("customers")).toBe("000001/09,000179/01");
    expect(params.get("customer_code")).toBeNull();
  });

  it("serializa série mensal com flag Novos Negócios", () => {
    const params = buildMensalQuery({
      startDate: "2025-08-01",
      endDate: "2026-08-01",
      novosNegocios: true,
    });
    expect(params.get("novos_negocios")).toBe("true");
  });
});
