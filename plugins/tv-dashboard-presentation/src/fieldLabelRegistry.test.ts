import { describe, expect, it } from "vitest";

import type { ComunicadoDataResolved } from "./comunicadoTypes";
import {
  applyFieldLabelsToResolved,
  isAutoBakedFieldLabel,
  lookupFieldLabel,
  normalizeFieldLabels,
  patchFieldLabels,
  resolveFieldDisplayLabel,
  suggestEditableFields,
} from "./fieldLabelRegistry";
import { parseComunicadoConfig, serializeComunicadoConfig } from "./comunicadoHelpers";
import { applyViewProjection } from "./viewProjection";

const resolved: ComunicadoDataResolved = {
  kpi: { value: 1, label: "DETAILED_DESCRIPTION" },
  kpiMetrics: [{ field: "DETAILED_DESCRIPTION", value: 1, label: "DETAILED_DESCRIPTION" }],
  table: {
    columns: [
      { key: "DETAILED_DESCRIPTION", label: "DETAILED_DESCRIPTION" },
      { key: "ITEM_CODE", label: "ITEM_CODE" },
    ],
    rows: [
      { DETAILED_DESCRIPTION: "Peças sem etiqueta", ITEM_CODE: "90264019" },
    ],
  },
};

describe("fieldLabelRegistry", () => {
  it("cascata: projeção > fonte > catálogo > key", () => {
    expect(
      resolveFieldDisplayLabel({
        field: "ITEM_CODE",
        projectionLabel: "Código",
        sourceFieldLabels: { ITEM_CODE: "Item" },
        catalogLabel: "Código item",
      }),
    ).toBe("Código");
    expect(
      resolveFieldDisplayLabel({
        field: "ITEM_CODE",
        sourceFieldLabels: { ITEM_CODE: "Item" },
        catalogLabel: "Código item",
      }),
    ).toBe("Item");
    expect(
      resolveFieldDisplayLabel({
        field: "ITEM_CODE",
        catalogLabel: "Código item",
      }),
    ).toBe("Código item");
    expect(resolveFieldDisplayLabel({ field: "ITEM_CODE" })).toBe("ITEM_CODE");
  });

  it("ignora projeção assada com a chave (case-insensitive)", () => {
    expect(
      resolveFieldDisplayLabel({
        field: "DETAILED_DESCRIPTION",
        projectionLabel: "DETAILED_DESCRIPTION",
        sourceFieldLabels: { DETAILED_DESCRIPTION: "Descrição detalhada" },
      }),
    ).toBe("Descrição detalhada");
    expect(
      resolveFieldDisplayLabel({
        field: "DETAILED_DESCRIPTION",
        projectionLabel: "detailed_description",
        sourceFieldLabels: { detailed_description: "Descrição detalhada" },
      }),
    ).toBe("Descrição detalhada");
    expect(isAutoBakedFieldLabel("ITEM_CODE", "item_code")).toBe(true);
  });

  it("lookup e apply são case-insensitive", () => {
    expect(lookupFieldLabel({ detailed_description: "Descrição" }, "DETAILED_DESCRIPTION")).toBe(
      "Descrição",
    );
    const next = applyFieldLabelsToResolved(resolved, {
      detailed_description: "Descrição",
      item_code: "Código",
    });
    expect(next?.table?.columns).toEqual([
      { key: "DETAILED_DESCRIPTION", label: "Descrição" },
      { key: "ITEM_CODE", label: "Código" },
    ]);
  });

  it("normalize e patch preservam espaço no final", () => {
    expect(normalizeFieldLabels({ a: "A " })).toEqual({ a: "A " });
    expect(patchFieldLabels(undefined, "a", "Label ")).toEqual({ a: "Label " });
    expect(patchFieldLabels({ a: "A " }, "a", "  ")).toBeUndefined();
  });

  it("normalizeFieldLabels remove vazios", () => {
    expect(normalizeFieldLabels({ a: " A ", b: "  ", c: 1 })).toEqual({ a: " A " });
    expect(normalizeFieldLabels(null)).toBeUndefined();
  });

  it("applyFieldLabelsToResolved não altera keys das rows", () => {
    const next = applyFieldLabelsToResolved(resolved, {
      DETAILED_DESCRIPTION: "Descrição",
      ITEM_CODE: "Código",
    });
    expect(next?.table?.columns).toEqual([
      { key: "DETAILED_DESCRIPTION", label: "Descrição" },
      { key: "ITEM_CODE", label: "Código" },
    ]);
    expect(next?.table?.rows?.[0]).toEqual(resolved.table?.rows?.[0]);
    expect(next?.kpiMetrics?.[0]?.label).toBe("Descrição");
  });

  it("patchFieldLabels remove entrada vazia", () => {
    expect(patchFieldLabels({ a: "A" }, "a", "")).toBeUndefined();
    expect(patchFieldLabels({ a: "A" }, "b", "B")).toEqual({ a: "A", b: "B" });
  });

  it("suggestEditableFields dedupa case-insensitive preferindo chave da API", () => {
    const fields = suggestEditableFields(
      resolved,
      [{ field: "detailed_description", label: "desc catálogo" }],
      { ITEM_CODE: "Código do item" },
    );
    expect(fields.some((item) => item.field === "DETAILED_DESCRIPTION")).toBe(true);
    expect(fields.some((item) => item.field === "detailed_description")).toBe(false);
    expect(fields.some((item) => item.field === "ITEM_CODE" && item.label === "Código do item")).toBe(
      true,
    );
  });

  it("applyViewProjection não sobrescreve fieldLabels com label assado", () => {
    const labeled = applyFieldLabelsToResolved(resolved, {
      DETAILED_DESCRIPTION: "Descrição detalhada",
    });
    const projected = applyViewProjection(labeled, {
      tableProjection: {
        columns: [
          { key: "DETAILED_DESCRIPTION", label: "DETAILED_DESCRIPTION", visible: true },
          { key: "ITEM_CODE", label: "ITEM_CODE", visible: true },
        ],
      },
    });
    expect(projected?.table?.columns?.[0]?.label).toBe("Descrição detalhada");
  });

  it("serialize/load preserva fieldLabels na fonte", () => {
    const serialized = serializeComunicadoConfig({
      blocks: [
        {
          id: "src-1",
          type: "data_source",
          frame: { x: 0, y: 0, w: 10, h: 10 },
          dataBinding: { operationId: "get_x", displayMode: "auto", params: {} },
          fieldLabels: { DETAILED_DESCRIPTION: "Descrição detalhada " },
        },
      ],
    });
    const parsed = parseComunicadoConfig(serialized);
    const source = parsed.blocks?.find((block) => block.id === "src-1");
    expect(source && "fieldLabels" in source ? source.fieldLabels : undefined).toEqual({
      DETAILED_DESCRIPTION: "Descrição detalhada ",
    });
  });
});
