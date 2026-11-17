/** Verificações estruturais da aba Roteiro — Routing Study Workspace V2.
 * A suíte do MFE é source-based; comportamento dinâmico é coberto pelos
 * unitários de `routingGrouping`/`routingStudyDraft` e pela E2E. */

import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "ProductRoutingTab.tsx"), "utf8");
const chart = readFileSync(join(here, "RoutingSeriesChart.tsx"), "utf8");
const chartExport = readFileSync(join(here, "routingChartExport.ts"), "utf8");
const posts = readFileSync(join(here, "PostConfigurator.tsx"), "utf8");
const draft = readFileSync(join(here, "routingStudyDraft.ts"), "utf8");
const hook = readFileSync(join(here, "useRoutingStudyDraft.ts"), "utf8");
const page = readFileSync(
  join(here, "../pages/ProductDetailPage.tsx"),
  "utf8",
);
const routes = readFileSync(
  join(here, "../productRoutes.ts"),
  "utf8",
);
const api = readFileSync(
  join(here, "../api/productApi.ts"),
  "utf8",
);
const css = readFileSync(join(here, "../../../index.css"), "utf8");
const all = `${src}\n${posts}\n${draft}\n${hook}`;

describe("aba Roteiro V2 — wiring", () => {
  it("registra a aba routing na navegação da ficha", () => {
    expect(routes).toContain('"routing"');
    expect(page).toContain('key: "routing"');
    expect(page).toContain("<ProductRoutingTab code={code} />");
  });

  it("consome somente os contratos BFF da Engineering API", () => {
    expect(api).toContain("/routing");
    expect(api).toContain("/line-balance");
    expect(src).not.toContain("api-delpi");
    expect(src).not.toContain("/apps/api-delpi");
    expect(src).not.toMatch(/sql|protheus/i);
  });
});

describe("aba Roteiro V2 — página única scrollável", () => {
  it("não possui navegação interna de três abas", () => {
    expect(src).not.toContain("EngineeringTabs");
    expect(src).not.toContain("SECTION_TABS");
    expect(src).not.toContain("RoutingSection");
    expect(src).not.toContain("routing-tab-");
    expect(src).not.toContain("routing-panel-");
  });

  it("renderiza todas as seções no scroll — ordem do contrato V2", () => {
    /* Ordem de render no JSX de ProductRoutingTab (não das definições). */
    const order = [
      '<EngineeringSectionCard\n              title="Roteiro de fabricação"',
      "<StageKpis",
      "<OperationsSection",
      "<StudySection",
      "<ResultsSection",
      "<VisualSection",
    ];
    let last = -1;
    for (const tag of order) {
      const idx = src.indexOf(tag);
      expect(idx, tag).toBeGreaterThan(last);
      last = idx;
    }
  });

  it("403, 404 e indisponibilidade têm estados distintos do vazio", () => {
    expect(src).toContain("isForbidden");
    expect(src).toContain("isNotFound");
    expect(src).toContain("autorização para consultar o roteiro");
    expect(src).toContain("não possui roteiro de fabricação");
  });

  it("paginação agregada respeita total e declara resposta parcial", () => {
    expect(api).toContain("ROUTING_MAX_PAGES");
    expect(api).toContain("truncated");
    expect(src).toContain("Resposta parcial");
  });
});

describe("aba Roteiro V2 — estudo e domínio", () => {
  it("dedup visual usa a identidade oficial da operação", () => {
    expect(src).toContain("groupRoutingRows");
  });

  it("calculadora chama o domínio EVA — sem algoritmo local", () => {
    expect(src).toContain("postProductLineBalance");
    expect(all).not.toContain("firstFitDecreasing");
    expect(all).not.toContain("Math.ceil");
  });

  it("cenários identificados A/B/C, limitados e comparáveis", () => {
    expect(draft).toContain("STUDY_MAX_SCENARIOS");
    expect(draft).toContain('["A", "B", "C", "D"]');
    expect(src).toContain("Novo cenário");
    expect(src).toContain("Cenário ${");
    expect(src).toContain("Resultados e cenários");
  });

  it("postos hipotéticos declaram limitação do motor — sem falsa viabilidade", () => {
    expect(src).toContain("DRAFT_LOCAL");
    expect(src).toContain("não valida alocação por posto");
    expect(src).toContain("não valida a distribuição manual");
  });

  it("postos usam multisseleção de operações oficiais — nunca livres", () => {
    expect(posts).toContain("EngineeringMultiSelectField");
    expect(posts).toContain("Somente operações oficiais");
    expect(posts).toContain("CT não equivale a posto físico");
  });

  it("ordenação de postos é por botões — acessível sem drag-and-drop", () => {
    expect(posts).toContain("para cima");
    expect(posts).toContain("para baixo");
    expect(posts).toContain("EngineeringIconButton");
  });
});

