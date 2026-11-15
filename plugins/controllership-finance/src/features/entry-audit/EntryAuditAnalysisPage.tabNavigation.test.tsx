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
  ENTRY_AUDIT_SEVERITY_URL: {},
}));

vi.mock("../../app/pluginNavigation", () => ({
  navigatePluginPath: (path: string) => {
    const url = new URL(path, "http://localhost");
    window.history.replaceState({}, "", `${url.pathname}${url.search}`);
    window.dispatchEvent(new PopStateEvent("popstate"));
  },
}));

import { EntryAuditAnalysisPage } from "./EntryAuditAnalysisPage";

const mockAnalysis = {
  id: "a1",
  date_from: "2026-10-01",
  date_to: "2026-10-31",
  status: "done",
  branches: ["01"],
  document_types: ["nfe"],
};

const mockSummary = {
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
};

afterEach(() => {
  cleanup();
});

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
  getAnalysis.mockResolvedValue(mockAnalysis);
  getSummary.mockResolvedValue(mockSummary);
  getBreakdowns.mockResolvedValue({
    by_severity: [],
    by_theme: [],
    suppliers: [],
    tes: [],
  });
  getDaily.mockResolvedValue({
    series: [{ name: "2026-10-01", count: 1 }],
    previous: [],
    period: ["2026-10-01", "2026-10-31"],
  });
  listRows.mockResolvedValue({
    items: [{ stable_key: "occ-1", document_number: "1", status: "pending" }],
    page: 1,
    page_size: 50,
    total: 3,
  });
});

describe("EntryAuditAnalysisPage tab navigation (W6 / A1)", () => {
  it("troca de aba não reconsulta summary, breakdowns nem daily", async () => {
    render(
      <EntryAuditAnalysisPage
        basePath="/apps/controllership-finance"
        analysisId="a1"
      />,
    );

    await screen.findByRole("tab", { name: /Ocorrências/i });
    await waitFor(() => {
      expect(getSummary).toHaveBeenCalledTimes(1);
      expect(getBreakdowns).toHaveBeenCalledTimes(1);
      expect(getDaily).toHaveBeenCalledTimes(1);
      // 1 = aba ativa (ocorrências) + 1 = pré-busca total da aba CT-e (AC-TAB-1)
      expect(listRows).toHaveBeenCalledTimes(2);
    });

    const documentsTab = await screen.findByRole("tab", {
      name: /Notas casadas/i,
    });
    listRows.mockResolvedValueOnce({
      items: [{ access_key: "k1", document_number: "99" }],
      page: 1,
      page_size: 50,
      total: 12,
    });
    fireEvent.click(documentsTab);

    await waitFor(() => {
      expect(listRows).toHaveBeenCalledTimes(3);
    });

    expect(getSummary).toHaveBeenCalledTimes(1);
    expect(getBreakdowns).toHaveBeenCalledTimes(1);
    expect(getDaily).toHaveBeenCalledTimes(1);
  });
});