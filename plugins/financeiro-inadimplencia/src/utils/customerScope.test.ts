import { describe, expect, it } from "vitest";
import {
  isExcludedCustomer,
  isNovosNegociosCustomer,
  isWegCustomer,
  WEG_CUSTOMER_CODE,
} from "./customerScope";

describe("customerScope", () => {
  it("exclui 000207 do plugin", () => {
    expect(isExcludedCustomer("000207")).toBe(true);
    expect(isExcludedCustomer("000001")).toBe(false);
  });

  it("identifica WEG e Novos Negócios", () => {
    expect(isWegCustomer(WEG_CUSTOMER_CODE)).toBe(true);
    expect(isNovosNegociosCustomer("000179")).toBe(true);
    expect(isNovosNegociosCustomer("000001")).toBe(false);
    expect(isNovosNegociosCustomer("000207")).toBe(false);
  });
});
