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
  });

  it("gráficos só via ppCharts — sem imports diretos do pacote de charts do kit", () => {
    const chartGateways = new Set(["components/data/ppCharts.tsx"]);
    const bannedChartImports = [
      /\bAreaSeriesChart\b/,
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
    expect(readRelative("components/data/ppCharts.tsx")).toMatch(/AreaSeriesChart/);
    expect(readRelative("components/data/ppCharts.tsx")).toMatch(/ChartCard/);
    expect(readRelative("components/data/ppChartConfig.ts")).toMatch(/buildPpReadingsChartOptions/);
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
