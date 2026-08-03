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

  it("com rotas heterogêneas (interseção vazia) oferta união + preset", () => {
    const a: DataParamSchema = {
      branch: { type: "string", label: "Filial" },
      start_date: { type: "string", format: "date" },
      end_date: { type: "string", format: "date" },
    };
    const b: DataParamSchema = {
      department_id: { type: "string", label: "Departamento" },
      start_date: { type: "string", format: "date" },
      end_date: { type: "string", format: "date" },
    };
    // Interseção não vazia (datas) → não cai na união.
    const keysShared = intersectInputParamKeysWithPresets([a, b]);
    expect(keysShared).toContain(DATE_RANGE_PRESET_PARAM);
    expect(keysShared).toContain("start_date");
    expect(keysShared).not.toContain("branch");

    // Sem chave em comum → união.
    const c: DataParamSchema = { branch: { type: "string" } };
    const d: DataParamSchema = { department_id: { type: "string" } };
    const keysUnion = intersectInputParamKeysWithPresets([c, d]);
    expect(keysUnion).toEqual(expect.arrayContaining(["branch", "department_id"]));
  });
});
