import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { canAccessView } from "../../app/routeAccess";
import { buildPluginPath, resolvePluginRoute } from "../../app/pluginRoutes";
import { HUB_SECTIONS } from "../../content/pluginRouteCatalog";
import {
  readMarketIntelligenceFromUrl,
  writeMarketIntelligenceToUrl,
} from "./marketIntelligenceUrl";

type WindowStub = {
  location: { search: string; pathname: string; hash: string };
  history: { replaceState: (state: unknown, title: string, url: string) => void };
};

function withWindow(search: string, run: (stub: WindowStub) => void) {
  const stub: WindowStub = {
    location: { search, pathname: "/apps/supplies/market-intelligence", hash: "" },
    history: { replaceState: () => {} },
  };
  const previous = (globalThis as { window?: unknown }).window;
  (globalThis as { window?: unknown }).window = stub;
  try {
    run(stub);
  } finally {
    (globalThis as { window?: unknown }).window = previous;
  }
}

const here = dirname(fileURLToPath(import.meta.url));

const BASE_STATE = {
  view: "indicators" as const,
  mode: "chart" as const,
  granularity: "month" as const,
  fxKind: "ptax_closing_sell" as const,
  metals: [] as string[],
  indicator: "ipp" as const,
  ncm: "",
  comexProducts: [] as string[],
  comexDirectNcms: [] as string[],
  ippSeries: "",
  from: "2025-01-01",
  to: "2025-12-31",
};

