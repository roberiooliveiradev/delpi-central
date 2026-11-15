import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@delpi/plugin-ui/index", async () => await import("../../test/pluginUiMock"));

const getAnalysis = vi.fn();
const getSummary = vi.fn();
const getBreakdowns = vi.fn();
const getDaily = vi.fn();
const listRows = vi.fn();
const listOptions = vi.fn();

vi.mock("../../api/entryAuditApi", () => ({
  downloadEntryAuditExport: vi.fn(),
  getEntryAuditAnalysis: (...args: unknown[]) => getAnalysis(...args),
  getEntryAuditBreakdowns: (...args: unknown[]) => getBreakdowns(...args),
  getEntryAuditDaily: (...args: unknown[]) => getDaily(...args),
  getEntryAuditSummary: (...args: unknown[]) => getSummary(...args),
  listEntryAuditOptions: (...args: unknown[]) => listOptions(...args),
  listEntryAuditRows: (...args: unknown[]) => listRows(...args),
  listEntryAuditTes: vi.fn(),
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

const mockAnalysis = {
  id: "a1",
  date_from: "2026-11-07",
  date_to: "2026-11-13",
  status: "done",
  branches: ["01", "02"],
  document_types: ["nfe", "cte"],
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
  listOptions.mockReset();

  window.history.replaceState({}, "", "/?tab=occurrences&page=1");

  listOptions.mockResolvedValue({ branches: [], document_types: [] });
  getAnalysis.mockResolvedValue(mockAnalysis);
  getSummary.mockResolvedValue(mockSummary);
  getBreakdowns.mockResolvedValue({
    by_severity: [
      { name: "Alta", count: 1 },
      { name: "Baixa", count: 2 },
    ],
    by_theme: [
      { name: "itens", count: 2 },
      { name: "cabecalho", count: 1 },
    ],
    suppliers: [{ name: "ACME", count: 2 }],
    tes: [{ name: "148", count: 1 }],
  });
  getDaily.mockResolvedValue({
    series: [
      { name: "2026-11-07", count: 1 },
      { name: "2026-11-08", count: 0 },
      { name: "2026-11-09", count: 1 },
    ],
    previous: [],
    period: ["2026-11-07", "2026-11-13"],
  });
  listRows.mockResolvedValue({
    items: [{ stable_key: "occ-1", document_number: "1", status: "pending" }],
    page: 1,
    page_size: 50,
    total: 3,
  });
});

async function renderReady() {
  render(
    <EntryAuditAnalysisPage
      basePath="/apps/controllership-finance"
      analysisId="a1"
    />,
  );
  await screen.findByLabelText("Distribuição por severidade");
}

describe("EntryAuditAnalysisPage selection (U14 F1)", () => {
  it("AC-SEL-1: Limpar seleção remove severity da URL", async () => {
    await renderReady();
    const donut = screen.getByLabelText("Distribuição por severidade");
    fireEvent.click(
      Array.from(donut.querySelectorAll("button")).find((b) =>
        b.textContent?.includes("Alta"),
      ) as HTMLButtonElement,
    );
    await waitFor(() => {
      expect(window.location.search).toMatch(/severity=high/);
    });
    fireEvent.click(screen.getByRole("button", { name: "Limpar seleção" }));
    await waitFor(() => {
      expect(window.location.search).not.toMatch(/severity=/);
    });
  });

  it("AC-SEL-2: segundo clique na fatia ou barra limpa o filtro", async () => {
    await renderReady();
    const donut = screen.getByLabelText("Distribuição por severidade");
    const alta = () =>
      Array.from(donut.querySelectorAll("button")).find((b) =>
        b.textContent?.includes("Alta"),
      ) as HTMLButtonElement;
    fireEvent.click(alta());
    await waitFor(() => {
      expect(window.location.search).toMatch(/severity=high/);
    });
    fireEvent.click(alta());
    await waitFor(() => {
      expect(window.location.search).not.toMatch(/severity=/);
    });

    const themeBars = screen.getByLabelText("Ocorrências por tema");
    const themeBtn = () =>
      themeBars.querySelector("button") as HTMLButtonElement;
    fireEvent.click(themeBtn());
    await waitFor(() => {
      expect(window.location.search).toMatch(/theme=/);
    });
    fireEvent.click(themeBtn());
    await waitFor(() => {
      expect(window.location.search).not.toMatch(/theme=/);
    });
  });

  it("AC-SEL-4: Limpar filtros remove todos os filtros de detalhamento", async () => {
    window.history.replaceState(
      {},
      "",
      "/?tab=occurrences&severity=high&theme=itens&supplier=ACME&tes=148&day=2026-11-07",
    );
    await renderReady();
    await screen.findByRole("button", { name: "Limpar filtros" });
    fireEvent.click(screen.getByRole("button", { name: "Limpar filtros" }));
    await waitFor(() => {
      const q = window.location.search;
      expect(q).not.toMatch(/severity=/);
      expect(q).not.toMatch(/theme=/);
      expect(q).not.toMatch(/supplier=/);
      expect(q).not.toMatch(/tes=/);
      expect(q).not.toMatch(/day=/);
    });
  });
});
