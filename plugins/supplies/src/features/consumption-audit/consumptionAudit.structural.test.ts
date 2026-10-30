import { describe, expect, it } from "vitest";

import { isConsumptionAuditResponse } from "./api";
import { CONSUMPTION_AUDIT_CONTENT as C } from "./content";
import {
  buildTargetSearch,
  formatDatePtBr,
  formatDateTimePtBr,
  formatQuantity,
  isValidProductionOrder,
  normalizeProductionOrder,
  normalizeUnit,
  parseTargetFromSearch,
  sameTarget,
} from "./query";
import type { ConsumptionAuditResponse } from "./types";

// ——— Fixture com o shape real observado no producer (OP 24884201006) ———

const REAL_PAYLOAD: ConsumptionAuditResponse = {
  production_order: "24884201006",
  branch: "01",
  metadata: {
    contract_version: "a2-proposal-1",
    generated_at_source: "api-delpi",
    tolerance_policy: { id: "glpi1353-v0", absolute: null, percent: null },
  },
  order: {
    order_number: "248842",
    order_item: "01",
    order_sequence: "006",
    order_type: "F",
    product_code: "50226108",
    product_description: "CB2,50VDAR-00646/09/09-2900-2900",
    product_type: "PI",
    unit_of_measure: "MI",
    warehouse: "01",
    status: "N",
    priority: "500",
    planned_quantity: 0.125,
    produced_quantity: 0.0,
    produced_quantity_basis: "stock_receipt",
    emission_date: "2026-10-20",
    planned_start_date: "2026-10-29",
    due_date: "2026-10-29",
    finished_at: "",
  },
  operations: [
    {
      operation: "01",
      work_center: "CT-23",
      execution_evidence: {
        execution_state: "evidenced",
        sh8_allocation: { row_present: false, source: "SH8010", status: null },
        sh6_appointments: [
          {
            appointment_id: "UDCGH1",
            channel: "collector",
            product_code: "50226108",
            resource: "CT-23",
            reported_quantity: 0.125,
            lost_quantity: 0.0,
            reported_at: "2026-10-29",
            started_at: "2026-10-29T05:13",
            ended_at: "2026-10-29T05:27",
            type: "P",
            source: "SH6010",
            linked_hza: true,
          },
        ],
        hza_records: [
          {
            appointment_ref: "0150226108       01UDCGH1",
            resource: "",
            started_at: "2026-10-29T05:13:23",
            ended_at: "2026-10-29T05:27:59",
            status: "2",
            transaction_type: "1",
            source: "HZA010",
          },
        ],
      },
      components: [
        {
          component_code: "10010030",
          component_description: "CABO PVC 70°C 2,50MM2 VD/AR",
          component_type: "MP",
          unit_of_measure: "MT",
          bom: {
            theoretical_quantity: 80.75,
            quantity_per_unit: 646.0,
            completeness: "complete",
            structure_as_of: "order_emission_date",
            reference_date: "20261020",
            valid_from: "2026-10-20",
            valid_to: "2049-12-31",
          },
          commitment: {
            lines: 1,
            original_quantity: 80.75,
            open_quantity: 0.0,
            derived_consumed_quantity: 80.75,
            origin_orders: [],
          },
          movements: {
            classified: [
              {
                component_code: "10010030",
                direction: "outbound",
                document: "220039841",
                issue_date: "2026-10-29",
                kind: "production_consumption",
                cf: "RE2",
                tm: "999",
                quantity: 80.75,
                unit_of_measure: "MT",
                warehouse: "99",
                reversed: false,
              },
            ],
            excluded: [
              {
                component_code: "10010030",
                direction: "inbound",
                document: "220039839",
                issue_date: "2026-10-29",
                kind: "warehouse_transfer",
                cf: "RE0",
                tm: "999",
                quantity: 0.64,
                unit_of_measure: "MT",
                warehouse: "99",
                reversed: false,
                reason: "not_raw_material_consumption",
              },
            ],
            eligible_consumption_quantity: 80.75,
          },
          discrepancy: {
            reference: "derived_commitment",
            value: 0.0,
            within_tolerance: null,
          },
          classification: "reconciled",
          quality_flags: ["ambiguous_cf_semantics"],
        },
      ],
    },
    {
      operation: "02",
      work_center: "CT-35",
      execution_evidence: {
        execution_state: "pending",
        sh8_allocation: {
          row_present: true,
          source: "SH8010",
          status: null,
          quantity: 0.125,
          scheduled_start: "2026-10-30T07:56",
          scheduled_end: "2026-10-30T08:50",
        },
        sh6_appointments: [],
        hza_records: [],
      },
      components: [
        {
          component_code: "10080329",
          component_description: "TERM. OLHAL M4",
          component_type: "MP",
          unit_of_measure: "PC",
          bom: {
            theoretical_quantity: 250.0,
            quantity_per_unit: 2000.0,
            completeness: "complete",
            structure_as_of: "order_emission_date",
            reference_date: "20261020",
            valid_from: "2026-10-20",
            valid_to: "2049-12-31",
          },
          commitment: {
            lines: 1,
            original_quantity: 250.0,
            open_quantity: 250.0,
            derived_consumed_quantity: 0.0,
            origin_orders: [],
          },
          movements: {
            classified: [],
            excluded: [],
            eligible_consumption_quantity: 0.0,
          },
          discrepancy: {
            reference: "derived_commitment",
            value: 0.0,
            within_tolerance: null,
          },
          classification: "requires_investigation",
          quality_flags: [],
        },
      ],
    },
  ],
  unmatched_movements: [
    {
      binding: "no_matching_commitment",
      component_code: "MOD216",
      component_type: "MO",
      direction: "outbound",
      document: "220039840",
      issue_date: "2026-10-29",
      kind: "production_consumption",
      cf: "RE1",
      tm: "999",
      quantity: 0.233,
      unit_of_measure: "HR",
      warehouse: "01",
      reversed: false,
      reason: "labor_not_material",
    },
  ],
  related_orders: [
    {
      production_order: "24884201001",
      relationship: "same_order_number",
      confidence: "proven",
      product_code: "90264300",
      product_type: "PA",
      planned_quantity: 0.125,
      produced_quantity: 0.0,
      status: "N",
    },
  ],
  quality: {
    status: "partial",
    warnings: [
      "movements_without_commitment",
      "re0_tm999_ambiguity",
      "sh6_vs_sc2_quantity_mismatch",
    ],
    unresolved_semantics: [
      "automatic_issue_causality",
      "re0_tm999_transfer_meaning",
      "sh8_row_removal_semantics",
    ],
  },
};

