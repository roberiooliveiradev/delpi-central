import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import {
  resolveParamFieldHint,
  resolveParamFieldLabel,
} from "../content/dataParamCatalog";
import { enumOptionLabel, resolveParamSelectOptions, visibleParamSchema } from "./DataParamFields";

describe("resolveParamFieldLabel", () => {
  it("traduz date_start / work_center mesmo com label EN do schema", () => {
    expect(resolveParamFieldLabel("date_start", "Date start")).toBe("Data início");
    expect(resolveParamFieldLabel("date_end", "Date end")).toBe("Data fim");
    expect(resolveParamFieldLabel("work_center", "Work center")).toBe("Centro de trabalho");
  });
});

describe("resolveParamFieldHint", () => {
  it("explica date_start e work_center", () => {
    expect(resolveParamFieldHint("date_start")).toMatch(/AAAA-MM-DD/);
    expect(resolveParamFieldHint("work_center")).toMatch(/centro de trabalho/i);
    expect(resolveParamFieldHint("limit")).toMatch(/Máximo/i);
  });
});

describe("resolveParamSelectOptions", () => {
  it("usa enum do schema com labels PT", () => {
    expect(resolveParamSelectOptions("granularity", { enum: ["day", "week"] })).toEqual([
      { value: "day", label: "Dia" },
      { value: "week", label: "Semana" },
    ]);
  });

  it("converte boolean em Sim/Não", () => {
    expect(resolveParamSelectOptions("legacy", { type: "boolean" })).toEqual([
      { value: "true", label: "Sim" },
      { value: "false", label: "Não" },
    ]);
  });

  it("mantém periodDays como input numérico (sem select)", () => {
    expect(resolveParamSelectOptions("periodDays", { type: "integer" })).toBeNull();
  });

  it("retorna null para texto livre", () => {
    expect(resolveParamSelectOptions("product_code", { type: "string" })).toBeNull();
  });
});

describe("enumOptionLabel", () => {
  it("mapeia customer_segment", () => {
    expect(enumOptionLabel("customer_segment", "new_business")).toBe("Novos negócios");
  });
});

describe("visibleParamSchema", () => {
  it("remove parâmetros fixos do catálogo", () => {
    expect(
      visibleParamSchema(
        {
          periodDays: { type: "integer" },
          granularity: { type: "string", enum: ["day"] },
        },
        { granularity: "day" },
      ),
    ).toEqual({ periodDays: { type: "integer" } });
  });
});

describe("DataParamFields date range UX contract", () => {
  it("não oculta date_start/date_end do schema quando há preset", () => {
    const base = dirname(fileURLToPath(import.meta.url));
    const source = readFileSync(join(base, "./DataParamFields.tsx"), "utf8");
    expect(source).toMatch(/dateInputsLocked/);
    expect(source).toMatch(/Definido pelo período relativo/);
    expect(source).toMatch(/portalScopeClassName=\{TV_DASHBOARD_ROOT_CLASS\}/);
    expect(source).not.toMatch(/isDateRangePairKey\(key, datePair\) && !isCustom/);
  });
});
