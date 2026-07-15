import { describe, expect, it } from "vitest";

import { buildRegistroDetailPath, parseScrapPath, readRegistroFromSearch } from "./routes";

describe("scrap routes", () => {
  it("detecta dashboard e detalhe por pathname", () => {
    expect(parseScrapPath("/apps/scrap-monitoring/sc")).toEqual({
      view: "dashboard",
      branchRoute: "SC",
    });
    expect(parseScrapPath("/apps/scrap-monitoring/es/registro")).toEqual({
      view: "registro-detail",
      branchRoute: "ES",
    });
  });

  it("serializa e lê registro do detalhe", () => {
    const path = buildRegistroDetailPath("SC", {
      filial: "01",
      dataPerda: "2026-07-01",
      op: "OP1",
      pa: "PA1",
      mp: "MP1",
      descricao: "Cabo",
      um: "KG",
      motivoCodigo: "FM",
      motivo: "Falha",
      quantidade: 2,
      valor: 10.5,
      centroTrabalho: "CT-1",
      codigoOperador: "1",
      nomeOperador: "Ana",
    });

    expect(path).toContain("/apps/scrap-monitoring/sc/registro?");
    const search = path.slice(path.indexOf("?"));
    const item = readRegistroFromSearch(search);
    expect(item?.op).toBe("OP1");
    expect(item?.valor).toBe(10.5);
    expect(item?.motivo).toBe("Falha");
  });
});
