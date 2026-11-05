import { describe, expect, it } from "vitest";

import { APP_BASE, listPath, parseRoute } from "./kaizen";

describe("parseRoute", () => {
  it("reconhece dashboard, list, new e detail", () => {
    expect(parseRoute(APP_BASE)).toEqual({ view: "dashboard" });
    expect(parseRoute(`${APP_BASE}/cadastros`)).toEqual({
      view: "list",
      status: undefined,
      branch: undefined,
    });
    expect(parseRoute(`${APP_BASE}/novo`)).toEqual({ view: "new" });
    expect(parseRoute(`${APP_BASE}/detalhe/abc-123`)).toEqual({
      view: "detail",
      id: "abc-123",
    });
  });

  it("extrai filtros de status e unidade da query da listagem", () => {
    expect(parseRoute(`${APP_BASE}/cadastros?status=recebido&branch=02`)).toEqual({
      view: "list",
      status: "recebido",
      branch: "02",
    });
  });

  it("mantém filtros opcionais ausentes como undefined", () => {
    expect(parseRoute(`${APP_BASE}/cadastros?status=recebido`)).toEqual({
      view: "list",
      status: "recebido",
      branch: undefined,
    });
  });
});

describe("listPath", () => {
  it("monta o caminho base sem filtros", () => {
    expect(listPath()).toBe(`${APP_BASE}/cadastros`);
  });

  it("serializa filtros na query", () => {
    expect(listPath({ status: "recebido", branch: "02" })).toBe(
      `${APP_BASE}/cadastros?status=recebido&branch=02`,
    );
    expect(listPath({ status: "recebido" })).toBe(
      `${APP_BASE}/cadastros?status=recebido`,
    );
  });
});
