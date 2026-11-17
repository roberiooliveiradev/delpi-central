/** Verificações estruturais da aba Roteiro (Doc 126) — a suíte do MFE
 * é source-based; comportamento dinâmico é coberto pelos unitários de
 * `routingGrouping` e pela validação visual/E2E. */

import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "ProductRoutingTab.tsx"), "utf8");
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

describe("aba Roteiro — wiring", () => {
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

describe("aba Roteiro — seções e estados honestos", () => {
  it("implementa as três seções do wireframe", () => {
    for (const id of ["operations", "balance", "visual"]) {
      expect(src).toContain(`"${id}"`);
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

  it("dedup visual usa a identidade oficial da operação", () => {
    expect(src).toContain("groupRoutingRows");
  });

  it("calculadora chama o domínio EVA — sem algoritmo local", () => {
    expect(src).toContain("postProductLineBalance");
    expect(src).not.toContain("firstFitDecreasing");
    expect(src).not.toContain("Math.ceil");
  });

  it("cenários são atribuíveis e limitados, sem persistência", () => {
    expect(src).toContain("MAX_SCENARIOS");
    expect(src).toContain("Comparação de cenários");
    expect(src).not.toContain("localStorage");
  });

  it("gráficos usam o componente oficial do kit", () => {
    expect(src).toContain("ConfigurableSeriesChart");
    expect(src).toContain("EngineeringChartCard");
  });

  it("marca proveniência e simulação visualmente", () => {
    expect(src).toContain("SIMULATION");
    expect(src).toContain("OBSERVED");
    expect(src).toContain("PROVIDED");
    expect(src).toContain("CALCULATED");
  });

  it("controles acessíveis — tabs do kit e cards expansíveis do kit", () => {
    expect(src).toContain('mode="tabs"');
    expect(src).toContain("EngineeringInteractiveDataCard");
    expect(src).toContain("onActivate");
    expect(src).not.toContain("expandedRowKey");
  });

  it("operações são cards expansíveis — DataTable só onde é tabular", () => {
    expect(src).not.toContain("OPERATION_COLUMNS");
    expect(src).not.toContain("COMPONENT_COLUMNS");
    // A DataTable permanece apenas na comparação de cenários (dados
    // verdadeiramente tabulares), nunca como visualização primária.
    expect(src).toContain("SCENARIO_COLUMNS");
  });
});

describe("aba Roteiro — Plugin UI como fonte de apresentação", () => {
  it("não reconstrói primitivos do kit — sem <table>/<select>/<button> manual", () => {
    expect(src).not.toContain("<table");
    expect(src).not.toContain("<select");
    expect(src).not.toContain("<button");
    expect(src).not.toContain("__expander");
    expect(src).not.toContain("__components-table");
  });

  it("usa os componentes canônicos do kit para cada superfície", () => {
    for (const component of [
      "EngineeringSectionCard",
      "EngineeringKpiCard",
      "EngineeringDetailCard",
      "EngineeringFilterSelect",
      "EngineeringFormActions",
      "EngineeringTabs",
      "EngineeringEmptyState",
      "EngineeringStateBanner",
      "EngineeringStatusBadge",
      "EngineeringChartCard",
      "EngineeringLoadingActivityCard",
      "EngineeringInteractiveDataCard",
    ]) {
      expect(src).toContain(component);
    }
    expect(src).toContain("DataTable");
  });

  it("gráficos herdam o tema do portal e formatam escala legível", () => {
    expect(src).toContain("usePortalTheme");
    expect(src).toContain("resolveChartTimeUnit");
    expect(src).toContain("decimalPlaces");
  });

  it("CSS local é só composição — sem primitivos visuais duplicados", () => {
    expect(css).not.toContain(".engineering-routing__table");
    expect(css).not.toContain(".engineering-routing__expander");
    expect(css).not.toContain(".engineering-routing__components-table");
    expect(css).not.toContain(".engineering-routing__filters");
    expect(css).not.toContain(".engineering-routing__calc-form");
  });
});
