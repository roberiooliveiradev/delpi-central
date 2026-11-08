import { describe, expect, it } from "vitest";

import {
  computeLinkDiff,
  computeScalarDiff,
  linkKeyOf,
} from "./prcDiff";

const official = [
  { supplierCode: "000002", store: "01", supplierName: "FORN A",
    partNumber: "880643-1", catalogNumber: "" },
  { supplierCode: "000089", store: "01", supplierName: "WEG",
    partNumber: "", catalogNumber: "C9" },
];

const row = (o = {}) => ({
  supplierCode: "000002", store: "01", partNumber: "880643-1",
  catalogNumber: "", ...o,
});

describe("computeScalarDiff", () => {
  const base = { group: "1008", unit: "UN", description: "CABO" };
  it("detecta mudança e ignora inalterados", () => {
    expect(computeScalarDiff(base,
      { group: "1009", unit: "UN", description: "CABO" },
      ["group", "unit", "description"]))
      .toEqual([{ path: "group", before: "1008", after: "1009" }]);
  });
  it("voltar ao original zera o diff", () => {
    expect(computeScalarDiff(base,
      { group: "1008" }, ["group"])).toEqual([]);
  });
  it("distingue vazio de ausente (preserva zeros à esquerda)", () => {
    expect(computeScalarDiff({ accountingAccount: "011401006" },
      { accountingAccount: "11401006" }, ["accountingAccount"]))
      .toEqual([{ path: "accountingAccount",
                  before: "011401006", after: "11401006" }]);
  });
});

describe("computeLinkDiff", () => {
  it("UPDATE só com atributos que mudaram", () => {
    const ops = computeLinkDiff(official,
      [row({ partNumber: "880643-2" }),
       row({ supplierCode: "000089", partNumber: "",
             catalogNumber: "C9" })],
      new Set());
    expect(ops).toEqual([{
      operation: "update",
      key: { supplierCode: "000002", store: "01" },
      fields: { partNumber: "880643-2" },
    }]);
  });
  it("limpar PN é mudança efetiva (vazio explícito)", () => {
    const ops = computeLinkDiff(official,
      [row({ supplierCode: "000089", partNumber: "",
             catalogNumber: "" })], new Set());
    expect(ops[0].operation).toBe("update");
    expect((ops[0] as { fields: object }).fields)
      .toEqual({ catalogNumber: "" });
  });
  it("ADD só linhas novas", () => {
    const ops = computeLinkDiff(official,
      [row(), row({ supplierCode: "001572", catalogNumber: "CAT-100" })],
      new Set());
    expect(ops.filter((o) => o.operation === "add")).toHaveLength(1);
  });
  it("REMOVE só oficial marcado e vence UPDATE", () => {
    const ops = computeLinkDiff(official,
      [row({ partNumber: "mudado" })],
      new Set([linkKeyOf("000002", "01")]));
    expect(ops).toEqual([{
      operation: "remove",
      key: { supplierCode: "000002", store: "01" },
    }]);
  });
  it("marca ignorada para chave não-oficial", () => {
    const ops = computeLinkDiff(official,
      [row(), row({ supplierCode: "999", store: "02" })],
      new Set([linkKeyOf("999", "02")]));
    expect(ops.filter((o) => o.operation === "remove")).toHaveLength(0);
    expect(ops.filter((o) => o.operation === "add")).toHaveLength(1);
  });
});
