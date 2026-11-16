/**
 * U15R R1 — Evolução por dia (MultiTypeSeriesChart) com clique → filtro day.
 */
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@delpi/plugin-ui/index", async () => await import("../../test/pluginUiMock"));

const getAnalysis = vi.fn();
const getSummary = vi.fn();
const getBreakdowns = vi.fn();
const getDaily = vi.fn();
const listRows = vi.fn();
const listTes = vi.fn();
const listOptions = vi.fn();

vi.mock("../../api/entryAuditApi", () => ({
  downloadEntryAuditExport: vi.fn(),
  getEntryAuditAnalysis: (...args: unknown[]) => getAnalysis(...args),
  getEntryAuditBreakdowns: (...args: unknown[]) => getBreakdowns(...args),
  getEntryAuditDaily: (...args: unknown[]) => getDaily(...args),
  getEntryAuditSummary: (...args: unknown[]) => getSummary(...args),
  listEntryAuditOptions: (...args: unknown[]) => listOptions(...args),
  listEntryAuditRows: (...args: unknown[]) => listRows(...args),
  listEntryAuditTes: (...args: unknown[]) => listTes(...args),
  setEntryAuditOccurrenceStatus: vi.fn(),
  ENTRY_AUDIT_SEVERITY_URL: { high: "Alta", medium: "Media", low: "Baixa" },
}));

vi.mock("../../app/pluginNavigation", () => ({
  navigatePluginPath: (path: string) => {
    const url = new URL(path, "http://localhost");
    window.history.replaceState({}, "", `${url.pathname}${url.search}`);
    window.dispatchEvent(new PopStateEvent("popstate"));
  },
}));

import { EntryAuditAnalysisPage } from "./EntryAuditAnalysisPage";

afterEach(() => cleanup());

beforeEach(() => {
  getAnalysis.mockReset();
  getSummary.mockReset();
  getBreakdowns.mockReset();
  getDaily.mockReset();
  listRows.mockReset();
  listTes.mockReset();
  listOptions.mockReset();
  window.history.replaceState({}, "", "/?tab=occurrences&page=1");
  listOptions.mockResolvedValue({ branches: [], document_types: [] });
  listTes.mockResolvedValue({ items: [] });
  getAnalysis.mockResolvedValue({
    id: "a1",
    date_from: "2026-11-07",
    date_to: "2026-11-09",
    status: "done",
    branches: ["01"],
    document_types: ["nfe"],
  });
  getSummary.mockResolvedValue({
    kpis: {
      documents: 12,
      occurrences: 3,
      high: 1,
      pending: 2,
      resolved: 1,
      xml_unavailable: 0,
      gross_checked: 1000,
      high_difference: 50,
    },
    previous: null,
    conformity: {
      clean: 10,
      divergent: 2,
      unmatched_open: 1,
      unmatched_explained: 0,
      posted_outside_period: { count: 0, by_date: [] },
    },
  });
  getBreakdowns.mockResolvedValue({
    by_severity: [{ name: "Alta", count: 1 }],
    by_theme: [],
    suppliers: [],
    tes: [],
  });
  getDaily.mockResolvedValue({
    series: [
      { name: "2026-11-07", count: 1 },
      { name: "2026-11-08", count: 2 },
      { name: "2026-11-09", count: 0 },
    ],
    previous: [],
    period: ["2026-11-07", "2026-11-09"],
  });
  listRows.mockResolvedValue({
    items: [],
    page: 1,
    page_size: 25,
    total: 0,
  });
});

describe("EntryAuditAnalysisPage daily evolution (U15R R1)", () => {
  it("clique na categoria define day=; segundo clique limpa", async () => {
    render(
      <EntryAuditAnalysisPage
        basePath="/apps/controllership-finance"
        analysisId="a1"
      />,
    );
    await screen.findByTestId("multi-type-series-chart");
    const dayBtn = () =>
      screen.getByRole("button", { name: /08\/11:\s*2/i });
    fireEvent.click(dayBtn());
    await waitFor(() => {
      expect(window.location.search).toMatch(/day=2026-11-08/);
    });
    fireEvent.click(dayBtn());
    await waitFor(() => {
      expect(window.location.search).not.toMatch(/day=/);
    });
  });

  it("oferece troca de tipo coluna/linha/área (period_compare)", async () => {
    render(
      <EntryAuditAnalysisPage
        basePath="/apps/controllership-finance"
        analysisId="a1"
      />,
    );
    const toggle = await screen.findByTestId("chart-type-segment-toggle");
    expect(toggle.getAttribute("data-value")).toBe("column");
    expect(screen.getByRole("button", { name: /^column$/i })).toBeTruthy();
    expect(screen.getByRole("button", { name: /^line$/i })).toBeTruthy();
    expect(screen.getByRole("button", { name: /^area$/i })).toBeTruthy();
  });
});
