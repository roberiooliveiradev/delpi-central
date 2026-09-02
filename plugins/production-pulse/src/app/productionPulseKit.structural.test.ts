import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

function listSourceFiles(dir: string): string[] {
  const entries = readdirSync(dir);
  const files: string[] = [];
  for (const entry of entries) {
    const path = join(dir, entry);
    const stat = statSync(path);
    if (stat.isDirectory()) {
      files.push(...listSourceFiles(path));
      continue;
    }
    if (/\.(tsx|ts)$/.test(entry) && !entry.endsWith(".test.ts") && !entry.endsWith(".test.tsx")) {
      files.push(path);
    }
  }
  return files;
}

function readRelative(pathFromSrc: string): string {
  return readFileSync(join(root, pathFromSrc), "utf8");
}

describe("production-pulse kit contracts", () => {
  const sources = listSourceFiles(root).map((abs) => ({
    rel: relative(root, abs),
    source: readFileSync(abs, "utf8"),
  }));

  it("usa PpDataTable canônico — nunca DataTable cru do kit", () => {
    for (const { rel, source } of sources) {
      if (rel === "components/data/dataTableUi.tsx") continue;
      expect(source, rel).not.toMatch(/\bDataTable\b.*@delpi\/plugin-ui/);
      expect(source, rel).not.toMatch(/dataTableBemClasses\s*\(/);
    }
    expect(readRelative("components/DeviceTable.tsx")).toMatch(/PpDataTable/);
    expect(readRelative("components/DeviceCard.tsx")).toMatch(/PpDataRecordCard/);
    expect(readRelative("components/DeviceCard.tsx")).not.toMatch(/pp-device-card__ghost/);
    expect(readRelative("components/data/dataTableUi.tsx")).toMatch(/labels={LABELS}/);
    expect(readRelative("components/data/dataTableUi.tsx")).toMatch(/loadingMessage:/);
  });

  it("usa FiltersRow canônico — sem flex externo que encolhe o shell", () => {
    for (const { rel, source } of sources) {
      expect(source, rel).not.toMatch(/pp-filters-wrap/);
      expect(source, rel).not.toMatch(/createFilterBarShell/);
    }
    const filtersBar = readRelative("components/DeviceFiltersBar.tsx");
    expect(filtersBar).toMatch(/PpFiltersRow/);
    expect(filtersBar).toMatch(/PpFilterToolbarRowClasses/);
    expect(filtersBar).not.toMatch(/pp-filters-wrap/);
    expect(filtersBar).not.toMatch(/PpFilterBarShell/);
    expect(readRelative("components/data/filtersUi.tsx")).toMatch(/PpFiltersRow/);
  });

  it("hub operador usa busca automática do kit — sem botão Buscar", () => {
    const hub = readRelative("pages/operator/OperatorPlacementHub.tsx");
    expect(hub).toMatch(/PpCatalogSearchBar/);
    expect(hub).not.toMatch(/Buscar/);
    expect(hub).not.toMatch(/pp-operator-hub__search-actions/);
  });

  it("painel admin tem atalho simétrico para modo operador", () => {
    const panel = readRelative("pages/PanelPage.tsx");
    expect(panel).toMatch(/productionPulseOperatorPath/);
    expect(panel).toMatch(/Modo operador/);
    expect(panel).toMatch(/canOperator/);
    expect(panel).toMatch(/pp-panel-operator-link/);
  });

  it("botões do hero usam classe de domínio pp-hero-brand-btn com tokens de marca", () => {
    const css = readRelative("index.css");
    const detail = readRelative("pages/DeviceDetailPage.tsx");
    expect(css).toMatch(
      /\.pp-hero-brand-btn[\s\S]*--pp-hero-brand-btn-border[\s\S]*--pp-hero-brand-fg[\s\S]*--pp-hero-brand-btn-bg/,
    );
    expect(detail).toMatch(/pp-hero-brand-btn/);
    expect(css).not.toMatch(/\.delpi-ui-/);
  });

  it("FilterInputField declara type explícito no painel", () => {
    const filtersBar = readRelative("components/DeviceFiltersBar.tsx");
    expect(filtersBar).toMatch(/type="search"/);
    expect(filtersBar).not.toMatch(/onChange=\{\(event\)/);
  });

  it("StateBox usa action singular do kit — não actions", () => {
    for (const { rel, source } of sources) {
      if (!source.includes("PpStateBox")) continue;
      const withoutPageHero = source.replace(/<PpPageHero[\s\S]*?\/>/g, "");
      expect(withoutPageHero, rel).not.toMatch(/<PpStateBox[\s\S]*?\bactions=/);
    }
  });

  it("modais de aviso usam PpHostContainedDialog — nunca ModalShell body-fixed", () => {
    const modalFiles = [
      "components/modals/TestConnectionModal.tsx",
      "components/modals/ResetCounterModal.tsx",
      "components/modals/OperatorClearCounterModal.tsx",
      "components/modals/CommandJsonModal.tsx",
    ];
    for (const rel of modalFiles) {
      const source = readRelative(rel);
      expect(source, rel).not.toMatch(/\bModalShell\b/);
      expect(source, rel).toMatch(/PpHostContainedDialog/);
    }
    const uiKit = readRelative("app/productionPulseUi.tsx");
    expect(uiKit).toMatch(/createHostContainedModalShell/);
    expect(uiKit).toMatch(/dashboard-production-pulse/);
    expect(uiKit).toMatch(/containedLayout:\s*"dialog"/);
  });

  it("index.css não sobrescreve classes .delpi-ui-* do kit", () => {
    const css = readRelative("index.css");
    expect(css).not.toMatch(/\.delpi-ui-/);
  });

  it("inputs e selects só via ppFormFields ou filtersUi — sem HTML cru", () => {
    const kitGateways = new Set([
      "components/data/ppFormFields.tsx",
      "components/data/filtersUi.tsx",
    ]);
    const bannedKitImports = [
      /\bNativeTextControl\b/,
      /\bNativeSwitchControl\b/,
      /\bNativeTextField\b/,
      /\bNativeSelectField\b/,
      /\bNativeSelectControl\b/,
      /\bNativeTextAreaField\b/,
      /\bcreateDashboardNativeFormFields\b/,
      /\bFormSelectControl\b/,
      /\bSelectControl\b/,
      /\bFilterInputField as PluginFilterInputField\b/,
      /\bcreateDashboardFiltersKit\b/,
    ];

    for (const { rel, source } of sources) {
      if (kitGateways.has(rel)) continue;
      expect(source, rel).not.toMatch(/<input[\s/>]/);
      expect(source, rel).not.toMatch(/<select[\s/>]/);
      expect(source, rel).not.toMatch(/<textarea[\s/>]/);
      for (const pattern of bannedKitImports) {
        expect(source, rel).not.toMatch(pattern);
      }
    }

    expect(readRelative("components/DeviceForm.tsx")).toMatch(/PpNative(TextField|SelectField|InlineTextField|SwitchField)/);
    expect(readRelative("components/DeviceBindingSection.tsx")).toMatch(/PpNative(TextField|SelectField|TextAreaField)/);
    expect(readRelative("components/DeviceFiltersBar.tsx")).toMatch(/PpFilter(InputField|SelectField)/);
    expect(readRelative("components/detail/DeviceHistoryTab.tsx")).toMatch(/PpFilterInputField/);
    expect(readRelative("app/productionPulseUi.tsx")).toMatch(/from "\.\.\/components\/data\/ppFormFields"/);
    expect(readRelative("app/productionPulseUi.tsx")).toMatch(/from "\.\.\/components\/data\/dataTableUi"/);
    expect(readRelative("app/productionPulseUi.tsx")).toMatch(/from "\.\.\/components\/data\/filtersUi"/);
  });

  it("consumidores importam data gateways só via productionPulseUi", () => {
    const uiHub = "app/productionPulseUi.tsx";
    const dataGateways = new Set([
      "components/data/dataTableUi.tsx",
      "components/data/filtersUi.tsx",
      "components/data/ppFormFields.tsx",
      "components/data/ppCharts.tsx",
      uiHub,
    ]);
    const bannedDirectImport =
      /from ["']\.\.?\/(?:components\/)?data\/(?:dataTableUi|filtersUi|ppFormFields|ppCharts)["']/;

    for (const { rel, source } of sources) {
      if (dataGateways.has(rel)) continue;
      expect(source, rel).not.toMatch(bannedDirectImport);
    }

    expect(readRelative("components/DeviceForm.tsx")).toMatch(/from "\.\.\/app\/productionPulseUi"/);
    expect(readRelative("components/DeviceTable.tsx")).toMatch(/from "\.\.\/app\/productionPulseUi"/);
    expect(readRelative("components/DeviceFiltersBar.tsx")).toMatch(/from "\.\.\/app\/productionPulseUi"/);
  });

  it("painel usa kit canônico — segment toggle de filial e paginação compacta", () => {
    const panel = readRelative("pages/PanelPage.tsx");
    expect(panel).toMatch(/PpSegmentToggle/);
    expect(panel).toMatch(/PpPagination/);
    expect(panel).not.toMatch(/FilialSwitcher/);
    expect(panel).not.toMatch(/pp-compact-pagination/);
    expect(sources.some(({ rel }) => rel === "components/FilialSwitcher.tsx")).toBe(false);
  });

  it("replacePanelFilters só roda no path do painel", () => {
    const hook = readRelative("hooks/usePanelFilters.ts");
    expect(hook).toMatch(/isPanelPath/);
    expect(hook).toMatch(/query\.has\("view"\)/);
  });

  it("operador contador e gauge usam shell responsivo WF-PP-OP-08", () => {
    const counter = readRelative("components/operator/CounterPadSurface.tsx");
    const gauge = readRelative("components/operator/GaugeReadoutSurface.tsx");
    const css = readRelative("index.css");
    expect(counter).toMatch(/pp-counter-pad__workspace/);
    expect(counter).toMatch(/pp-counter-pad__pad-host/);
    expect(counter).toMatch(/pp-counter-pad__controls/);
    expect(counter).toMatch(/pp-counter-pad__btn--increment/);
    expect(counter).not.toMatch(/isMobileViewport/);
    expect(counter).not.toMatch(/pp-counter-pad__pad--stack/);
    expect(gauge).toMatch(/pp-gauge-readout__workspace/);
    expect(css).toMatch(/--pp-operator-content-max/);
    expect(css).toMatch(/--pp-operator-counter-value/);
    expect(css).toMatch(/--pp-operator-content-max/);
    expect(css).toMatch(/\.pp-operator-surface[\s\S]*max-width: none/);
    expect(css).toMatch(/data-pp-viewport-short="true"/);
    expect(css).toMatch(/dashboard-page--fill/);
    expect(css).toMatch(/\.pp-counter-pad__workspace[\s\S]*flex: 1 1 auto/);
    expect(css).toMatch(/\.pp-counter-pad__stage[\s\S]*flex: 1 1 auto/);
    expect(css).not.toMatch(/grid-template-rows: auto auto auto minmax\(min-content, 1fr\) auto/);
    expect(css).not.toMatch(/\.pp-counter-pad__workspace[\s\S]*display: contents/);
    expect(css).toMatch(/container-type: inline-size/);
    expect(css).toMatch(/container-name: pp-counter-pad/);
    expect(css).toMatch(/pp-counter-pad__pad \.pp-counter-pad__btn \+ \.pp-counter-pad__btn[\s\S]*margin-inline-start: 0/);
    expect(css).toMatch(/@container pp-counter-pad \(min-width: 26rem\)/);
    expect(css).toMatch(/min-height: 0/);
    expect(css).toMatch(/min-width: 901px\)[\s\S]*pp-gauge-readout__grid/);
    expect(css).toMatch(/--pp-operator-card-min-height/);
    expect(css).toMatch(/dashboard-production-pulse--operator \.pp-device-status/);
  });

  it("modo operador device usa dashboard-page--fill (preenche área do portal)", () => {
    const app = readRelative("App.tsx");
    expect(app).toMatch(/dashboard-page--fill/);
    expect(app).toMatch(/isOperatorFillRoute/);
    expect(app).toMatch(/operatorDevice/);
  });

  it("trocar posto no operador volta ao hub — evita auto-redirect do picker", () => {
    const counter = readRelative("components/operator/CounterPadSurface.tsx");
    const gauge = readRelative("components/operator/GaugeReadoutSurface.tsx");
    const nav = readRelative("utils/operatorNavigation.ts");
    expect(counter).toMatch(/navigateOperatorPlacementHub/);
    expect(counter).not.toMatch(/productionPulseOperatorPlacementPath/);
    expect(gauge).toMatch(/navigateOperatorPlacementHub/);
    expect(gauge).not.toMatch(/productionPulseOperatorPlacementPath/);
    expect(nav).toMatch(/productionPulseOperatorPath/);
  });

  it("router hook escuta popstate e lê pathname do browser (não só do host)", () => {
    const hook = readRelative("hooks/useProductionPulseRouterPath.ts");
    expect(hook).toMatch(/addEventListener\("popstate"/);
    expect(hook).toMatch(/routeEpoch/);
    expect(hook).toMatch(/readPathname\(\)/);
    expect(hook).toMatch(/readSearch\(\)/);
    expect(hook).not.toMatch(/setPathname\(pathnameFromHost\)/);
  });

  it("textos de ação e modal não ficam hardcoded fora de helpTooltips", () => {
    const contentPaths = new Set(["content/helpTooltips.ts", "content/deviceApiMessages.ts"]);
    for (const { rel, source } of sources) {
      if (contentPaths.has(rel) || !rel.endsWith(".tsx")) continue;
      expect(source, rel).not.toMatch(/>\s*Poll\s*</);
      expect(source, rel).not.toMatch(/"Poll agora"/);
      expect(source, rel).not.toMatch(/"Testar conexão"/);
    }
    expect(readRelative("components/modals/TestConnectionModal.tsx")).toMatch(/PP_HELP\.modals/);
  });

  it("gráficos só via ppCharts — sem imports diretos do pacote de charts do kit", () => {
    const chartGateways = new Set(["components/data/ppCharts.tsx"]);
    const bannedChartImports = [
      /\bAreaSeriesChart\b/,
      /\bComparativeAreaChart\b/,
      /\bLineSeriesChart\b/,
      /\bBarSeriesChart\b/,
      /\bConfigurableSeriesChart\b/,
      /\bSeriesChartPrimitive\b/,
      /\bChartCard\b/,
      /\bchartCardBemClasses\b/,
    ];

    for (const { rel, source } of sources) {
      if (chartGateways.has(rel)) continue;
      for (const pattern of bannedChartImports) {
        expect(source, rel).not.toMatch(pattern);
      }
    }

    expect(readRelative("components/detail/DeviceOverviewTab.tsx")).toMatch(/PpReadingsAreaChart/);
    expect(readRelative("components/detail/DeviceHistoryTab.tsx")).toMatch(/PpReadingsAreaChart/);
    expect(readRelative("components/detail/DeviceHistoryTab.tsx")).toMatch(/PpChartCard/);
    expect(readRelative("app/productionPulseUi.tsx")).toMatch(/from "\.\.\/components\/data\/ppCharts"/);
    expect(readRelative("components/data/ppCharts.tsx")).toMatch(/ComparativeAreaChart/);
    expect(readRelative("components/data/ppCharts.tsx")).toMatch(/useDelpiDarkMode/);
    expect(readRelative("components/data/ppCharts.tsx")).toMatch(/ChartCard/);
    expect(readRelative("components/data/ppChartConfig.ts")).toMatch(/buildPpReadingsChartSeries/);
    expect(readRelative("components/data/ppFormFields.tsx")).toMatch(/searchable = true/);
    expect(readRelative("components/data/filtersUi.tsx")).toMatch(/searchable = true/);
  });

  it("hero usa paleta brand do operador em todo o plugin", () => {
    const css = readRelative("index.css");
    expect(css).toMatch(/\.dashboard-production-pulse \.pp-page-hero \{/);
    expect(css).toMatch(/--pp-hero-brand-fg:/);
    expect(readRelative("components/operator/OperatorBrandBar.tsx")).toMatch(/PpPageHero/);
  });

  it("páginas profundas usam PagePath — não BackLink", () => {
    const detail = readRelative("pages/DeviceDetailPage.tsx");
    const formPage = readRelative("pages/DeviceFormPage.tsx");
    const uiKit = readRelative("app/productionPulseUi.tsx");
    expect(detail).toMatch(/ProductionPulsePagePath/);
    expect(detail).not.toMatch(/PpBackLink/);
    expect(formPage).toMatch(/ProductionPulsePagePath/);
    expect(formPage).not.toMatch(/PpBackLink/);
    expect(uiKit).toMatch(/createDashboardPagePath/);
    expect(uiKit).not.toMatch(/PpBackLink/);
    expect(readRelative("components/ProductionPulsePagePath.tsx")).toMatch(/PpPagePath/);
  });

  it("cadastro usa grade responsiva e footer compacto", () => {
    const formPage = readRelative("pages/DeviceFormPage.tsx");
    const deviceForm = readRelative("components/DeviceForm.tsx");
    const bindingSection = readRelative("components/DeviceBindingSection.tsx");
    expect(formPage).toMatch(/isCompactViewport/);
    expect(formPage).toMatch(/pp-form-footer--sticky/);
    expect(deviceForm).toMatch(/pp-form-grid--pair/);
    expect(deviceForm).toMatch(/PpNativeTextField/);
    expect(deviceForm).not.toMatch(/<input[\s>]/);
    expect(bindingSection).toMatch(/PpNativeTextField/);
    expect(bindingSection).not.toMatch(/<datalist/);
    expect(readRelative("App.tsx")).toMatch(/data-pp-viewport/);
    expect(readRelative("App.tsx")).toMatch(/data-pp-viewport-short/);
    expect(readRelative("hooks/useShortViewport.ts")).toMatch(/isShortViewportHeight/);
    expect(readRelative("components/data/ppFormFields.tsx")).toMatch(/createDashboardNativeFormFields/);
    expect(readRelative("components/data/ppFormFields.tsx")).toMatch(/FormSelectControl/);
    expect(readRelative("components/data/ppFormFields.tsx")).not.toMatch(/<select[\s/>]/);
    const css = readRelative("index.css");
    expect(css).toMatch(/--pp-form-max-width/);
    expect(css).toMatch(/pp-form-grid--pair/);
    expect(css).toMatch(/pp-page-stack\.pp-form-page/);
    expect(css).toMatch(/display:\s*contents/);
  });
});