describe("consumption-audit query (URL state)", () => {
  it("normaliza unidade — só filiais concretas", () => {
    expect(normalizeUnit("01")).toBe("01");
    expect(normalizeUnit("02")).toBe("02");
    expect(normalizeUnit("03")).toBeNull();
    expect(normalizeUnit("all")).toBeNull();
    expect(normalizeUnit("")).toBeNull();
    expect(normalizeUnit(null)).toBeNull();
  });

  it("normaliza e valida a chave de 11 posições da OP", () => {
    expect(normalizeProductionOrder(" 24884201006 ")).toBe("24884201006");
    expect(normalizeProductionOrder("24884201006".toLowerCase())).toBe(
      "24884201006",
    );
    expect(isValidProductionOrder("24884201006")).toBe(true);
    expect(isValidProductionOrder("2488420100A")).toBe(true);
    expect(isValidProductionOrder("2488420100")).toBe(false);
    expect(isValidProductionOrder("2488420100-6")).toBe(false);
    expect(isValidProductionOrder("")).toBe(false);
  });

  it("faz round-trip do alvo pela query string", () => {
    const target = { unit: "01" as const, productionOrder: "24884201006" };
    const search = buildTargetSearch(target);
    expect(search).toBe("?unit=01&op=24884201006");
    expect(parseTargetFromSearch(search)).toEqual(target);
    expect(sameTarget(parseTargetFromSearch(search), target)).toBe(true);
  });

  it("rejeita buscas com unidade ausente/inválida ou OP malformada", () => {
    expect(parseTargetFromSearch("?op=24884201006")).toBeNull();
    expect(parseTargetFromSearch("?unit=01")).toBeNull();
    expect(parseTargetFromSearch("?unit=03&op=24884201006")).toBeNull();
    expect(parseTargetFromSearch("?unit=all&op=24884201006")).toBeNull();
    expect(parseTargetFromSearch("?unit=01&op=ABC")).toBeNull();
    expect(parseTargetFromSearch("?unit=01&op=248842010")).toBeNull();
    expect(parseTargetFromSearch("")).toBeNull();
  });
});

