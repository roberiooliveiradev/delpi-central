import { describe, expect, it } from "vitest";

import type { ComunicadoBlock, ComunicadoInputBlock } from "@delpi/tv-dashboard-presentation";

import { DATE_RANGE_PRESET_PARAM, PERIOD_DAYS_PARAM } from "../../utils/dateRangePresets";

/** Espelha patchInputBlock com filterBundle (slide scope). */
function applyPatchInputBlock(
  current: { version: number; blocks?: ComunicadoBlock[]; dataFilters?: Record<string, unknown> },
  blockId: string,
  inputPatch: Partial<ComunicadoInputBlock["input"]>,
  filterBundle?: Record<string, string | number | boolean | null | undefined>,
) {
  let nextFilters = current.dataFilters;
  const nextBlocks = (current.blocks ?? []).map((item) => {
    if (item.id !== blockId || item.type !== "input") return item;
    const prevKey = String(item.input?.paramKey || "").trim();
    const nextInput = { ...item.input, ...inputPatch };
    const nextKey = String(nextInput.paramKey || "").trim();
    const scope = nextInput.targetScope === "sources" ? "sources" : "slide";
    if (scope === "slide") {
      const filters = { ...(current.dataFilters ?? {}) };
      if (prevKey && prevKey !== nextKey) {
        delete filters[prevKey];
        if (prevKey === DATE_RANGE_PRESET_PARAM || nextKey === DATE_RANGE_PRESET_PARAM) {
          delete filters[PERIOD_DAYS_PARAM];
        }
      }
      if (nextKey) {
        const value = nextInput.defaultValue;
        if (value === undefined || value === null || value === "") delete filters[nextKey];
        else filters[nextKey] = value;
      }
      if (filterBundle) {
        for (const [key, value] of Object.entries(filterBundle)) {
          if (value === undefined || value === null || value === "") delete filters[key];
          else filters[key] = value;
        }
      }
      nextFilters = Object.keys(filters).length > 0 ? filters : undefined;
    }
    return { ...item, input: nextInput } as ComunicadoBlock;
  });
  return { ...current, blocks: nextBlocks, dataFilters: nextFilters, version: 4 };
}

describe("patchInputBlock date presets", () => {
  const input: ComunicadoInputBlock = {
    id: "inp-1",
    type: "input",
    frame: { x: 0, y: 0, w: 20, h: 10 },
    input: { paramKey: DATE_RANGE_PRESET_PARAM, targetScope: "slide", defaultValue: null },
  };

  it("sincroniza dateRangePreset e periodDays no dataFilters", () => {
    const next = applyPatchInputBlock(
      { version: 4, blocks: [input] },
      "inp-1",
      { defaultValue: "last_n_days" },
      { [DATE_RANGE_PRESET_PARAM]: "last_n_days", [PERIOD_DAYS_PARAM]: 15 },
    );
    expect(next.dataFilters).toEqual({ dateRangePreset: "last_n_days", periodDays: 15 });
  });
});