describe("aba Roteiro V2 — rascunho de sessão", () => {
  it("persiste em sessionStorage com chave por identidade e contexto", () => {
    expect(draft).toContain("sessionStorage");
    expect(hook).toContain("window.sessionStorage");
    expect(src).not.toContain("localStorage");
    expect(draft).toContain("buildStorageKey");
    expect(draft).toContain("context.productCode");
    expect(draft).toContain("context.branch");
    expect(draft).toContain("context.stageKey");
  });

  it("chave usa sub do JWT — nunca token, email ou segredo", () => {
    expect(src).toContain("getSubjectFromAccessToken");
    expect(src).toContain("getCurrentAccessToken");
    expect(draft).toContain("anonymous");
    expect(all).not.toMatch(/storage\.setItem\([^)]*token/i);
    expect(all).not.toContain("localStorage");
  });

  it("resultados nunca são persistidos — CALCULATED é transitório", () => {
    expect(hook).toContain("computed`) são transitórios");
    /* saveDraft serializa só o RoutingStudyDraft (inputs+postos+modo)
     * — `computed` vive em estado separado e nunca entra no payload. */
    expect(hook).toMatch(/saveDraft\(store, storageKey, \{\s*\.\.\.draft,[\s\S]*?savedAt/);
    expect(src).toContain("STALE");
    expect(draft).toContain("inputsFingerprint");
  });

  it("limpar exige confirmação e remove só a chave do contexto", () => {
    expect(src).toContain("Limpar estudo");
    expect(src).toContain("EngineeringConfirmDialog");
    expect(src).toContain("Não altera roteiro");
    expect(hook).toContain("clearStudy");
    expect(draft).toContain("removeDraft");
  });

  it("estados de persistência são honestos", () => {
    expect(src).toContain("Salvo nesta aba");
    expect(src).toContain("Não foi possível salvar");
    expect(src).toContain("Rascunho recuperado nesta aba");
    expect(draft).toContain("QuotaExceededError");
  });
});

describe("aba Roteiro V2 — Plugin UI como fonte de apresentação", () => {
  it("não reconstrói primitivos do kit — sem <table>/<select>/<button> manual", () => {
    expect(all).not.toContain("<table");
    expect(all).not.toContain("<select");
    expect(all).not.toContain("<button");
    expect(src).not.toContain("__expander");
  });

  it("usa os componentes canônicos do kit para cada superfície", () => {
    for (const component of [
      "EngineeringSectionCard",
      "EngineeringKpiCard",
      "EngineeringDetailCard",
      "EngineeringFilterSelect",
      "EngineeringFormActions",
      "EngineeringEmptyState",
      "EngineeringStateBanner",
      "EngineeringStatusBadge",
      "EngineeringChartCard",
      "EngineeringLoadingActivityCard",
      "EngineeringInteractiveDataCard",
      "EngineeringSegmentToggle",
      "EngineeringScopeChipBar",
    ]) {
      expect(src, component).toContain(component);
    }
    for (const component of [
      "EngineeringMultiSelectField",
      "EngineeringIconButton",
      "EngineeringTextField",
      "EngineeringTextAreaField",
    ]) {
      expect(posts, component).toContain(component);
    }
    expect(src).toContain("DataTable");
    expect(src).toContain("EngineeringConfirmDialog");
  });

  it("gráficos usam a composição corporativa do kit — sem renderer paralelo", () => {
    expect(src).toContain("RoutingSeriesChart");
    expect(src).not.toContain("ConfigurableSeriesChart");
    expect(src).not.toContain("recharts");
    expect(chart).toContain("ChartViewShell");
    expect(chart).toContain("MultiTypeSeriesChart");
    expect(chart).toContain("ChartTypeSegmentToggle");
    expect(chart).toContain("ChartOverlayOptionsPopover");
    expect(chart).toContain("ChartSeriesColorsPopover");
    expect(chart).toContain("usePersistedChartPreferences");
    expect(chart).toContain("TabularExportButtons");
    expect(chart).toContain("runTabularExport");
    expect(chart).not.toContain('from "recharts"');
    expect(chart).not.toContain("ConfigurableSeriesChart");
  });

  it("preferências de gráfico usam namespace próprio da Engenharia", () => {
    expect(src).toContain("engineering:routing:");
    expect(src).not.toContain("commercial:");
    expect(chart).not.toContain("localStorage");
  });

  it("exportação CSV/Excel/PDF via API compartilhada com contexto", () => {
    expect(src).toContain("buildOpsTimeExportPayload");
    expect(src).toContain("buildOpsVsTaktExportPayload");
    expect(src).toContain("buildSimDistributionExportPayload");
    expect(chartExport).toContain("OBSERVED");
    expect(chartExport).toContain("CALCULATED");
    expect(chartExport).toContain("SIMULATION");
    expect(chartExport).toContain("TableExportPayload");
  });

  it("marca proveniência e simulação visualmente", () => {
    expect(all).toContain("SIMULATION");
    expect(all).toContain("OBSERVED");
    expect(all).toContain("PROVIDED");
    expect(all).toContain("CALCULATED");
  });

  it("operações são cards expansíveis — DataTable só onde é tabular", () => {
    expect(src).not.toContain("OPERATION_COLUMNS");
    expect(src).toContain("SCENARIO_COLUMNS");
    expect(src).toContain("ariaExpanded");
    expect(src).not.toContain("expandedRowKey");
  });

  it("CSS local é só composição — sem primitivos visuais duplicados", () => {
    expect(css).not.toContain(".engineering-routing__table");
    expect(css).not.toContain(".engineering-routing__expander");
    expect(css).not.toContain(".engineering-routing__filters");
    expect(css).not.toContain(".engineering-routing__calc-form");
  });
});