describe("consumption-audit api guard", () => {
  it("aceita o payload real do producer", () => {
    expect(isConsumptionAuditResponse(REAL_PAYLOAD)).toBe(true);
  });

  it("rejeita payloads malformados — 200 com shape errado não é empty state", () => {
    expect(isConsumptionAuditResponse(null)).toBe(false);
    expect(isConsumptionAuditResponse({})).toBe(false);
    expect(isConsumptionAuditResponse({ production_order: "24884201006" })).toBe(
      false,
    );
    expect(
      isConsumptionAuditResponse({ ...REAL_PAYLOAD, operations: "x" }),
    ).toBe(false);
    expect(
      isConsumptionAuditResponse({ ...REAL_PAYLOAD, order: null }),
    ).toBe(false);
    expect(
      isConsumptionAuditResponse({
        ...REAL_PAYLOAD,
        operations: [{ work_center: "CT-23" }],
      }),
    ).toBe(false);
    expect(
      isConsumptionAuditResponse({
        ...REAL_PAYLOAD,
        quality: { status: "partial" },
      }),
    ).toBe(false);
  });
});

describe("consumption-audit content", () => {
  it("cobre todos os códigos do payload real", () => {
    for (const op of REAL_PAYLOAD.operations) {
      expect(C.executionStates[op.execution_evidence.execution_state]).toBeTruthy();
      for (const component of op.components) {
        expect(C.classifications[component.classification]).toBeTruthy();
        for (const mv of component.movements.classified) {
          expect(C.movementKinds[mv.kind]).toBeTruthy();
          expect(C.movementDirections[mv.direction]).toBeTruthy();
        }
        for (const mv of component.movements.excluded) {
          expect(C.movementKinds[mv.kind]).toBeTruthy();
          expect(C.exclusionReasons[mv.reason ?? ""]).toBeTruthy();
        }
      }
    }
    for (const warning of REAL_PAYLOAD.quality.warnings) {
      expect(C.warningLabels[warning]).toBeTruthy();
    }
    for (const item of REAL_PAYLOAD.quality.unresolved_semantics) {
      expect(C.unresolvedLabels[item]).toBeTruthy();
    }
    for (const rel of REAL_PAYLOAD.related_orders) {
      expect(C.relatedRelationships[rel.relationship]).toBeTruthy();
    }
    for (const mv of REAL_PAYLOAD.unmatched_movements) {
      expect(C.exclusionReasons[mv.reason ?? ""]).toBeTruthy();
    }
  });

  it("não vaza identificadores técnicos do ERP/API no conteúdo visível", () => {
    const strings = JSON.stringify(C);
    for (const leak of [
      "SD3",
      "SD4",
      "SH6",
      "SH8",
      "HZA",
      "SG1",
      "SC2",
      "D3_",
      "D4_",
      "operationId",
      "api-delpi",
      "supplies-api",
    ]) {
      expect(strings).not.toContain(leak);
    }
  });

  it("labels-chave permanecem em linguagem de negócio", () => {
    expect(C.classifications.reconciled).toBe("Conciliado");
    expect(C.executionStates.pending).toBe("Pendente");
    expect(C.exclusionReasons.not_raw_material_consumption).toContain(
      "matéria-prima",
    );
    expect(C.exclusionReasons.labor_not_material).toContain("Mão de obra");
  });
});

describe("consumption-audit formatting", () => {
  it("formata quantidades, datas e ausências em PT-BR", () => {
    expect(formatQuantity(80.75)).toContain("80,75");
    expect(formatQuantity(0)).toBe("0");
    expect(formatQuantity(null)).toBe("—");
    expect(formatQuantity(undefined)).toBe("—");
    expect(formatDatePtBr("2026-10-20")).toBe("20/10/2026");
    expect(formatDatePtBr("20261020")).toBe("20/10/2026");
    expect(formatDatePtBr("")).toBe("—");
    expect(formatDateTimePtBr("2026-10-29T05:13:23")).toBe("29/10/2026 05:13");
    expect(formatDateTimePtBr("2026-10-30T08:50")).toBe("30/10/2026 08:50");
  });
});

// ——— F1–F4 · busca, filtros e comparação (GLPI #1353 evolução) ———

