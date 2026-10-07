import type { ComunicadoInputBlock } from "@delpi/tv-dashboard-presentation";
import { describe, expect, it } from "vitest";

import {
  buildInputEditorValues,
  buildInputValueEditorSchema,
  intersectInputParamKeysWithPresets,
  resolveFilterExpressionKeys,
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

const expressionSpec = {
  expression: { version: 1, expression: { kind: "identifier", value: "today" } },
} as unknown as ComunicadoInputBlock["input"]["defaultValue"];

function filterBlock(
  input: Partial<ComunicadoInputBlock["input"]>,
): ComunicadoInputBlock {
  return {
    id: "filter_1",
    type: "input",
    frame: { x: 0, y: 0, w: 10, h: 10 },
    input: { paramKey: "date_start", control: "date", ...input },
  } as ComunicadoInputBlock;
}

describe("resolveFilterExpressionKeys", () => {
  it("oferece Expressão só no paramKey dono quando todas as rotas aceitam", () => {
    const keys = resolveFilterExpressionKeys("date_start", [
      { paramSchema: dateRouteSchema },
      { paramSchema: { date_start: { type: "string", format: "date" } } },
    ]);
    expect([...keys]).toEqual(["date_start"]);
    expect(keys.has("date_end")).toBe(false);
  });

  it("sibling: rota com o param fixo é ignorada sem vetar as demais", () => {
    const keys = resolveFilterExpressionKeys("date_start", [
      { paramSchema: dateRouteSchema, fixedQueryParams: { date_start: "2026-01-01" } },
      { paramSchema: dateRouteSchema },
    ]);
    expect(keys.has("date_start")).toBe(true);
  });

  it.each([
    ["path", [{ paramSchema: { date_start: { type: "string", in: "path" } } }]],
    ["expressionAllowed=false", [{ paramSchema: { date_start: { type: "string", expressionAllowed: false } } }]],
    ["não declarado", [{ paramSchema: { branch: { type: "string" } } }]],
    ["só rotas fixas", [{ paramSchema: dateRouteSchema, fixedQueryParams: { date_start: "x" } }]],
  ])("negativo: %s → modo literal", (_label, routes) => {
    expect(resolveFilterExpressionKeys("date_start", routes).size).toBe(0);
  });

  it("negativo: tipos de retorno divergentes entre rotas consumidoras → modo literal", () => {
    const keys = resolveFilterExpressionKeys("limit", [
      { paramSchema: { limit: { type: "integer" } } },
      { paramSchema: { limit: { type: "boolean" } } },
    ]);
    expect(keys.size).toBe(0);
  });
});

describe("buildInputEditorValues — Filtro com expressão", () => {
  it("expressão persistida no paramKey prevalece sobre dataFilters do slide", () => {
    const values = buildInputEditorValues(
      filterBlock({ defaultValue: expressionSpec }),
      { date_start: "2026-01-01", date_end: "2026-01-31" },
      dateRouteSchema,
    );
    expect(values.date_start).toBe(expressionSpec);
    expect(values.date_end).toBe("2026-01-31");
  });

  it("negativo: literal persistido continua cedendo ao valor do slide", () => {
    const values = buildInputEditorValues(
      filterBlock({ defaultValue: "2025-12-01" }),
      { date_start: "2026-01-01" },
      dateRouteSchema,
    );
    expect(values.date_start).toBe("2026-01-01");
  });
});
