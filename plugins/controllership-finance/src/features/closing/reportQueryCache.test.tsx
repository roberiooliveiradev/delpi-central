import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@delpi/plugin-ui/index", async () => await import("../../test/pluginUiMock"));

const p3Mock = vi.fn();
const matrixMock = vi.fn();
const summaryMock = vi.fn();
const stockMock = vi.fn();
const reconMock = vi.fn();

vi.mock("../../api/p3Api", () => ({
  getP3State: (...args: unknown[]) => p3Mock(...args),
}));
vi.mock("../../api/reportsApi", () => ({
  listReportMatrix: (...args: unknown[]) => matrixMock(...args),
}));
vi.mock("../../api/financialSettlementsApi", () => ({
  getFinancialSettlementsSummary: (...args: unknown[]) => summaryMock(...args),
}));
vi.mock("../../api/stockInventoryApi", () => ({
  getStockInventory: (...args: unknown[]) => stockMock(...args),
}));
vi.mock("../../api/stockReconciliationApi", () => ({
  getStockReconciliation: (...args: unknown[]) => reconMock(...args),
}));

import { ApiError } from "../../api/httpClient";
import { ControllershipQueryProvider } from "../../app/ControllershipQueryProvider";
import {
  readTokenSubject,
  sealReportSession,
} from "../../app/reportQueryCache";
import {
  invalidateP3,
  invalidateReportMatrix,
  invalidateVisibleReports,
} from "../../app/reportQueryInvalidation";
import {
  REPORT_GC_TIME_MS,
  p3QueryKey,
  settlementsSummaryQueryKey,
  stockInventoryQueryKey,
  type ReportCacheScope,
} from "../../app/reportQueryKeys";
import { MonthlyReportsPanel } from "./MonthlyReportsPanel";

const PERIOD = "2026-10";
const SCOPE: ReportCacheScope = {
  subject: "user-1",
  authzFingerprint: "0:controllership-finance.access",
  generation: 1,
};

function token(sub: string): string {
  const payload = btoa(JSON.stringify({ sub }))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/g, "");
  return `e30.${payload}.sig`;
}

function readyMocks() {
  p3Mock.mockResolvedValue({
    period: PERIOD,
    state: "READY_TO_CLOSE",
    canonical_stock_state: "OPEN",
    cutoff: null,
    reconciliations: [],
    last_revalidation: null,
    revalidation_valid: true,
    input_fingerprint: "fp",
    blockers: [],
  });
  matrixMock.mockResolvedValue({ period: PERIOD, reports: [] });
  summaryMock.mockResolvedValue({
    report: "financial_settlements_summary",
    period: { start_date: `${PERIOD}-01`, end_date: `${PERIOD}-31` },
    status: "available",
    officialTotals: false,
    quality: {
      missingDocumentCount: 0,
      missingNatureCount: 0,
      unresolvedBranchCount: 0,
    },
    groups: [],
  });
  stockMock.mockResolvedValue({
    report: "stock_inventory",
    period: PERIOD,
    referenceDate: `${PERIOD}-31`,
    dataAsOf: "2026-10-31T23:59:59Z",
    branchCode: "all",
    reportScope: "all_products",
    source: "totvs_sb9",
    officialP7: false,
    parityStatus: "PENDING",
    status: "source_missing",
    branchesAvailable: [],
    branchesMissing: [],
    historicalTotal: null,
    pagination: {
      page: 1,
      page_size: 25,
      total_items: 0,
      total_pages: 0,
      has_next: false,
      has_previous: false,
    },
    items: [],
    summariesByType: [],
    summariesByWarehouse: [],
  });
  reconMock.mockResolvedValue({
    report: "stock_reconciliation",
    kind: "analytical",
    governedReconciliation: "P3",
    period: PERIOD,
    branchCode: "all",
    reportScope: "all_products",
    equation: "DIVERGENCIA = ENTRADAS_SAIDAS - P7 - H02",
    operandSemantics: {},
    eligibility: "INELIGIBLE",
    ineligibleOperands: ["p7"],
    operands: {
      entradasSaidas: { available: true, status: "AVAILABLE", value: "10.00" },
      p7: { available: false, status: "SOURCE_MISSING", value: null },
      h02: { available: true, status: "AVAILABLE", value: "1.00" },
    },
    components: {},
    divergence: null,
    divergenceCents: null,
    parity: "NOT_COMPUTED",
    parityTolerance: "NONE",
    provenance: {},
  });
}

