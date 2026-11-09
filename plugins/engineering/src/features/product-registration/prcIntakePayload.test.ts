import { describe, expect, it } from "vitest";

import {
  buildCreateIntakeBody,
  buildCreateReasons,
  buildUpdateIntakeBody,
  linkChangesWithReasons,
} from "./prcIntakePayload";
import type { PrcLinkOp } from "./prcDiff";
import type { SupplierRow } from "./prcSuppliers";

function row(over: Partial<SupplierRow> = {}): SupplierRow {
  return {
    supplierCode: "000002",
    store: "01",
    supplierName: "TE CONNECTIVITY",
    partNumber: "",
    catalogNumber: "",
    query: "",
    ...over,
  };
}

const REF_DATA = {
  schemaVersion: 1,
  productTypes: ["raw_material"],
  requestTypes: ["create", "update"],
  statuses: [],
  sources: ["portal-engineering"],
  editableDraftPaths: [],
  supplierKeys: { required: [], optional: [] },
  fields: [
    {
      path: "description",
      kind: "text",
      requiredCreateIntake: true,
      verifiable: true,
      maxLength: 60,
    },
  ],
};

describe("linkChangesWithReasons (D14-FIX)", () => {
  const updateOp: PrcLinkOp = {
    operation: "update",
    key: { supplierCode: "000002", store: "01" },
    fields: { partNumber: "PN-9", catalogNumber: "CAT-9" },
  };

  it("razões de PN e Catálogo são independentes", () => {
    const out = linkChangesWithReasons(
      [updateOp],
      [
        row({
          partNumber: "PN-9",
          catalogNumber: "CAT-9",
          pnReason: "motivo pn",
          catReason: "motivo cat",
        }),
      ],
    );
    expect(out[0].fieldReasons).toEqual({
      partNumber: "motivo pn",
      catalogNumber: "motivo cat",
    });
  });

  it("PN alterado sem afetar Catálogo → só razão de PN", () => {
    const out = linkChangesWithReasons(
      [
        {
          operation: "update",
          key: { supplierCode: "000002", store: "01" },
          fields: { partNumber: "PN-9" },
        } as PrcLinkOp,
      ],
      [row({ partNumber: "PN-9", pnReason: "só pn", catReason: "cat" })],
    );
    expect(out[0].fieldReasons).toEqual({ partNumber: "só pn" });
  });

  it("Catálogo alterado sem afetar PN → só razão de Catálogo", () => {
    const out = linkChangesWithReasons(
      [
        {
          operation: "update",
          key: { supplierCode: "000002", store: "01" },
          fields: { catalogNumber: "CAT-9" },
        } as PrcLinkOp,
      ],
      [row({ catalogNumber: "CAT-9", pnReason: "pn", catReason: "cat" })],
    );
    expect(out[0].fieldReasons).toEqual({ catalogNumber: "cat" });
  });

  it("desfazer a alteração retira a razão do payload mas preserva o rascunho", () => {
    // usuário reverteu PN ao baseline → op.fields não traz partNumber
    const out = linkChangesWithReasons(
      [
        {
          operation: "update",
          key: { supplierCode: "000002", store: "01" },
          fields: { catalogNumber: "CAT-9" },
        } as PrcLinkOp,
      ],
      [row({ catalogNumber: "CAT-9", pnReason: "rascunho", catReason: "c" })],
    );
    expect(out[0].fieldReasons).toEqual({ catalogNumber: "c" });
  });

  it("ADD carrega razão da operação + razões dos atributos preenchidos", () => {
    const out = linkChangesWithReasons(
      [
        {
          operation: "add",
          key: { supplierCode: "000089", store: "01" },
          fields: { partNumber: "PN-1" },
          supplierName: "NOVO FORN",
        } as PrcLinkOp,
      ],
      [
        row({
          supplierCode: "000089",
          partNumber: "PN-1",
          opReason: "inclusão homologada",
          pnReason: "pn informado",
        }),
      ],
    );
    expect(out[0].reason).toBe("inclusão homologada");
    expect(out[0].fieldReasons).toEqual({ partNumber: "pn informado" });
  });

  it("REMOVE carrega só a razão da operação, sem fields/fieldReasons", () => {
    const out = linkChangesWithReasons(
      [
        {
          operation: "remove",
          key: { supplierCode: "000002", store: "01" },
        },
      ],
      [
        row({
          opReason: "desvincular",
          pnReason: "não deve vazar",
          catReason: "não deve vazar",
        }),
      ],
    );
    expect(out[0].reason).toBe("desvincular");
    expect(out[0].fields).toEqual({});
    expect(out[0].fieldReasons).toBeUndefined();
  });

  it("sem razão registrada → fieldReasons omitido e reason vazio", () => {
    const out = linkChangesWithReasons([updateOp], [row()]);
    expect(out[0].reason).toBe("");
    expect(out[0].fieldReasons).toBeUndefined();
  });
});

describe("buildCreateReasons (D14-FIX)", () => {
  it("undefined quando nenhuma razão foi registrada", () => {
    expect(
      buildCreateReasons({ description: "X" }, {}, [row()]),
    ).toBeUndefined();
  });

  it("razão de campo só entra se o campo estiver preenchido", () => {
    const out = buildCreateReasons(
      { description: "MAT", unit: "" },
      { description: "ctx desc", unit: "ctx unit" },
      [],
    );
    expect(out?.fields).toEqual({ description: "ctx desc" });
  });

  it("razão de vínculo exige identidade oficial selecionada", () => {
    const out = buildCreateReasons(
      {},
      {},
      [
        row({ supplierCode: "", store: "", opReason: "fantasma" }),
        row({ opReason: "incluído" }),
      ],
    );
    expect(out?.supplierLinks).toEqual([
      {
        key: { supplierCode: "000002", store: "01" },
        reason: "incluído",
      },
    ]);
  });

  it("fieldReasons só para atributos preenchidos — PN nunca copia para Catálogo", () => {
    const out = buildCreateReasons(
      {},
      {},
      [
        row({
          partNumber: "PN-1",
          pnReason: "ctx pn",
          catReason: "ctx cat",
        }),
      ],
    );
    expect(out?.supplierLinks?.[0].fieldReasons).toEqual({
      partNumber: "ctx pn",
    });
  });

  it("buildCreateIntakeBody inclui reasons fora de requestedData", () => {
    const body = buildCreateIntakeBody({
      refData: REF_DATA,
      values: { description: "MAT" },
      reasons: { description: "ctx" },
      suppliers: [row({ opReason: "incl" })],
    });
    expect(body.requestedData).not.toHaveProperty("reasons");
    const suppliers = body.requestedData?.suppliers as object[];
    expect(suppliers[0]).not.toHaveProperty("reason");
    expect(body.reasons?.fields).toEqual({ description: "ctx" });
    expect(body.reasons?.supplierLinks?.[0].reason).toBe("incl");
  });
});

describe("buildUpdateIntakeBody", () => {
  it("change de campo carrega apenas a razão do próprio path", () => {
    const body = buildUpdateIntakeBody({
      refData: REF_DATA,
      officialCode: " 90264270 ",
      scalarDiff: [
        { path: "description", before: "A", after: "B" },
        { path: "unit", before: "UN", after: "KG" },
      ],
      linkOps: [],
      reasons: { description: "porque mudou" },
      suppliers: [],
    });
    expect(body.officialProductCode).toBe("90264270");
    expect(body.changes?.[0].reason).toBe("porque mudou");
    expect(body.changes?.[1].reason).toBe("");
  });
});