import {
  buildSearchQuery,
  EMPTY_FILTERS,
  filtersAreEmpty,
  parseFiltersFromSearch,
} from "./query";
import {
  isConsumptionAuditComparison,
  isConsumptionAuditSearchPage,
} from "./api";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

describe("consumption-audit search filters (URL state)", () => {
  it("round-trip dos filtros pela query string", () => {
    const qs = buildSearchQuery("01", {
      dateType: "finished",
      periodStart: "2026-10-01",
      periodEnd: "2026-10-31",
      product: "CABO",
      status: "N",
      workCenter: "CT-23",
      operation: "01",
    });
    const parsed = parseFiltersFromSearch(qs);
    expect(parsed.unit).toBe("01");
    expect(parsed.filters).toEqual({
      dateType: "finished",
      periodStart: "2026-10-01",
      periodEnd: "2026-10-31",
      product: "CABO",
      status: "N",
      workCenter: "CT-23",
      operation: "01",
    });
  });

  it("date_types permanecem semanticamente distintos", () => {
    const qs = buildSearchQuery("01", {
      ...EMPTY_FILTERS,
      dateType: "appointment",
    });
    expect(qs).toContain("date_type=appointment");
    expect(qs).not.toContain("date_type=emission");
    const parsed = parseFiltersFromSearch(qs);
    expect(parsed.filters.dateType).toBe("appointment");
  });

  it("datas inválidas na URL são descartadas", () => {
    const parsed = parseFiltersFromSearch(
      "?unit=01&period_start=29/10/2026&period_end=2026-13-99",
    );
    expect(parsed.filters.periodStart).toBe("");
    expect(parsed.filters.periodEnd).toBe("");
  });

  it("filtros padrão não poluem a URL", () => {
    const qs = buildSearchQuery("02", EMPTY_FILTERS);
    expect(qs).toBe("?unit=02");
    expect(filtersAreEmpty(EMPTY_FILTERS)).toBe(true);
    expect(
      filtersAreEmpty({ ...EMPTY_FILTERS, product: "x" }),
    ).toBe(false);
  });
});

describe("consumption-audit search/comparison api guards", () => {
  it("aceita página de busca válida e rejeita shape errado", () => {
    const page = {
      items: [
        {
          production_order: "24884201006",
          order_number: "248842",
          order_item: "01",
          order_sequence: "006",
          product_code: "50226108",
          product_description: "CB",
          product_type: "PI",
          status: "N",
          planned_quantity: 0.125,
          produced_quantity: 0,
          unit_of_measure: "MI",
          warehouse: "01",
          emission_date: "2026-10-20",
          planned_start_date: "",
          due_date: "",
          finished_at: "",
        },
      ],
      page: 1,
      page_size: 10,
      total: 1,
      total_pages: 1,
    };
    expect(isConsumptionAuditSearchPage(page)).toBe(true);
    expect(isConsumptionAuditSearchPage({ items: "x" })).toBe(false);
    expect(isConsumptionAuditSearchPage({ items: [{ bad: 1 }] })).toBe(false);
  });

  it("aceita comparação válida e rejeita shape errado", () => {
    const comparison = {
      branch: "01",
      items: [
        {
          production_order: "24884201006",
          branch: "01",
          order: {},
          operations: [],
          totals_by_unit: [],
          quality: { status: "partial", warnings: [] },
          unmatched_movements_count: 0,
          related_orders_count: 0,
        },
      ],
      not_found: [],
      metadata: { generated_at_source: "api-delpi" },
    };
    expect(isConsumptionAuditComparison(comparison)).toBe(true);
    expect(isConsumptionAuditComparison({ items: [] })).toBe(false);
  });
});

describe("consumption-audit page structure (F2–F5)", () => {
  const pageSource = readFileSync(
    join(
      dirname(fileURLToPath(import.meta.url)),
      "ConsumptionAuditPage.tsx",
    ),
    "utf-8",
  );

  it("removeu o botão Consultar — nenhum submit dispara a pesquisa", () => {
    expect(pageSource).not.toContain('type="submit"');
    expect(pageSource).not.toContain("consultAction");
  });

  it("busca automática usa debounce e descarte de respostas antigas", () => {
    expect(pageSource).toContain("SEARCH_DEBOUNCE_MS = 350");
    expect(pageSource).toContain("AbortController");
    expect(pageSource).toContain("lastSearchKey");
  });

  it("combobox expõe semântica acessível e teclado", () => {
    expect(pageSource).toContain('role="combobox"');
    expect(pageSource).toContain("aria-activedescendant");
    expect(pageSource).toContain('"ArrowDown"');
    expect(pageSource).toContain('"Escape"');
  });

  it("seleção múltipla respeita o limite de comparação", () => {
    expect(pageSource).toContain("COMPARE_MAX = 10");
    expect(pageSource).toContain("selected.length >= COMPARE_MAX");
  });
});

