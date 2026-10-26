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

describe("market intelligence page (PROC-0076)", () => {
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

  it("is reachable by URL but absent from hub/palette while E11 is open", () => {
    const every = HUB_SECTIONS.flatMap((section) => section.routes);
    expect(
      every.find((route) => route.viewId === "market_intelligence"),
    ).toBeUndefined();
  });

  it("persists filters in the URL with allowlisted values", () => {
    const url = readFileSync(join(here, "marketIntelligenceUrl.ts"), "utf8");
    expect(url).toContain("instrument");
    expect(url).toContain("currency");
    expect(url).toContain("granularity");
    expect(url).toContain("fx_kind");
    expect(url).toContain("replaceState");
  });

  it("uses kit-first components and scoped sp classes", () => {
    const page = readFileSync(
      join(here, "MarketIntelligencePage.tsx"),
      "utf8",
    );
    const series = readFileSync(
      join(here, "MarketIntelligenceSeriesSection.tsx"),
      "utf8",
    );
    const table = readFileSync(
      join(here, "MarketIntelligenceMonthlyTable.tsx"),
      "utf8",
    );
    // Page composes through suppliesUi kit bindings — no direct kit import.
    expect(page).not.toMatch(/from ["']@delpi\/plugin-ui/);
    // Chart/table components use the kit's chart/data families directly,
    // same pattern as OverviewOtdSeriesChart/DeliveriesListTable.
    expect(series).toContain('prefix="sp"');
    expect(table).toContain("spDataTableClassNames");
    expect(page).toContain("sp-page-stack");
    expect(page).toContain("SuppliesPageHero");
    expect(page).toContain("SuppliesSelectField");
    expect(page).toContain("SuppliesSegmentToggle");
    expect(page).toContain("SuppliesDateField");
    expect(page).toContain("SuppliesKpiCard");
    expect(series).toContain("MultiTypeSeriesChart");
    expect(series).toContain("ChartViewShell");
    expect(table).toContain("SuppliesDataTable");
    expect(table).toContain("SuppliesCompactPagination");
    // No business math in the MFE — BFF owns conversion/averages.
    expect(page).not.toContain("price * ");
    expect(page).not.toContain("reduce(");
  });

  it("documents stale/partial/empty states and source attribution", () => {
    const content = readFileSync(join(here, "content.ts"), "utf8");
    expect(content).toContain("staleNote");
    expect(content).toContain("partialNote");
    expect(content).toContain("fxMissingNote");
    expect(content).toContain("attributionLabel");
    expect(content).toContain("rateLimited");
    expect(content).toContain("unavailable");
  });

  it("URL read/write roundtrip preserves the contract", () => {
    let written = "";
    withWindow(
      "?instrument=copper&currency=BRL&granularity=month&fx_kind=ptax_closing_buy&from=2025-01-01&to=2025-12-31",
      (stub) => {
        const state = readMarketIntelligenceFromUrl();
        expect(state.instrument).toBe("copper");
        expect(state.currency).toBe("BRL");
        expect(state.granularity).toBe("month");
        expect(state.fxKind).toBe("ptax_closing_buy");
        expect(state.from).toBe("2025-01-01");
        expect(state.to).toBe("2025-12-31");
        stub.history.replaceState = (_s, _t, url) => {
          written = url;
        };
        writeMarketIntelligenceToUrl({
          instrument: "copper",
          currency: "BRL",
          granularity: "month",
          fxKind: "ptax_closing_buy",
          from: "2025-01-01",
          to: "2025-12-31",
        });
      },
    );
    expect(written).toContain("instrument=copper");
    expect(written).toContain("currency=BRL");
    expect(written).toContain("fx_kind=ptax_closing_buy");
  });

  it("URL read rejects out-of-contract values", () => {
    withWindow(
      "?instrument=<script>&currency=EUR&granularity=hour&fx_kind=spot&from=99%2F01%2F2025&to=nope",
      () => {
        const state = readMarketIntelligenceFromUrl();
        expect(state.currency).toBeUndefined();
        expect(state.granularity).toBeUndefined();
        expect(state.fxKind).toBeUndefined();
        expect(state.from).toBeUndefined();
        expect(state.to).toBeUndefined();
      },
    );
  });
});
