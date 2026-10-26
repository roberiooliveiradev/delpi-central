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
  view: "ipp" as const,
  mode: "chart" as const,
  granularity: "month" as const,
  fxKind: "ptax_closing_sell" as const,
  ncm: "",
  ippSeries: "",
  from: "2025-01-01",
  to: "2025-12-31",
};

describe("market intelligence page (PROC-0076 R3)", () => {
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

  it("persists the R3 contract in the URL (view/mode/filters)", () => {
    const url = readFileSync(join(here, "marketIntelligenceUrl.ts"), "utf8");
    expect(url).toContain("view");
    expect(url).toContain("mode");
    expect(url).toContain("granularity");
    expect(url).toContain("fx_kind");
    expect(url).toContain("ipp_series");
    expect(url).toContain("ncm");
    expect(url).toContain("replaceState");
  });

  it("maps a legacy R2 link (instrument=usd-brl) to the fx view", () => {
    withWindow("?instrument=usd-brl&currency=BRL", () => {
      const state = readMarketIntelligenceFromUrl();
      expect(state.view).toBe("fx");
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
    // Page composes through suppliesUi kit bindings — no direct kit import.
    expect(page).not.toMatch(/from ["']@delpi\/plugin-ui/);
    expect(page).toContain("sp-page-stack");
    expect(page).toContain("SuppliesPageHero");
    expect(page).toContain("SuppliesSelectField");
    expect(page).toContain("SuppliesSegmentToggle");
    expect(page).toContain("SuppliesDateField");
    // One analysis panel, exclusive chart/table modes.
    expect(panel).toContain("MultiTypeSeriesChart");
    expect(panel).toContain("ChartViewShell");
    expect(panel).toContain("SuppliesDataTable");
    expect(panel).toContain("SuppliesKpiCard");
    expect(panel).toContain('prefix="sp"');
    // No business math in the MFE — BFF owns metrics.
    expect(panel).not.toContain("reduce(");
    expect(page).not.toContain("reduce(");
  });

  it("renders exactly one perspective panel — no stacked R2 modules (R3-01)", () => {
    const page = readFileSync(
      join(here, "MarketIntelligencePage.tsx"),
      "utf8",
    );
    // Three exclusive conditional branches, each rendering the single
    // panel component — the old stacked module sections are gone.
    const panelCount = (page.match(/MarketIntelligencePanel</g) ?? [])
      .length;
    expect(panelCount).toBe(3);
    expect(page).toContain('view === "ipp"');
    expect(page).toContain('view === "comex"');
    expect(page).toContain('view === "fx"');
    // Legacy surfaces removed from the composition.
    expect(page).not.toContain("MarketIntelligenceModuleSection");
    expect(page).not.toContain("MarketIntelligenceSeriesSection");
    expect(page).not.toContain("MarketIntelligenceMonthlyTable");
    expect(page).not.toContain("getMarketIntelligenceSummary");
  });

  it("offers the comparison mode disabled — no mixed units (R3-03)", () => {
    const panel = readFileSync(
      join(here, "MarketIntelligencePanel.tsx"),
      "utf8",
    );
    expect(panel).toContain("compareDisabledHint");
    expect(panel).toContain("disabled: true");
  });

  it("keeps chart XOR table exclusive (R3-03)", () => {
    const panel = readFileSync(
      join(here, "MarketIntelligencePanel.tsx"),
      "utf8",
    );
    expect(panel).toContain('mode === "chart"');
    expect(panel).toContain('mode === "table"');
  });

  it("documents stale/partial/empty/unavailable states (R3-06..R3-08)", () => {
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
  });

  it("URL read/write roundtrip preserves the R3 contract", () => {
    let written = "";
    withWindow(
      "?view=comex&mode=table&ncm=74040010&granularity=year&from=2025-01-01&to=2025-12-31",
      (stub) => {
        const state = readMarketIntelligenceFromUrl();
        expect(state.view).toBe("comex");
        expect(state.mode).toBe("table");
        expect(state.ncm).toBe("74040010");
        expect(state.granularity).toBe("year");
        stub.history.replaceState = (_s, _t, url) => {
          written = url;
        };
        writeMarketIntelligenceToUrl({
          ...BASE_STATE,
          view: "comex",
          mode: "table",
          ncm: "74040010",
          granularity: "year",
        });
      },
    );
    expect(written).toContain("view=comex");
    expect(written).toContain("mode=table");
    expect(written).toContain("ncm=74040010");
    expect(written).toContain("granularity=year");
  });

  it("URL write drops legacy instrument/currency params", () => {
    let written = "";
    withWindow("?instrument=copper&currency=USD&view=ipp", (stub) => {
      stub.history.replaceState = (_s, _t, url) => {
        written = url;
      };
      writeMarketIntelligenceToUrl(BASE_STATE);
    });
    expect(written).not.toContain("instrument=");
    expect(written).not.toContain("currency=");
    expect(written).toContain("view=ipp");
  });

  it("enforces default-deny on perspective selectability (R1.3)", () => {
    const page = readFileSync(
      join(here, "MarketIntelligencePage.tsx"),
      "utf8",
    );
    // Legacy payloads without `selectable` must never grant selection —
    // only an explicit true is a permission.
    expect(page).toContain("entry.selectable === true");
    expect(page).not.toContain("entry.selectable !== false");
    // A catalog with zero selectable series renders a neutral
    // unavailability state, never the misleading empty-data card.
    expect(page).toContain("noSelectableInstruments");
    const panel = readFileSync(
      join(here, "MarketIntelligencePanel.tsx"),
      "utf8",
    );
    // Denied responses clear previously rendered data.
    expect(panel).toContain("setRows([])");
    expect(panel).toContain("setSummary(null)");
  });

  it("declares the neutral no-selectable-instruments copy", () => {
    const content = readFileSync(join(here, "content.ts"), "utf8");
    expect(content).toContain("noSelectableInstruments");
    expect(content).toContain("sourceNotApproved");
  });

  it("wires the three source endpoints once each (R3-01)", () => {
    const page = readFileSync(
      join(here, "MarketIntelligencePage.tsx"),
      "utf8",
    );
    // Perspectives consume only dedicated BFF endpoints — never upstream.
    expect(page).toContain("getMarketImportSeries");
    expect(page).toContain("getMarketProducerPriceSeries");
    expect(page).toContain("getMarketFxSeries");
    expect(page).toContain("entry.selectable === true");
  });

  it("documents the R3 perspectives without conflating metric kinds", () => {
    const content = readFileSync(join(here, "content.ts"), "utf8");
    // Comex FOB is never labelled a metal quote; IPP is never a price
    // in USD/t; both carry their own PT-BR labels.
    expect(content).toContain("valor médio de importação");
    expect(content).toContain("Metalurgia");
    expect(content).toContain("PTAX");
    expect(content).toContain("moduleUnavailable");
    expect(content).toContain("Preços industriais");
    expect(content).toContain("Importações");
    expect(content).toContain("Câmbio");
  });

  it("URL read rejects malformed module selections", () => {
    withWindow("?ncm=12345&ipp_series=<script>", () => {
      const state = readMarketIntelligenceFromUrl();
      expect(state.ncm).toBeUndefined();
      expect(state.ippSeries).toBeUndefined();
    });
  });

  it("URL read rejects out-of-contract values", () => {
    withWindow(
      "?view=<script>&mode=csv&granularity=hour&fx_kind=spot&from=99%2F01%2F2025&to=nope",
      () => {
        const state = readMarketIntelligenceFromUrl();
        expect(state.view).toBeUndefined();
        expect(state.mode).toBeUndefined();
        expect(state.granularity).toBeUndefined();
        expect(state.fxKind).toBeUndefined();
        expect(state.from).toBeUndefined();
        expect(state.to).toBeUndefined();
      },
    );
  });
});
