import { describe, expect, it } from "vitest";

import {
  applyRuntimeInputValue,
  collectInputFilterContributions,
  emptyInputFilterContributions,
  hasInputFilterContributions,
  intersectParamSchemaKeys,
  isValueAllowedByParamSchema,
  mergeFilterLayers,
  resolveInputParamSchemaField,
} from "./comunicadoInputFilters";
import type { ComunicadoBlock } from "./comunicadoTypes";

const schemaA = {
  branch: { type: "string", enum: ["01", "02"], label: "Filial" },
  periodDays: { type: "integer", label: "Dias" },
};
const schemaB = {
  branch: { type: "string", enum: ["01", "02"], label: "Filial" },
  limit: { type: "integer", label: "Limite" },
};

function inputBlock(
  id: string,
  patch: {
    paramKey: string;
    defaultValue?: string | number | boolean | null;
    targetScope?: "slide" | "sources";
    targetSourceIds?: string[];
    zIndex?: number;
  },
): ComunicadoBlock {
  return {
    id,
    type: "input",
    frame: { x: 0, y: 0, w: 20, h: 10 },
    style: { zIndex: patch.zIndex ?? 1 },
    input: {
      paramKey: patch.paramKey,
      defaultValue: patch.defaultValue,
      targetScope: patch.targetScope ?? "slide",
      targetSourceIds: patch.targetSourceIds,
    },
  };
}

describe("comunicadoInputFilters", () => {
  it("intersectParamSchemaKeys retorna só chaves comuns", () => {
    expect(intersectParamSchemaKeys([schemaA, schemaB])).toEqual(["branch"]);
  });

  it("resolveInputParamSchemaField exige chave na interseção", () => {
    expect(resolveInputParamSchemaField("periodDays", [schemaA, schemaB])).toBeNull();
    expect(resolveInputParamSchemaField("branch", [schemaA, schemaB])?.label).toBe("Filial");
  });

  it("isValueAllowedByParamSchema respeita enum", () => {
    expect(isValueAllowedByParamSchema("01", schemaA.branch)).toBe(true);
    expect(isValueAllowedByParamSchema("99", schemaA.branch)).toBe(false);
  });

  it("collect slide vs multi-fonte", () => {
    const blocks = [
      inputBlock("i1", { paramKey: "branch", defaultValue: "01", targetScope: "slide" }),
      inputBlock("i2", {
        paramKey: "periodDays",
        defaultValue: 7,
        targetScope: "sources",
        targetSourceIds: ["src-a", "src-b"],
      }),
    ];
    const contrib = collectInputFilterContributions(blocks);
    expect(contrib.slide).toEqual({ branch: "01" });
    expect(contrib.bySourceId["src-a"]).toEqual({ periodDays: 7 });
    expect(contrib.bySourceId["src-b"]).toEqual({ periodDays: 7 });
  });

  it("maior zIndex vence no mesmo paramKey", () => {
    const blocks = [
      inputBlock("low", { paramKey: "branch", defaultValue: "01", zIndex: 1 }),
      inputBlock("high", { paramKey: "branch", defaultValue: "02", zIndex: 5 }),
    ];
    expect(collectInputFilterContributions(blocks).slide.branch).toBe("02");
  });

  it("descarta valor fora do enum quando schemas fornecidos", () => {
    const blocks = [inputBlock("i1", { paramKey: "branch", defaultValue: "99" })];
    const contrib = collectInputFilterContributions(blocks, null, null, [schemaA]);
    expect(contrib.slide.branch).toBeUndefined();
  });

  it("mergeFilterLayers e runtime overrides", () => {
    expect(mergeFilterLayers({ a: 1 }, { b: 2 }, { a: 3 })).toEqual({ a: 3, b: 2 });
    const block = inputBlock("i1", {
      paramKey: "branch",
      defaultValue: "01",
      targetScope: "sources",
      targetSourceIds: ["src-a"],
    }) as Extract<ComunicadoBlock, { type: "input" }>;
    const next = applyRuntimeInputValue(emptyInputFilterContributions(), block, "02");
    expect(next.bySourceId["src-a"]?.branch).toBe("02");
    expect(hasInputFilterContributions(next)).toBe(true);
  });
});