// ——— UX/layout — período rápido e componentes do kit (feedback PO) ———

import {
  matchSuppliesQuickPeriod,
  resolveSuppliesQuickPeriod,
  SUPPLIES_QUICK_PERIOD_OPTIONS,
} from "../../app/periodPreset";

describe("supplies quick-period presets", () => {
  const now = new Date("2026-10-30T15:00:00Z"); // 12h em America/Sao_Paulo

  it("cobre as ações exigidas na ordem operacional", () => {
    expect(SUPPLIES_QUICK_PERIOD_OPTIONS.map((o) => o.value)).toEqual([
      "today",
      "yesterday",
      "last_7_days",
      "last_15_days",
      "last_30_days",
      "this_month",
      "last_month",
      "custom",
    ]);
    expect(SUPPLIES_QUICK_PERIOD_OPTIONS.map((o) => o.label)).toEqual([
      "Hoje",
      "Ontem",
      "Últimos 7 dias",
      "Últimos 15 dias",
      "Últimos 30 dias",
      "Este mês",
      "Mês passado",
      "Personalizado",
    ]);
  });

  it("resolve janelas móveis terminando em hoje", () => {
    expect(resolveSuppliesQuickPeriod("today", now)).toEqual({
      from: "2026-10-30",
      to: "2026-10-30",
    });
    expect(resolveSuppliesQuickPeriod("yesterday", now)).toEqual({
      from: "2026-10-29",
      to: "2026-10-29",
    });
    expect(resolveSuppliesQuickPeriod("last_7_days", now)).toEqual({
      from: "2026-10-24",
      to: "2026-10-30",
    });
    expect(resolveSuppliesQuickPeriod("last_15_days", now)).toEqual({
      from: "2026-10-16",
      to: "2026-10-30",
    });
    expect(resolveSuppliesQuickPeriod("last_30_days", now)).toEqual({
      from: "2026-10-01",
      to: "2026-10-30",
    });
    expect(resolveSuppliesQuickPeriod("this_month", now)).toEqual({
      from: "2026-10-01",
      to: "2026-10-30",
    });
    expect(resolveSuppliesQuickPeriod("last_month", now)).toEqual({
      from: "2026-09-01",
      to: "2026-09-30",
    });
    expect(resolveSuppliesQuickPeriod("custom", now)).toBeNull();
  });

  it("detecta o preset ativo e marca datas manuais como Personalizado", () => {
    expect(
      matchSuppliesQuickPeriod("2026-10-24", "2026-10-30", now),
    ).toBe("last_7_days");
    expect(
      matchSuppliesQuickPeriod("2026-10-29", "2026-10-29", now),
    ).toBe("yesterday");
    expect(
      matchSuppliesQuickPeriod("2026-10-01", "2026-10-15", now),
    ).toBe("custom");
    expect(matchSuppliesQuickPeriod("", "", now)).toBe("custom");
  });
});

describe("consumption-audit layout (plugin-ui composition)", () => {
  const pageSource = readFileSync(
    join(
      dirname(fileURLToPath(import.meta.url)),
      "ConsumptionAuditPage.tsx",
    ),
    "utf-8",
  );

  it("área de filtros usa os componentes canônicos do kit", () => {
    expect(pageSource).toContain("SuppliesFilterBarShell");
    expect(pageSource).toContain("SuppliesSegmentToggle");
    expect(pageSource).toContain("SuppliesDateField");
    expect(pageSource).toContain("SuppliesClearFiltersButton");
    expect(pageSource).toContain("FiltersRow");
  });

  it("período rápido preenche datas e oferece limpeza dedicada", () => {
    expect(pageSource).toContain("SUPPLIES_QUICK_PERIOD_OPTIONS");
    expect(pageSource).toContain("applyQuickPeriod");
    expect(pageSource).toContain("clearPeriod");
    expect(pageSource).toContain('idPrefix="ca-period-preset"');
  });

  it("busca/filtros fora do hero — cabeçalho não engole a área útil", () => {
    const heroIndex = pageSource.indexOf("<SuppliesPageHero");
    const formIndex = pageSource.indexOf("sp-consumption-audit__filters-form");
    expect(heroIndex).toBeGreaterThan(-1);
    expect(formIndex).toBeGreaterThan(heroIndex);
    // hero não carrega filhos — o formulário vem depois dele
    expect(pageSource.slice(heroIndex, formIndex)).not.toContain("combobox");
  });

  it("filtros avançados ficam em bloco colapsável separado", () => {
    expect(pageSource).toContain("sp-consumption-audit__advanced");
    expect(pageSource).toContain("advancedOpen");
  });
});

