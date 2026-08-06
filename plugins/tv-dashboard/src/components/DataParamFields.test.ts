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

  it("rótulos PT para visão Transformômetro", () => {
    expect(
      resolveParamSelectOptions("view", {
        enum: ["consolidated", "filial", "department"],
      }),
    ).toEqual([
      { value: "consolidated", label: "Consolidado" },
      { value: "filial", label: "Filial" },
      { value: "department", label: "Departamento" },
    ]);
  });

  it("converte boolean em Sim/Não", () => {
    expect(resolveParamSelectOptions("legacy", { type: "boolean" })).toEqual([
      { value: "true", label: "Sim" },
      { value: "false", label: "Não" },
    ]);
  });

  it("branch com enum no schema vira select mesmo sem branchScope", () => {
    expect(resolveParamSelectOptions("branch", { enum: ["01", "02"] })).toEqual([
      { value: "01", label: "Filial 01" },
      { value: "02", label: "Filial 02" },
    ]);
  });

  it("retorna null para texto livre", () => {
    expect(resolveParamSelectOptions("product_code", { type: "string" })).toBeNull();
  });
});

describe("enumOptionLabel", () => {
  it("mapeia customer_segment", () => {
    expect(enumOptionLabel("customer_segment", "new_business")).toBe("Novos negócios");
  });

  it("traduz rank_by / metric / sort de horas improdutivas", () => {
    expect(enumOptionLabel("rank_by", "stop_reason")).toBe("Motivo de parada");
    expect(enumOptionLabel("rank_by", "resource")).toBe("Recurso");
    expect(enumOptionLabel("rank_by", "cost_center")).toBe("Centro de custo");
    expect(enumOptionLabel("rank_by", "operator")).toBe("Operador");
    expect(enumOptionLabel("rank_by", "product")).toBe("Produto");
    expect(enumOptionLabel("rank_by", "operation")).toBe("Operação");
    expect(enumOptionLabel("metric", "hours")).toBe("Horas");
    expect(enumOptionLabel("metric", "cost")).toBe("Custo");
    expect(enumOptionLabel("sort", "date_desc")).toBe("Data ↓");
    expect(enumOptionLabel("sort", "hours_asc")).toBe("Horas ↑");
    expect(enumOptionLabel("sort", "cost_desc")).toBe("Custo ↓");
  });

  it("traduz enums PCP de OPs", () => {
    expect(enumOptionLabel("rank_by", "warehouse")).toBe("Armazém");
    expect(enumOptionLabel("rank_by", "op")).toBe("OP");
    expect(enumOptionLabel("metric", "order_qty")).toBe("Qtd. ordem");
    expect(enumOptionLabel("metric", "balance")).toBe("Saldo");
    expect(enumOptionLabel("sort", "delivery_desc")).toBe("Entrega ↓");
    expect(enumOptionLabel("sort", "delay_desc")).toBe("Atraso ↓");
  });

  it("traduz enums que antes apareciam crus no TV", () => {
    expect(enumOptionLabel("department_id", "production")).toBe("Produção");
    expect(enumOptionLabel("audit_status", "evaluation_complete")).toBe("Avaliação concluída");
    expect(enumOptionLabel("severity", "critical")).toBe("Crítica");
    expect(enumOptionLabel("shift", "TURNO_1")).toBe("Turno 1");
    expect(enumOptionLabel("status", "below_safety_stock")).toBe("Abaixo do estoque de segurança");
    expect(enumOptionLabel("status", "1")).toBe("Registrada (1)");
    expect(enumOptionLabel("result", "A")).toBe("Aprovado (A)");
    expect(enumOptionLabel("group_by", "product_group")).toBe("Grupo de produto");
    expect(enumOptionLabel("granularity", "auto")).toBe("Automático");
  });
});

describe("resolveParamSelectOptions horas improdutivas", () => {
  it("exibe labels PT para rank_by", () => {
    expect(
      resolveParamSelectOptions("rank_by", {
        enum: ["stop_reason", "resource", "cost_center", "operator", "product", "operation"],
      }),
    ).toEqual([
      { value: "stop_reason", label: "Motivo de parada" },
      { value: "resource", label: "Recurso" },
      { value: "cost_center", label: "Centro de custo" },
      { value: "operator", label: "Operador" },
      { value: "product", label: "Produto" },
      { value: "operation", label: "Operação" },
    ]);
  });

  it("exibe labels PT para metric", () => {
    expect(resolveParamSelectOptions("metric", { enum: ["hours", "cost"] })).toEqual([
      { value: "hours", label: "Horas" },
      { value: "cost", label: "Custo" },
    ]);
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

  it("passa enum do schema para BranchField (Configurar fonte)", () => {
    const base = dirname(fileURLToPath(import.meta.url));
    const source = readFileSync(join(base, "./DataParamFields.tsx"), "utf8");
    expect(source).toMatch(/schemaEnum=\{field\.enum\}/);
  });

  it("respeita openEndedDateRange e resolveFallbackPreset (contrato)", () => {
    const base = dirname(fileURLToPath(import.meta.url));
    const source = readFileSync(join(base, "./DataParamFields.tsx"), "utf8");
    expect(source).toMatch(/openEndedDateRange/);
    expect(source).toMatch(/hydrateDefaultPreset/);
    expect(source).toMatch(/filterLayer/);
    expect(source).toMatch(/resolveFallbackPreset/);
    expect(source).toMatch(/openEndedDateRange \? "custom" : "this_month"/);
    expect(source).toMatch(/filterPeriodRequired/);
    expect(source).toMatch(/buildFilterSelectOptions/);
    expect(source).toMatch(/DIVERGED_FILTER_SELECT_VALUE|dataParamFilterUi/);
  });

  it("camada agregada usa filterUnsetHere / filterValuesDiffer", () => {
    const base = dirname(fileURLToPath(import.meta.url));
    const source = readFileSync(join(base, "./DataParamFields.tsx"), "utf8");
    expect(source).toMatch(/filterUnsetHere/);
    expect(source).toMatch(/filterValuesDiffer/);
    expect(source).toMatch(/divergedKeys/);
    expect(source).toMatch(/emptyChoiceLabel/);
    expect(source).toMatch(/aggregateLayer/);
    expect(source).toMatch(/resolveFilterClearLabel/);
  });

  it("expõe Não definido aqui em selects, Período e inputs (dados/tela/programação)", () => {
    const base = dirname(fileURLToPath(import.meta.url));
    const source = readFileSync(join(base, "./DataParamFields.tsx"), "utf8");
    expect(source).toMatch(/filterUnsetHere/);
    expect(source).toMatch(/filterClear/);
    expect(source).toMatch(/ClearableControl/);
    expect(source).toMatch(/td-data-param-clearable/);
    expect(source).toMatch(/buildFilterSelectOptions/);
    expect(source).toMatch(/canClearFilterValue/);
    expect(source).toMatch(/filterAllBranches|resolveBranchEmptyLabel/);
  });
});
