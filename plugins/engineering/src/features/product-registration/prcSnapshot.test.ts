import { describe, expect, it } from "vitest";

import {
  diffCellState,
  snapshotFieldsToSheetData,
  snapshotHasField,
  snapshotHasSupplierLink,
  snapshotSupplierRows,
  summarizeChangedPaths,
  supplierLinkIdentity,
} from "./prcSnapshot";

describe("snapshotFieldsToSheetData — UX-P0-01", () => {
  it("preserva o valor literal '#' sem reinterpretá-lo", () => {
    const data = snapshotFieldsToSheetData(
      {
        schemaVersion: 2,
        fields: {
          description: {
            value: "#",
            coverageState: "present",
            valueOrigin: "inherited_confirmed",
          },
        },
      },
      "30190125",
    );
    expect(data.description).toBe("#");
    expect(data.officialProductCode).toBe("30190125");
  });

  it("omite campos com cobertura != present (a view exibe '—')", () => {
    const data = snapshotFieldsToSheetData({
      schemaVersion: 2,
      fields: {
        description: { coverageState: "unknown" },
        unit: { value: "PC", coverageState: "present" },
      },
    });
    expect(data).not.toHaveProperty("description");
    expect(data.unit).toBe("PC");
  });

  it("tolerates snapshot ausente/nulo e legado sem fields", () => {
    expect(snapshotFieldsToSheetData(null)).toEqual({});
    expect(snapshotFieldsToSheetData(undefined, "30190123")).toEqual({
      officialProductCode: "30190123",
    });
    expect(snapshotFieldsToSheetData({ schemaVersion: 1 })).toEqual({});
  });

  it("mantém valores vazios/nulos persistidos como registrados", () => {
    const data = snapshotFieldsToSheetData({
      schemaVersion: 2,
      fields: {
        description: { value: "", coverageState: "present" },
        group: { value: null, coverageState: "present" },
      },
    });
    expect(data.description).toBe("");
    expect(data.group).toBeNull();
  });
});

describe("snapshotSupplierRows — identidade code|store", () => {
  const snapshot = {
    schemaVersion: 2,
    supplierLinks: {
      "000113|01": {
        linkState: "present",
        attributes: {
          supplierName: { value: "FORN A" },
          partNumber: { value: "PN-1" },
          catalogNumber: { value: "" },
        },
      },
      "000002|02": { linkState: "unknown" },
    },
  };

  it("projeta somente vínculos presentes, ordenados", () => {
    const rows = snapshotSupplierRows(snapshot as never);
    expect(rows).toEqual([
      {
        supplierCode: "000113",
        store: "01",
        supplierName: "FORN A",
        partNumber: "PN-1",
        catalogNumber: "",
      },
    ]);
  });

  it("snapshotHasSupplierLink honra linkState", () => {
    expect(
      snapshotHasSupplierLink(snapshot as never, "000113", "01"),
    ).toBe(true);
    expect(
      snapshotHasSupplierLink(snapshot as never, "000002", "02"),
    ).toBe(false);
  });
});

describe("snapshotHasField", () => {
  it("somente coverageState=present autoriza alvo de bandeira", () => {
    const snap = {
      schemaVersion: 2,
      fields: {
        unit: { value: "PC", coverageState: "present" },
        group: { coverageState: "unknown" },
      },
    };
    expect(snapshotHasField(snap as never, "unit")).toBe(true);
    expect(snapshotHasField(snap as never, "group")).toBe(false);
    expect(snapshotHasField(null, "unit")).toBe(false);
  });
});

describe("diffCellState — UX-P0-02", () => {
  it("beforePresent=false → não observado (nunca '—' como remoção)", () => {
    expect(
      diffCellState(
        { path: "unit", before: null, after: "PC", beforePresent: false },
        "before",
      ),
    ).toEqual({ kind: "not_observed" });
    expect(
      diffCellState(
        { path: "unit", before: null, after: "PC", beforePresent: false },
        "after",
      ),
    ).toEqual({ kind: "value", text: "PC" });
  });

  it("flag ausente (contrato antigo) cai no fallback empty/value", () => {
    expect(diffCellState({ path: "a", before: null }, "before")).toEqual({
      kind: "empty",
    });
    expect(
      diffCellState({ path: "a", after: "#" }, "after"),
    ).toEqual({ kind: "value", text: "#" });
  });

  it("string vazia presente é 'empty', não 'not_observed'", () => {
    expect(
      diffCellState(
        { path: "a", before: "", beforePresent: true },
        "before",
      ),
    ).toEqual({ kind: "empty" });
  });
});

describe("summarizeChangedPaths / supplierLinkIdentity", () => {
  it("separa campos técnicos de vínculos de fornecedor", () => {
    const { fieldPaths, supplierPaths } = summarizeChangedPaths([
      "description",
      "suppliers[000113|01]",
      "suppliers[000113|01].partNumber",
      "group",
    ]);
    expect(fieldPaths).toEqual(["description", "group"]);
    expect(supplierPaths).toEqual([
      "suppliers[000113|01]",
      "suppliers[000113|01].partNumber",
    ]);
    expect(summarizeChangedPaths(null)).toEqual({
      fieldPaths: [],
      supplierPaths: [],
    });
  });

  it("extrai identidade legível do path técnico", () => {
    expect(supplierLinkIdentity("suppliers[000113|01]")).toEqual({
      supplierCode: "000113",
      store: "01",
      attribute: null,
    });
    expect(
      supplierLinkIdentity("suppliers[000113|01].partNumber"),
    ).toEqual({
      supplierCode: "000113",
      store: "01",
      attribute: "partNumber",
    });
    expect(supplierLinkIdentity("description")).toBeNull();
  });
});