function renderPanel(period = PERIOD) {
  return render(
    <MonthlyReportsPanel
      period={period}
      selectedReport={null}
      onOpenReport={vi.fn()}
      reportHref={(key) => key}
    />,
  );
}

afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

beforeEach(() => {
  p3Mock.mockReset();
  matrixMock.mockReset();
  summaryMock.mockReset();
  stockMock.mockReset();
  reconMock.mockReset();
});

describe("chaves e identidade", () => {
  it("separa período, filtro e paginação sem usar o token", () => {
    const settlementsA = settlementsSummaryQueryKey(SCOPE, {
      startDate: "2026-10-01",
      endDate: "2026-10-31",
      natureCode: "ALUG",
    });
    const settlementsB = settlementsSummaryQueryKey(SCOPE, {
      startDate: "2026-10-01",
      endDate: "2026-10-31",
      natureCode: "VND",
    });
    const stockA = stockInventoryQueryKey(SCOPE, { period: PERIOD, page: 1 });
    const stockB = stockInventoryQueryKey(SCOPE, { period: PERIOD, page: 2 });
    expect(settlementsA).not.toEqual(settlementsB);
    expect(stockA).not.toEqual(stockB);
    expect(JSON.stringify(p3QueryKey(SCOPE, PERIOD))).not.toContain("Bearer");
    expect(JSON.stringify(p3QueryKey(SCOPE, PERIOD))).not.toContain("sig");
  });

  it("lê somente o sub e rejeita token sem sujeito", () => {
    expect(readTokenSubject(token("user-1"))).toBe("user-1");
    expect(readTokenSubject("nao-e-jwt")).toBeNull();
    expect(readTokenSubject(undefined)).toBeNull();
  });
});

