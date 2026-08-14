import { describe, expect, it } from "vitest";
import {
  formatMoney,
  formatQuantity,
  formatTaxId,
  firstGivenName,
  itemOriginLabel,
  itemTotal,
  parseQuantityInput,
  warehouse01BalanceHint,
} from "./format";

describe("format helpers", () => {
  it("formata valor em BRL", () => {
    expect(formatMoney(10)).toMatch(/R\$/);
  });

  it("formata CNPJ", () => {
    expect(formatTaxId("12345678000199")).toBe("12.345.678/0001-99");
  });

  it("calcula total do item", () => {
    expect(itemTotal(2, 15.5)).toBe(31);
  });

  it("rótulo de origem do item", () => {
    expect(itemOriginLabel({})).toBe("Avulso");
    expect(itemOriginLabel({ sales_order: "000111", sales_order_item: "02" })).toBe(
      "PV 000111/02",
    );
  });

  it("formata quantidade sempre com 3 casas decimais", () => {
    expect(formatQuantity(0.25)).toBe("0,250");
    expect(formatQuantity(1)).toBe("1,000");
    expect(formatQuantity(10.5)).toBe("10,500");
  });

  it("monta o saldo do almoxarifado 01", () => {
    expect(warehouse01BalanceHint(12)).toBe("Saldo no almoxarifado 01: 12,000");
  });

  it("interpreta quantidade digitada com vírgula ou ponto", () => {
    expect(parseQuantityInput("0,250")).toBe(0.25);
    expect(parseQuantityInput("0.25")).toBe(0.25);
    expect(parseQuantityInput("1.234,500")).toBe(1234.5);
  });

  it("extrai o primeiro nome do solicitante", () => {
    expect(firstGivenName("Maria da Silva")).toBe("Maria");
    expect(firstGivenName("de Souza")).toBe("Souza");
    expect(firstGivenName("")).toBe("—");
  });
});
