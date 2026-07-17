import { describe, expect, it } from "vitest";

import { ApiClientError, resolveApiErrorTitle, toSectionError } from "../types/api";
import {
  computeDisplayBalance,
  computeDisplayDeficit,
  formatApiErrorMessage,
  formatUnitPricePtBr,
  isPermissionError,
} from "./formatters";

describe("formatters", () => {
  it("formata preço unitário com até 4 casas decimais", () => {
    expect(formatUnitPricePtBr(12.5)).toMatch(/12,50/);
    expect(formatUnitPricePtBr(0.0123)).toMatch(/0,0123/);
    expect(formatUnitPricePtBr(null)).toBe("—");
  });

  it("calcula saldo exibido como soma dos armazéns 01, 98 e 99", () => {
    expect(
      computeDisplayBalance({
        primary_stock: 50,
        warehouse_98_stock: 5,
        warehouse_99_stock: 10,
      }),
    ).toBe(65);
  });

  it("calcula déficit como estoque de segurança menos saldo disponível", () => {
    expect(
      computeDisplayDeficit({
        safety_stock: 100,
        primary_stock: 50,
        warehouse_98_stock: 20,
        warehouse_99_stock: 10,
      }),
    ).toBe(20);
  });
  it("formata erro de permissão", () => {
    const error = new ApiClientError(
      "Você não possui permissão para consultar o Estoque de Segurança ou a filial solicitada.",
      403,
      "forbidden",
      { retryable: false },
    );
    expect(formatApiErrorMessage(error)).toContain("permissão");
    expect(isPermissionError(error)).toBe(true);
  });

  it("mapeia títulos por status HTTP", () => {
    expect(toSectionError(new ApiClientError("msg", 401, "auth")).title).toBe("Sessão expirada");
    expect(toSectionError(new ApiClientError("msg", 403, "forbidden")).title).toBe("Acesso negado");
    expect(toSectionError(new ApiClientError("msg", 400, "validation")).title).toBe(
      "Filtros inválidos",
    );
    expect(toSectionError(new ApiClientError("msg", 503, "unavailable")).title).toBe(
      "Dados temporariamente indisponíveis",
    );
    expect(toSectionError(new ApiClientError("msg", 500, "unknown")).title).toBe(
      "Não foi possível carregar os dados",
    );
  });

  it("expõe resolveApiErrorTitle para cada kind", () => {
    expect(resolveApiErrorTitle("auth")).toBe("Sessão expirada");
    expect(resolveApiErrorTitle("forbidden")).toBe("Acesso negado");
    expect(resolveApiErrorTitle("validation")).toBe("Filtros inválidos");
    expect(resolveApiErrorTitle("unavailable")).toBe("Dados temporariamente indisponíveis");
  });
});