describe("market intelligence page (PROC-0076 R4)", () => {
  it("resolves /market-intelligence and requires supplies.access only", () => {
    expect(
      resolvePluginRoute("/apps/supplies/market-intelligence").view,
    ).toBe("market_intelligence");
    expect(buildPluginPath("market_intelligence")).toBe(
      "/apps/supplies/market-intelligence",
    );
    expect(
      canAccessView("market_intelligence", { access: false, manage: false }),
    ).toBe(false);
    expect(
      canAccessView("market_intelligence", { access: true, manage: false }),
    ).toBe(true);
  });

  it("is published in the hub analytics section after page release", () => {
    const every = HUB_SECTIONS.flatMap((section) => section.routes);
    const route = every.find((r) => r.viewId === "market_intelligence");
    expect(route).toBeDefined();
    expect(route?.requiredCap).toBe("analytics");
  });

  it("persists the R4 contract in the URL (view/metals/mode/filters)", () => {
    const url = readFileSync(join(here, "marketIntelligenceUrl.ts"), "utf8");
    expect(url).toContain("view");
    expect(url).toContain("metals");
    expect(url).toContain("mode");
    expect(url).toContain("granularity");
    expect(url).toContain("indicator");
    expect(url).toContain("fx_kind");
    expect(url).toContain("ipp_series");
    expect(url).toContain("ncm");
    expect(url).toContain('"week"');
    expect(url).toContain('"compare"');
    expect(url).toContain("replaceState");
  });

  it("maps legacy R3 links to the R4 perspectives", () => {
    withWindow("?view=ipp&ipp_series=ipp-metalurgia-index", () => {
      const state = readMarketIntelligenceFromUrl();
      expect(state.view).toBe("indicators");
      expect(state.indicator).toBe("ipp");
      expect(state.ippSeries).toBe("ipp-metalurgia-index");
    });
    withWindow("?view=comex&ncm=74040010", () => {
      const state = readMarketIntelligenceFromUrl();
      expect(state.view).toBe("indicators");
      expect(state.indicator).toBe("comex");
      expect(state.ncm).toBe("74040010");
    });
  });

  it("parses a multi-NCM CSV and the comex product selection (S4)", () => {
    withWindow(
      "?view=indicators&indicator=comex&ncm=74040010,85444900&products=MP0001,MP0002",
      () => {
        const state = readMarketIntelligenceFromUrl();
        expect(state.ncm).toBe("74040010,85444900");
        expect(state.comexProducts).toEqual(["MP0001", "MP0002"]);
      },
    );
  });

  it("parses direct-entry NCMs and drops malformed codes (S6)", () => {
    withWindow(
      "?view=indicators&indicator=comex&direct_ncm=85444200,8544.49.00,abc,74040010",
      () => {
        const state = readMarketIntelligenceFromUrl();
        // Only exact 8-digit codes survive — "8544.49.00" keeps its
        // punctuation and is dropped by the URL contract.
        expect(state.comexDirectNcms).toEqual([
          "85444200",
          "74040010",
        ]);
      },
    );
  });

  it("drops malformed NCM codes and product codes from the URL", () => {
    withWindow("?ncm=74040010,abc,123&products=OK-1,<script>", () => {
      const state = readMarketIntelligenceFromUrl();
      expect(state.ncm).toBe("74040010");
      expect(state.comexProducts).toEqual(["OK-1"]);
    });
  });

  it("round-trips the comex selection to the URL", () => {
    let written = "";
    withWindow("", (stub) => {
      stub.history.replaceState = (_s, _t, url) => {
        written = url;
      };
      writeMarketIntelligenceToUrl({
        ...BASE_STATE,
        indicator: "comex",
        ncm: "74040010,85444900",
        comexProducts: ["MP0001"],
      });
    });
    expect(written).toContain("indicator=comex");
    expect(written).toContain("ncm=74040010%2C85444900");
    expect(written).toContain("products=MP0001");
  });

  it("round-trips the direct NCM selection to the URL (S6)", () => {
    let written = "";
    withWindow("", (stub) => {
      stub.history.replaceState = (_s, _t, url) => {
        written = url;
      };
      writeMarketIntelligenceToUrl({
        ...BASE_STATE,
        indicator: "comex",
        comexDirectNcms: ["85444200", "74040010"],
      });
    });
    expect(written).toContain("direct_ncm=85444200%2C74040010");
  });

  it("maps a legacy R2 link (instrument=usd-brl) to the fx view", () => {
    withWindow("?instrument=usd-brl&currency=BRL", () => {
      const state = readMarketIntelligenceFromUrl();
      expect(state.view).toBe("fx");
    });
  });

  it("maps a legacy R2 metal link to the metals view with selection", () => {
    withWindow("?instrument=copper", () => {
      const state = readMarketIntelligenceFromUrl();
      expect(state.view).toBe("metals");
      expect(state.metals).toEqual(["copper"]);
    });
  });

  it("uses kit-first components and scoped sp classes", () => {
    const page = readFileSync(
      join(here, "MarketIntelligencePage.tsx"),
      "utf8",
    );
    const panel = readFileSync(
      join(here, "MarketIntelligencePanel.tsx"),
      "utf8",
    );
    const metalsPanel = readFileSync(
      join(here, "MarketMetalsPanel.tsx"),
      "utf8",
    );
    // Page composes through suppliesUi kit bindings — no direct kit import.
    expect(page).not.toMatch(/from ["']@delpi\/plugin-ui/);
    expect(page).toContain("sp-page-stack");
    expect(page).toContain("SuppliesPageHero");
    expect(page).toContain("SuppliesSelectField");
    expect(page).toContain("SuppliesSegmentToggle");
    expect(page).toContain("SuppliesDateField");
    expect(page).toContain("sp-market-instruments-grid");
    // One analysis panel per perspective branch.
    expect(panel).toContain("MultiTypeSeriesChart");
    expect(panel).toContain("ChartViewShell");
    expect(panel).toContain("SuppliesDataTable");
    expect(panel).toContain("SuppliesKpiCard");
    expect(panel).toContain('prefix="sp"');
    expect(metalsPanel).toContain("MultiTypeSeriesChart");
    expect(metalsPanel).toContain("SuppliesDataTable");
    // No business math in the MFE — BFF owns metrics.
    expect(panel).not.toContain("reduce(");
    expect(page).not.toContain("reduce(");
    expect(metalsPanel).not.toContain("reduce(");
  });

  it("renders exactly the three R4 perspectives — no stacked modules (R4-01/02)", () => {
    const page = readFileSync(
      join(here, "MarketIntelligencePage.tsx"),
      "utf8",
    );
    expect(page).toContain('view === "metals"');
    expect(page).toContain('view === "indicators"');
    expect(page).toContain('view === "fx"');
    // One panel per exclusive branch (metals + ipp + comex + fx).
    expect(page).toContain("MarketMetalsPanel");
    const panelCount = (page.match(/MarketIntelligencePanel</g) ?? [])
      .length;
    expect(panelCount).toBe(3);
    // Legacy surfaces removed from the composition.
    expect(page).not.toContain("MarketIntelligenceModuleSection");
    expect(page).not.toContain("MarketIntelligenceSeriesSection");
    expect(page).not.toContain("MarketIntelligenceMonthlyTable");
    expect(page).not.toContain("getMarketIntelligenceSummary");
  });

  it("renders the six metal cards via the local selectable component (R4-03/04)", () => {
    const page = readFileSync(
      join(here, "MarketIntelligencePage.tsx"),
      "utf8",
    );
    const card = readFileSync(
      join(here, "MarketInstrumentCard.tsx"),
      "utf8",
    );
    expect(page).toContain("MarketInstrumentCard");
    expect(page).toContain("filters.toggleMetal");
    // Accessible toggle semantics — never color-only selection.
    expect(card).toContain("aria-pressed");
    expect(card).toContain('type="button"');
    // D-04: selection is separate from data-access rights.
    expect(card).toContain("selectable");
    expect(card).toContain("dataAccessAllowed");
    expect(card).toContain("pendingLabel");
    // R5.S2: semantic icon + quote-basis/reference context line.
    expect(card).toContain("__icon");
    expect(card).toContain("formatMarketUnit");
    expect(card).toContain("context");
  });

  it("formats technical unit codes into friendly labels (R5.S2)", () => {
    const units = readFileSync(join(here, "marketUnits.ts"), "utf8");
    expect(units).toContain("usd_per_metric_ton");
    expect(units).toContain("usd_per_pound");
    expect(units).toContain("brl_per_usd");
    expect(units).toContain('"US$/t"');
    expect(units).toContain('"US$/lb"');
    expect(units).toContain('"R$/US$"');
    // Unknown units pass through verbatim — never silently dropped.
    expect(units).toContain("?? unit");
  });

  it("renders honest context cards on zero-observation states (R5.S2)", () => {
    const panel = readFileSync(
      join(here, "MarketIntelligencePanel.tsx"),
      "utf8",
    );
    const content = readFileSync(join(here, "content.ts"), "utf8");
    // Status cards use real feed/meta evidence — never fake metrics.
    // R5.S3: at most three compact items — last attempt, latest
    // observation, coverage; long messages live in the banner, and
    // internal codes/ISO strings are formatted for display.
    expect(panel).toContain("statusKpis");
    expect(panel).toContain("last_run_started_at");
    expect(panel).toContain("latest_observation_date");
    expect(panel).toContain("formatMarketDateTime");
    expect(panel).toContain("formatMarketDate");
    expect(panel).toContain("marketRunOutcomeLabel");
    expect(content).toContain("lastAttemptTitle");
    expect(content).toContain("latestObservationTitle");
    expect(content).toContain("coverageTitle");
    expect(content).toContain("runOutcome");
    expect(content).not.toContain("seriesTitle");
    // Config-pending preview is labels/hints only (value stays "—").
    expect(panel).toContain("configState?.preview");
    expect(panel).toContain("configState?.nextSteps");
    expect(content).toContain("comexNextSteps");
    expect(content).toContain("configPreviewLabel");
    expect(content).toContain("nextStepsLabel");
    // Section icons are semantic, rendered via header actions.
    expect(panel).toContain("sectionIcon");
    expect(panel).toContain("sp-section-icon");
  });

  it("names denied instruments and splits charts by unit (R5.S2)", () => {
    const metalsPanel = readFileSync(
      join(here, "MarketMetalsPanel.tsx"),
      "utf8",
    );
    const content = readFileSync(join(here, "content.ts"), "utf8");
    // Selected-but-denied instruments are listed with their BFF reason.
    expect(metalsPanel).toContain("denied");
    expect(metalsPanel).toContain("unavailable_reason");
    expect(content).toContain("unavailableSelectionLabel");
    expect(content).toContain("sourceUsePending");
    // Charts never mix incompatible units on one axis.
    expect(metalsPanel).toContain("chartGroups");
    expect(metalsPanel).toContain("sp-market-chart-group");
    // Series legends and table headers carry the friendly unit.
    expect(metalsPanel).toContain("formatMarketUnit");
  });

  it("enables the compare mode only for ≥2 authorized series (R4-07)", () => {
    const metalsPanel = readFileSync(
      join(here, "MarketMetalsPanel.tsx"),
      "utf8",
    );
    expect(metalsPanel).toContain("compareEligible");
    expect(metalsPanel).toContain("compareNeedTwoSeries");
    expect(metalsPanel).toContain("getMarketQuoteCompare");
    const indicatorsPanel = readFileSync(
      join(here, "MarketIntelligencePanel.tsx"),
      "utf8",
    );
    // Single-source perspectives keep the option visible but disabled —
    // units never mix.
    expect(indicatorsPanel).toContain("compareDisabledHint");
    expect(indicatorsPanel).toContain("disabled: true");
  });

  it("keeps chart/table/compare mutually exclusive (R4-07)", () => {
    const metalsPanel = readFileSync(
      join(here, "MarketMetalsPanel.tsx"),
      "utf8",
    );
    expect(metalsPanel).toContain('mode === "chart"');
    expect(metalsPanel).toContain('mode === "table"');
    expect(metalsPanel).toContain('mode === "compare"');
  });

  it("declares the four frequencies with per-series capability (R4-05)", () => {
    const page = readFileSync(
      join(here, "MarketIntelligencePage.tsx"),
      "utf8",
    );
    expect(page).toContain("granularityDay");
    expect(page).toContain("granularityWeek");
    expect(page).toContain("granularityMonth");
    expect(page).toContain("granularityYear");
    expect(page).toContain("supportedGranularities");
    expect(page).toContain("frequencyUnsupported");
  });

  it("documents stale/partial/empty/unavailable states (R4-08)", () => {
    const content = readFileSync(join(here, "content.ts"), "utf8");
    expect(content).toContain("staleNote");
    expect(content).toContain("partialNote");
    expect(content).toContain("fxMissingNote");
    expect(content).toContain("attributionLabel");
    expect(content).toContain("rateLimited");
    expect(content).toContain("unavailable");
    expect(content).toContain("comexConfigPending");
    expect(content).toContain("providerUnavailable");
    expect(content).toContain("feedNotCollected");
    expect(content).toContain("windowEmpty");
    expect(content).toContain("missingPeriodsExplanation");
    expect(content).toContain("pendingSource");
    expect(content).toContain("emptySelectionTitle");
  });

  it("URL read/write roundtrip preserves the R4 contract", () => {
    let written = "";
    withWindow(
      "?view=metals&metals=copper,aluminum&mode=compare&granularity=week&from=2025-01-01&to=2025-12-31",
      (stub) => {
        const state = readMarketIntelligenceFromUrl();
        expect(state.view).toBe("metals");
        expect(state.metals).toEqual(["copper", "aluminum"]);
        expect(state.mode).toBe("compare");
        expect(state.granularity).toBe("week");
        stub.history.replaceState = (_s, _t, url) => {
          written = url;
        };
        writeMarketIntelligenceToUrl({
          ...BASE_STATE,
          view: "metals",
          mode: "compare",
          metals: ["copper", "aluminum"],
          granularity: "week",
        });
      },
    );
    expect(written).toContain("view=metals");
    expect(written).toContain("metals=copper%2Caluminum");
    expect(written).toContain("mode=compare");
    expect(written).toContain("granularity=week");
  });

  it("URL write drops legacy instrument/currency params", () => {
    let written = "";
    withWindow("?instrument=copper&currency=USD&view=indicators", (stub) => {
      stub.history.replaceState = (_s, _t, url) => {
        written = url;
      };
      writeMarketIntelligenceToUrl(BASE_STATE);
    });
    expect(written).not.toContain("instrument=");
    expect(written).not.toContain("currency=");
    expect(written).toContain("view=indicators");
  });

  it("enforces default-deny on perspective selectability (R4-17)", () => {
    const page = readFileSync(
      join(here, "MarketIntelligencePage.tsx"),
      "utf8",
    );
    // Legacy payloads without `selectable`/`selectable_in_ui` must never
    // grant selection — only an explicit true is a permission.
    expect(page).toContain("entry.selectable === true");
    expect(page).toContain("entry.selectable_in_ui === true");
    expect(page).toContain("entry.data_access_allowed === true");
    expect(page).not.toContain("entry.selectable !== false");
    expect(page).toContain("noSelectableInstruments");
    const panel = readFileSync(
      join(here, "MarketIntelligencePanel.tsx"),
      "utf8",
    );
    // Denied responses clear previously rendered data.
    expect(panel).toContain("setRows([])");
    expect(panel).toContain("setSummary(null)");
    const metalsPanel = readFileSync(
      join(here, "MarketMetalsPanel.tsx"),
      "utf8",
    );
    expect(metalsPanel).toContain("setPayload(null)");
    expect(metalsPanel).toContain("data_access_allowed === true");
  });

  it("declares the neutral no-selectable-instruments copy", () => {
    const content = readFileSync(join(here, "content.ts"), "utf8");
    expect(content).toContain("noSelectableInstruments");
    expect(content).toContain("sourceNotApproved");
  });

  it("wires the dedicated BFF endpoints once each (R4-15)", () => {
    const page = readFileSync(
      join(here, "MarketIntelligencePage.tsx"),
      "utf8",
    );
    const metalsPanel = readFileSync(
      join(here, "MarketMetalsPanel.tsx"),
      "utf8",
    );
    // Perspectives consume only dedicated BFF endpoints — never upstream.
    expect(page).toContain("getMarketImportSeries");
    expect(page).toContain("getMarketProducerPriceSeries");
    expect(page).toContain("getMarketFxSeries");
    expect(metalsPanel).toContain("getMarketQuoteSeries");
    expect(metalsPanel).toContain("getMarketQuoteCompare");
    // No provider coupling in the UI contract (D-08).
    for (const file of [page, metalsPanel]) {
      expect(file).not.toMatch(/metalcharts|lme|shockmetais/i);
    }
  });

  it("documents the R4 perspectives without conflating metric kinds", () => {
    const content = readFileSync(join(here, "content.ts"), "utf8");
    // Comex FOB is never labelled a metal quote; IPP is never a price
    // in USD/t; metals stay USD-native.
    expect(content).toContain("valor médio de importação");
    expect(content).toContain("Metalurgia");
    expect(content).toContain("PTAX");
    expect(content).toContain("moduleUnavailable");
    expect(content).toContain("Metais");
    expect(content).toContain("Indicadores");
    expect(content).toContain("Câmbio");
    expect(content).toContain("Aguardando observações de fonte homologada");
    expect(content).toContain("unidade nativa");
  });

  it("URL read rejects malformed module selections", () => {
    withWindow("?ncm=12345&ipp_series=<script>&metals=<script>", () => {
      const state = readMarketIntelligenceFromUrl();
      expect(state.ncm).toBeUndefined();
      expect(state.ippSeries).toBeUndefined();
      expect(state.metals).toBeUndefined();
    });
  });

  it("URL read rejects out-of-contract values", () => {
    withWindow(
      "?view=<script>&mode=csv&granularity=hour&fx_kind=spot&indicator=nope&from=99%2F01%2F2025&to=nope",
      () => {
        const state = readMarketIntelligenceFromUrl();
        expect(state.view).toBeUndefined();
        expect(state.mode).toBeUndefined();
        expect(state.granularity).toBeUndefined();
        expect(state.fxKind).toBeUndefined();
        expect(state.indicator).toBeUndefined();
        expect(state.from).toBeUndefined();
        expect(state.to).toBeUndefined();
      },
    );
  });
});