describe("reutilização das cinco consultas", () => {
  it("monta uma vez, reabre sem request e distingue a competência", async () => {
    readyMocks();
    const first = renderPanel();
    await screen.findByText("Relatórios para análise");
    expect(p3Mock).toHaveBeenCalledTimes(1);
    expect(matrixMock).toHaveBeenCalledTimes(1);
    expect(summaryMock).toHaveBeenCalledTimes(1);
    expect(stockMock).toHaveBeenCalledTimes(1);
    expect(reconMock).toHaveBeenCalledTimes(1);

    first.unmount();
    renderPanel();
    await screen.findByText("Relatórios para análise");
    expect(p3Mock).toHaveBeenCalledTimes(1);
    expect(summaryMock).toHaveBeenCalledTimes(1);

    renderPanel("2026-11");
    await waitFor(() => expect(p3Mock).toHaveBeenCalledWith("2026-11", expect.anything()));
    expect(summaryMock).toHaveBeenCalledWith(
      expect.objectContaining({ startDate: "2026-11-01", endDate: "2026-11-30" }),
      expect.anything(),
    );
  });

  it("deduplica consultas equivalentes em montagem simultânea", async () => {
    readyMocks();
    render(
      <>
        <MonthlyReportsPanel
          period={PERIOD}
          selectedReport={null}
          onOpenReport={vi.fn()}
          reportHref={(key) => key}
        />
        <MonthlyReportsPanel
          period={PERIOD}
          selectedReport={null}
          onOpenReport={vi.fn()}
          reportHref={(key) => key}
        />
      </>,
    );
    await screen.findAllByText("Relatórios para análise");
    expect(p3Mock).toHaveBeenCalledTimes(1);
    expect(stockMock).toHaveBeenCalledTimes(1);
  });

  it("não exibe a posição ausente do mês anterior enquanto o mês novo carrega", async () => {
    readyMocks();
    stockMock.mockImplementation(async (query: { period: string }) => {
      if (query.period === PERIOD) {
        return {
          report: "stock_inventory",
          period: PERIOD,
          status: "source_missing",
          historicalTotal: null,
          officialP7: false,
          parityStatus: "PENDING",
          pagination: { page: 1, page_size: 25, total_items: 0, total_pages: 0 },
          items: [],
          summariesByType: [],
          summariesByWarehouse: [],
          branchesAvailable: [],
          branchesMissing: [],
        };
      }
      return new Promise(() => undefined);
    });
    const view = renderPanel();
    await screen.findAllByText("Posição histórica indisponível");
    view.rerender(
      <MonthlyReportsPanel
        period="2026-11"
        selectedReport={null}
        onOpenReport={vi.fn()}
        reportHref={(key) => key}
      />,
    );
    expect(screen.queryAllByText("Posição histórica indisponível")).toHaveLength(0);
  });

  it("refaz P3 e matriz depois do frescor e mantém a leitura operacional", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    readyMocks();
    const view = renderPanel();
    await screen.findByText("Relatórios para análise");
    view.unmount();
    await vi.advanceTimersByTimeAsync(61_000);
    renderPanel();
    await waitFor(() => expect(p3Mock).toHaveBeenCalledTimes(2));
    expect(matrixMock).toHaveBeenCalledTimes(2);
    expect(summaryMock).toHaveBeenCalledTimes(1);
    expect(stockMock).toHaveBeenCalledTimes(1);
    expect(reconMock).toHaveBeenCalledTimes(1);
  });

  it("descarta o cache inativo depois do gcTime", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    readyMocks();
    const view = renderPanel();
    await screen.findByText("Relatórios para análise");
    view.unmount();
    await vi.advanceTimersByTimeAsync(REPORT_GC_TIME_MS + 1_000);
    renderPanel();
    await waitFor(() => expect(summaryMock).toHaveBeenCalledTimes(2));
    expect(p3Mock).toHaveBeenCalledTimes(2);
  });

  it("atualização manual refaz as cinco fontes da competência visível", async () => {
    readyMocks();
    renderPanel();
    await screen.findByText("Relatórios para análise");
    invalidateVisibleReports(PERIOD);
    await waitFor(() => expect(p3Mock).toHaveBeenCalledTimes(2));
    expect(summaryMock).toHaveBeenCalledTimes(2);
    expect(stockMock).toHaveBeenCalledTimes(2);
    expect(reconMock).toHaveBeenCalledTimes(2);
    expect(matrixMock).toHaveBeenCalledTimes(2);
  });
});

