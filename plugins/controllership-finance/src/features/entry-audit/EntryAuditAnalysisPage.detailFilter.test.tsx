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
  ENTRY_AUDIT_SEVERITY_URL: { Alta: "alta", Media: "media", Baixa: "baixa" },
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

function buildSummary(overrides: {
  documents?: number;
  high?: number;
  pending?: number;
}) {
  return {
    kpis: {
      documents: overrides.documents ?? 12,
      occurrences: 3,
      high: overrides.high ?? 1,
      pending: overrides.pending ?? 2,
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
}

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
  getSummary.mockResolvedValue(buildSummary({}));
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

describe("EntryAuditAnalysisPage detail filter (U13 X3)", () => {
  it("filtro de detalhamento mantém hero/KPIs e atualiza números ao chegar o resumo", async () => {
    render(
      <EntryAuditAnalysisPage
        basePath="/apps/controllership-finance"
        analysisId="a1"
      />,
    );

    await screen.findByRole("group", { name: "Indicadores da auditoria" });
    expect(screen.getByRole("heading", { name: /Análise de / })).toBeTruthy();
    expect(screen.getByText("Notas conferidas").closest("article")?.textContent).toMatch(
      /12/,
    );

    let resolveSummary: (value: ReturnType<typeof buildSummary>) => void = () =>
      undefined;
    const deferred = new Promise<ReturnType<typeof buildSummary>>((resolve) => {
      resolveSummary = resolve;
    });
    getSummary.mockImplementationOnce(() => deferred);
    listRows.mockResolvedValue({
      items: [{ stable_key: "occ-2", document_number: "2", status: "pending" }],
      page: 1,
      page_size: 50,
      total: 1,
    });

    fireEvent.click(screen.getByText("Alta"));

    await waitFor(() => {
      expect(getSummary).toHaveBeenCalledTimes(2);
    });

    // Hero e KPIs permanecem montados com dados anteriores (stale-while-revalidate).
    expect(screen.getByRole("heading", { name: /Análise de / })).toBeTruthy();
    expect(
      screen.getByRole("group", { name: "Indicadores da auditoria" }),
    ).toBeTruthy();
    expect(screen.getByText("Notas conferidas").closest("article")?.textContent).toMatch(
      /12/,
    );
    expect(
      screen.getByRole("group", { name: "Indicadores da auditoria" }).getAttribute(
        "aria-busy",
      ),
    ).toBe("true");

    resolveSummary(buildSummary({ documents: 4, high: 4, pending: 4 }));

    await waitFor(() => {
      expect(
        screen.getByText("Notas conferidas").closest("article")?.textContent,
      ).toMatch(/4/);
    });
    await waitFor(() => {
      expect(
        screen
          .getByRole("group", { name: "Indicadores da auditoria" })
          .getAttribute("aria-busy"),
      ).toBeNull();
    });
  });
});
