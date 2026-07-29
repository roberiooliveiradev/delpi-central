import { describe, expect, it } from "vitest";

import {
  reconcileChartSeriesPartAfterSeriesFieldsChange,
  reconcileTableHeaderPartsAfterVisibleKeysChange,
} from "./reconcileProjectionPartSelection";

describe("reconcileTableHeaderPartsAfterVisibleKeysChange", () => {
  it("remapeia colIndex pela chave ao reordenar / re-adicionar coluna", () => {
    expect(
      reconcileTableHeaderPartsAfterVisibleKeysChange({
        prevVisibleKeys: ["a", "b", "c"],
        nextVisibleKeys: ["a", "c", "b"],
        selectedParts: [{ kind: "headerCell", colIndex: 1 }],
      }),
    ).toEqual([{ kind: "headerCell", colIndex: 2 }]);
  });

  it("remove headerCell cuja coluna sumiu; mantém frame", () => {
    expect(
      reconcileTableHeaderPartsAfterVisibleKeysChange({
        prevVisibleKeys: ["a", "b"],
        nextVisibleKeys: ["a"],
        selectedParts: [{ kind: "headerCell", colIndex: 1 }, { kind: "frame" }],
      }),
    ).toEqual([{ kind: "frame" }]);
  });

  it("re-adicionar coluna não inventa seleção nova", () => {
    expect(
      reconcileTableHeaderPartsAfterVisibleKeysChange({
        prevVisibleKeys: ["a"],
        nextVisibleKeys: ["a", "b"],
        selectedParts: [],
      }),
    ).toEqual([]);
  });
});

describe("reconcileChartSeriesPartAfterSeriesFieldsChange", () => {
  it("remapeia seriesIndex ao reordenar séries", () => {
    expect(
      reconcileChartSeriesPartAfterSeriesFieldsChange({
        prevSeriesFields: ["qtd", "valor"],
        nextSeriesFields: ["valor", "qtd"],
        selectedPart: { kind: "series", seriesIndex: 0 },
      }),
    ).toEqual({ kind: "series", seriesIndex: 1 });
  });

  it("limpa série removida; preserva plotArea", () => {
    expect(
      reconcileChartSeriesPartAfterSeriesFieldsChange({
        prevSeriesFields: ["qtd"],
        nextSeriesFields: [],
        selectedPart: { kind: "series", seriesIndex: 0 },
      }),
    ).toBeNull();
    expect(
      reconcileChartSeriesPartAfterSeriesFieldsChange({
        prevSeriesFields: ["qtd"],
        nextSeriesFields: [],
        selectedPart: { kind: "plotArea" },
      }),
    ).toEqual({ kind: "plotArea" });
  });
});
