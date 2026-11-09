import { describe, expect, it } from "vitest";

import {
  computeLinkDiff,
  computeLinkDiffDetailed,
  computeScalarDiff,
  linkKeyOf,
} from "./prcDiff";

const official = [
  {
    supplierCode: "000002",
    store: "01",
    supplierName: "FORN A",
    partNumber: "880643-1",
    catalogNumber: "",
  },
  {
    supplierCode: "000089",
    store: "01",
    supplierName: "WEG",
    partNumber: "",
    catalogNumber: "C9",
  },
];

const row = (
  o: Partial<{
    rowId: string;
    origin: "official" | "draft";
    supplierCode: string;
    store: string;
    partNumber: string;
    catalogNumber: string;
    supplierName: string;
  }> = {},
) => ({
  rowId: o.rowId || "r-a",
  origin: o.origin || ("official" as const),
  supplierCode: o.supplierCode ?? "000002",
  store: o.store ?? "01",
  partNumber: o.partNumber ?? "880643-1",
  catalogNumber: o.catalogNumber ?? "",
  supplierName: o.supplierName,
});

describe("computeScalarDiff", () => {
  const base = { group: "1008", unit: "UN", description: "CABO" };
  it("detecta mudança e ignora inalterados", () => {
    expect(
      computeScalarDiff(
        base,
        { group: "1009", unit: "UN", description: "CABO" },
        ["group", "unit", "description"],
      ),
    ).toEqual([{ path: "group", before: "1008", after: "1009" }]);
  });
  it("voltar ao original zera o diff", () => {
    expect(computeScalarDiff(base, { group: "1008" }, ["group"])).toEqual(
      [],
    );
  });
  it("distingue vazio de ausente (preserva zeros à esquerda)", () => {
    expect(
      computeScalarDiff(
        { accountingAccount: "011401006" },
        { accountingAccount: "11401006" },
        ["accountingAccount"],
      ),
    ).toEqual([
      {
        path: "accountingAccount",
        before: "011401006",
        after: "11401006",
      },
    ]);
  });
});

describe("computeLinkDiff (D14-FIX-02)", () => {
  it("UPDATE só com atributos que mudaram", () => {
    const ops = computeLinkDiff(
      official,
      [
        row({ partNumber: "880643-2" }),
        row({
          rowId: "r-b",
          supplierCode: "000089",
          partNumber: "",
          catalogNumber: "C9",
        }),
      ],
      new Set(),
    );
    expect(ops).toEqual([
      {
        operation: "update",
        key: { supplierCode: "000002", store: "01" },
        fields: { partNumber: "880643-2" },
      },
    ]);
  });

  it("UPDATE de PN não altera Catálogo", () => {
    const ops = computeLinkDiff(
      official,
      [row({ partNumber: "PN-X", catalogNumber: "" })],
      new Set(),
    );
    expect(ops).toEqual([
      {
        operation: "update",
        key: { supplierCode: "000002", store: "01" },
        fields: { partNumber: "PN-X" },
      },
    ]);
  });

  it("ADD só linhas draft novas", () => {
    const ops = computeLinkDiff(
      official,
      [
        row(),
        row({
          rowId: "r-new",
          origin: "draft",
          supplierCode: "001572",
          catalogNumber: "CAT-100",
        }),
      ],
      new Set(),
    );
    expect(ops.filter((o) => o.operation === "add")).toHaveLength(1);
  });

  it("REMOVE só official marcado por rowId e vence UPDATE", () => {
    const ops = computeLinkDiff(
      official,
      [row({ rowId: "off-1", partNumber: "mudado" })],
      new Set(["off-1"]),
    );
    expect(ops).toEqual([
      {
        operation: "remove",
        key: { supplierCode: "000002", store: "01" },
      },
    ]);
  });

  it("descartar draft (ausente) não gera remove nem add", () => {
    const ops = computeLinkDiff(
      official,
      [row({ rowId: "off-1" })],
      new Set(),
    );
    expect(ops).toEqual([]);
  });

  it("ADD seguido de remoção da candidata → diff vazio", () => {
    /* Candidata existiu e foi descartada — não está em rows. */
    const ops = computeLinkDiff(official, [row({ rowId: "off-1" })], new Set());
    expect(ops.filter((o) => o.operation === "add")).toHaveLength(0);
    expect(ops.filter((o) => o.operation === "remove")).toHaveLength(0);
  });

  it("draft duplicado da chave oficial não gera add nem remove", () => {
    const detailed = computeLinkDiffDetailed(
      official,
      [
        row({ rowId: "off-1", origin: "official" }),
        row({
          rowId: "draft-dup",
          origin: "draft",
          supplierCode: "000002",
          store: "01",
          partNumber: "X",
        }),
      ],
      new Set(),
    );
    expect(detailed.conflictingKeys).toContain(linkKeyOf("000002", "01"));
    expect(detailed.ops).toEqual([]);
  });

  it("marcar remove no draft rowId é ignorado (não vira remove SA5)", () => {
    const ops = computeLinkDiff(
      official,
      [
        row({ rowId: "off-1" }),
        row({
          rowId: "draft-1",
          origin: "draft",
          supplierCode: "001572",
          store: "01",
        }),
      ],
      new Set(["draft-1"]),
    );
    expect(ops.filter((o) => o.operation === "remove")).toHaveLength(0);
    expect(ops.filter((o) => o.operation === "add")).toHaveLength(0);
  });

  it("dois fornecedores diferentes não se afetam", () => {
    const ops = computeLinkDiff(
      official,
      [
        row({ rowId: "off-1", partNumber: "NOVO" }),
        row({
          rowId: "off-2",
          supplierCode: "000089",
          partNumber: "",
          catalogNumber: "C9",
        }),
      ],
      new Set(),
    );
    expect(ops).toHaveLength(1);
    expect(ops[0]).toMatchObject({
      operation: "update",
      key: { supplierCode: "000002", store: "01" },
    });
  });

  it("ambiguidade oficial bloqueia ops da chave", () => {
    const ambOfficial = [
      ...official,
      {
        supplierCode: "000002",
        store: "01",
        supplierName: "DUP",
        partNumber: "Z",
        catalogNumber: "",
      },
    ];
    const detailed = computeLinkDiffDetailed(
      ambOfficial,
      [row({ rowId: "off-1", partNumber: "X" })],
      new Set(),
    );
    expect(detailed.ambiguousOfficialKeys).toContain(
      linkKeyOf("000002", "01"),
    );
    expect(detailed.ops).toEqual([]);
  });

  it("desfazer remoção (rowId fora do set) restaura update possível", () => {
    const ops = computeLinkDiff(
      official,
      [row({ rowId: "off-1", partNumber: "mudado" })],
      new Set(),
    );
    expect(ops[0].operation).toBe("update");
  });
});
