import { describe, expect, it } from "vitest";

import {
  buildInputValueEditorSchema,
  intersectInputParamKeysWithPresets,
} from "./inputFilterParamSchema";
import { DATE_RANGE_PRESET_PARAM } from "./dateRangePresets";
import type { DataParamSchema } from "../components/DataParamFields";

const dateRouteSchema: DataParamSchema = {
  date_start: { type: "string", format: "date", label: "Início" },
  date_end: { type: "string", format: "date", label: "Fim" },
  branch: { type: "string", label: "Filial", optional: true },
};

describe("inputFilterParamSchema", () => {
  it("inclui dateRangePreset nas chaves de parâmetro do input", () => {
    const keys = intersectInputParamKeysWithPresets([dateRouteSchema]);
    expect(keys).toContain(DATE_RANGE_PRESET_PARAM);
    expect(keys).toContain("branch");
  });

  it("expande schema com presets quando paramKey é dateRangePreset", () => {
    const schema = buildInputValueEditorSchema([dateRouteSchema], DATE_RANGE_PRESET_PARAM);
    expect(schema[DATE_RANGE_PRESET_PARAM]).toBeTruthy();
    expect(schema.date_start).toBeTruthy();
    expect(schema.date_end).toBeTruthy();
  });
});