// ——— Listagem oficial plugin-ui + tokens de tema (revisão UI/UX PO) ———

describe("consumption-audit results table (plugin-ui migration)", () => {
  const pageSource = readFileSync(
    join(
      dirname(fileURLToPath(import.meta.url)),
      "ConsumptionAuditPage.tsx",
    ),
    "utf-8",
  );
  const cssSource = readFileSync(
    join(dirname(fileURLToPath(import.meta.url)), "../../index.css"),
    "utf-8",
  );

  it("usa o DataTable oficial para a listagem de OPs — sem tabela própria", () => {
    expect(pageSource).toContain("SuppliesDataTable");
    expect(pageSource).toContain(
      "onRowClick={(item) => selectOrder(item.production_order)}",
    );
    expect(pageSource).toContain("sp-list-table-region");
    expect(pageSource).not.toContain("sp-consumption-audit__result-row");
    // a região de resultados renderiza o kit, não um <table> manual
    const regionIndex = pageSource.indexOf("sp-list-table-region");
    const resultsBlock = pageSource.slice(
      regionIndex,
      pageSource.indexOf("<SuppliesCompactPagination", regionIndex),
    );
    expect(resultsBlock).toContain("SuppliesDataTable");
    expect(resultsBlock).not.toContain("<table");
    expect(cssSource).not.toContain("__result-row");
    expect(cssSource).not.toContain("__pagination");
  });

  it("seleção múltipla usa o checkbox oficial — nenhum input nativo cru", () => {
    expect(pageSource).toContain("SuppliesFilterCheckbox");
    expect(pageSource).not.toContain('type="checkbox"');
    expect(pageSource).toContain('key: "compare"');
    expect(pageSource).toContain("interactive: true");
    expect(pageSource).toContain("selected.length >= COMPARE_MAX");
  });

  it("linha selecionada usa o estado canônico is-selected do kit", () => {
    expect(pageSource).toContain('"is-selected"');
    expect(cssSource).toContain("tr.is-selected");
  });

  it("paginação usa o CompactPagination oficial", () => {
    expect(pageSource).toContain("SuppliesCompactPagination");
    expect(pageSource).toContain("onPageChange={setListPage}");
    expect(pageSource).not.toContain("sp-consumption-audit__pagination");
  });
});

describe("consumption-audit theme tokens", () => {
  const cssSource = readFileSync(
    join(dirname(fileURLToPath(import.meta.url)), "../../index.css"),
    "utf-8",
  );

  it("tokens semânticos de estado resolvidos nos dois temas", () => {
    // cada token deve aparecer ao menos 2x: bloco claro + bloco escuro
    for (const token of [
      "--sp-primary:",
      "--sp-primary-soft:",
      "--sp-accent-soft:",
      "--sp-surface-alt:",
    ]) {
      expect(cssSource.split(token).length - 1).toBeGreaterThanOrEqual(2);
    }
  });

  it("nenhum fallback claro fixo para tokens de estado (dark-safe)", () => {
    expect(cssSource).not.toContain("var(--sp-accent-soft, #");
    expect(cssSource).not.toContain("var(--sp-accent-soft, rgba");
    expect(cssSource).not.toContain("var(--sp-surface-alt, #");
    expect(cssSource).not.toContain("var(--sp-surface-alt, rgba");
    expect(cssSource).not.toContain("var(--sp-primary, #1f6feb)");
    expect(cssSource).not.toContain("#f5f7ff");
    expect(cssSource).not.toContain("#eef2ff");
  });
});