describe("isolamento", () => {
  function renderScoped(
    sub: string,
    permissions: string[] = ["controllership-finance.access"],
  ) {
    return render(
      <ControllershipQueryProvider
        getAccessToken={() => token(sub)}
        permissions={permissions}
      >
        <MonthlyReportsPanel
          period={PERIOD}
          selectedReport={null}
          onOpenReport={vi.fn()}
          reportHref={(key) => key}
        />
      </ControllershipQueryProvider>,
    );
  }

  it("não consulta sem sujeito e limpa no logout", async () => {
    readyMocks();
    const view = render(
      <ControllershipQueryProvider getAccessToken={() => undefined}>
        <MonthlyReportsPanel
          period={PERIOD}
          selectedReport={null}
          onOpenReport={vi.fn()}
          reportHref={(key) => key}
        />
      </ControllershipQueryProvider>,
    );
    expect(await screen.findByText(/Sessão expirada/)).toBeTruthy();
    expect(p3Mock).not.toHaveBeenCalled();

    view.rerender(
      <ControllershipQueryProvider
        getAccessToken={() => token("user-1")}
        permissions={["controllership-finance.access"]}
      >
        <MonthlyReportsPanel
          period={PERIOD}
          selectedReport={null}
          onOpenReport={vi.fn()}
          reportHref={(key) => key}
        />
      </ControllershipQueryProvider>,
    );
    await screen.findByText("Relatórios para análise");
    const calls = p3Mock.mock.calls.length;
    const refreshed = token("user-1");
    view.rerender(
      <ControllershipQueryProvider
        getAccessToken={() => refreshed}
        permissions={["controllership-finance.access"]}
      >
        <MonthlyReportsPanel
          period={PERIOD}
          selectedReport={null}
          onOpenReport={vi.fn()}
          reportHref={(key) => key}
        />
      </ControllershipQueryProvider>,
    );
    expect(p3Mock).toHaveBeenCalledTimes(calls);

    window.dispatchEvent(new CustomEvent("DELPI_GLOBAL_LOGOUT"));
    expect(await screen.findByText(/Sessão expirada/)).toBeTruthy();
    expect(screen.queryByText("Relatórios para análise")).toBeNull();
    expect(p3Mock).toHaveBeenCalledTimes(calls);
  });

  it("troca de sub e de permissions descarta o resultado anterior", async () => {
    readyMocks();
    const view = renderScoped("user-1");
    await screen.findAllByText("Posição histórica indisponível");
    stockMock.mockImplementation(() => new Promise(() => undefined));
    view.rerender(
      <ControllershipQueryProvider
        getAccessToken={() => token("user-2")}
        permissions={["controllership-finance.access"]}
      >
        <MonthlyReportsPanel
          period={PERIOD}
          selectedReport={null}
          onOpenReport={vi.fn()}
          reportHref={(key) => key}
        />
      </ControllershipQueryProvider>,
    );
    expect(screen.queryAllByText("Posição histórica indisponível")).toHaveLength(0);

    stockMock.mockResolvedValue({
      report: "stock_inventory",
      period: PERIOD,
      status: "source_missing",
      historicalTotal: null,
      officialP7: false,
      parityStatus: "PENDING",
      pagination: { page: 1, page_size: 25, total_items: 0, total_pages: 0 },
      items: [],
      summariesByType: [],
      summariesByWarehouse: [],
      branchesAvailable: [],
      branchesMissing: [],
    });
    view.rerender(
      <ControllershipQueryProvider
        getAccessToken={() => token("user-2")}
        permissions={["controllership-finance.manage"]}
      >
        <MonthlyReportsPanel
          period={PERIOD}
          selectedReport={null}
          onOpenReport={vi.fn()}
          reportHref={(key) => key}
        />
      </ControllershipQueryProvider>,
    );
    await waitFor(() =>
      expect(stockMock.mock.calls.length).toBeGreaterThanOrEqual(2),
    );
  });

  it("401 e 403 não mantêm a posição anterior", async () => {
    readyMocks();
    renderPanel();
    await screen.findAllByText("Posição histórica indisponível");
    stockMock.mockRejectedValue(new ApiError(401, "sessão", "unauthorized"));
    invalidateVisibleReports(PERIOD);
    expect(await screen.findByText(/Sessão expirada/)).toBeTruthy();
    expect(screen.queryAllByText("Posição histórica indisponível")).toHaveLength(0);

    sealReportSession(null);
  });

  it("403 substitui o payload da fonte sem tratar como logout", async () => {
    readyMocks();
    renderPanel();
    await screen.findAllByText("Posição histórica indisponível");
    stockMock.mockRejectedValue(new ApiError(403, "negado", "forbidden"));
    reconMock.mockResolvedValue({
      report: "stock_reconciliation",
      kind: "analytical",
      governedReconciliation: "P3",
      period: PERIOD,
      branchCode: "all",
      reportScope: "all_products",
      equation: "DIVERGENCIA = ENTRADAS_SAIDAS - P7 - H02",
      operandSemantics: {},
      eligibility: "ELIGIBLE",
      ineligibleOperands: [],
      operands: {
        entradasSaidas: { available: true, status: "AVAILABLE", value: "10.00" },
        p7: { available: true, status: "AVAILABLE", value: "8.00" },
        h02: { available: true, status: "AVAILABLE", value: "1.00" },
      },
      components: {},
      divergence: "1.00",
      divergenceCents: 100,
      parity: "NOT_COMPUTED",
      parityTolerance: "NONE",
      provenance: {},
    });
    invalidateVisibleReports(PERIOD);
    expect(
      await screen.findByText(/Você não tem autorização para esta consulta/),
    ).toBeTruthy();
    expect(screen.queryByText(/Sessão expirada/)).toBeNull();
    expect(screen.queryAllByText("Posição histórica indisponível")).toHaveLength(0);
  });

  it("resposta tardia da geração anterior não republica o valor", async () => {
    const pending: Array<(value: unknown) => void> = [];
    p3Mock.mockImplementation(
      () =>
        new Promise((resolve) => {
          pending.push(resolve);
        }),
    );
    matrixMock.mockResolvedValue({ period: PERIOD, reports: [] });
    summaryMock.mockResolvedValue({
      report: "financial_settlements_summary",
      period: { start_date: `${PERIOD}-01`, end_date: `${PERIOD}-31` },
      status: "available",
      officialTotals: false,
      quality: { missingDocumentCount: 0, missingNatureCount: 0, unresolvedBranchCount: 0 },
      groups: [],
    });
    stockMock.mockResolvedValue({
      status: "available",
      historicalTotal: "10.00",
      officialP7: false,
      parityStatus: "PENDING",
      pagination: { page: 1, page_size: 25, total_items: 0, total_pages: 0 },
      items: [],
      summariesByType: [],
      summariesByWarehouse: [],
      branchesAvailable: [],
      branchesMissing: [],
    });
    reconMock.mockResolvedValue({
      eligibility: "ELIGIBLE",
      ineligibleOperands: [],
      operands: {
        entradasSaidas: { status: "AVAILABLE", value: "1.00" },
        p7: { status: "AVAILABLE", value: "1.00" },
        h02: { status: "AVAILABLE", value: "1.00" },
      },
      divergenceCents: null,
      parity: "MATCH",
    });
    const view = render(
      <ControllershipQueryProvider getAccessToken={() => token("user-1")}>
        <MonthlyReportsPanel
          period={PERIOD}
          selectedReport={null}
          onOpenReport={vi.fn()}
          reportHref={(key) => key}
        />
      </ControllershipQueryProvider>,
    );
    await waitFor(() => expect(pending).toHaveLength(1));
    view.rerender(
      <ControllershipQueryProvider getAccessToken={() => token("user-2")}>
        <MonthlyReportsPanel
          period={PERIOD}
          selectedReport={null}
          onOpenReport={vi.fn()}
          reportHref={(key) => key}
        />
      </ControllershipQueryProvider>,
    );
    await waitFor(() => expect(pending.length).toBeGreaterThanOrEqual(2));
    await act(async () => {
      pending[0]?.({
        period: PERIOD,
        state: "READY_TO_CLOSE",
        canonical_stock_state: "OPEN",
        cutoff: null,
        reconciliations: [
          {
            domain: "P7",
            source_state: "AVAILABLE",
            expected_amount: "100.00",
            reported_amount: "424242.42",
            divergence: "424142.42",
            fetched_at: "2026-10-31T12:00:00Z",
          },
        ],
        last_revalidation: null,
        revalidation_valid: true,
        input_fingerprint: "old-user",
        blockers: [],
      });
    });
    expect(screen.queryByText(/424\.242,42/)).toBeNull();
    expect(screen.queryByText(/424\.142,42/)).toBeNull();
  });
});

describe("invalidação direcionada", () => {
  it("escrita sem entidade não marca a consulta como obsoleta", async () => {
    readyMocks();
    renderPanel();
    await screen.findByText("Relatórios para análise");
    invalidateP3(PERIOD);
    invalidateReportMatrix(PERIOD);
    await waitFor(() => expect(p3Mock).toHaveBeenCalledTimes(2));
    expect(matrixMock).toHaveBeenCalledTimes(2);
    expect(summaryMock).toHaveBeenCalledTimes(1);
    expect(stockMock).toHaveBeenCalledTimes(1);
    expect(reconMock).toHaveBeenCalledTimes(1);
  });
});
