import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

vi.mock("@delpi/plugin-ui/index", async () => await import("../../test/pluginUiMock"));

const p3Mock = vi.fn();
const matrixMock = vi.fn();
const summaryMock = vi.fn();
const stockMock = vi.fn();

vi.mock("../../api/p3Api", () => ({
  getP3State: (...args: unknown[]) => p3Mock(...args),
}));

vi.mock("../../api/reportsApi", () => ({
  listReportMatrix: (...args: unknown[]) => matrixMock(...args),
}));

vi.mock("../../api/financialSettlementsApi", () => ({
  getFinancialSettlementsSummary: (...args: unknown[]) =>
    summaryMock(...args),
}));

vi.mock("../../api/stockInventoryApi", () => ({
  getStockInventory: (...args: unknown[]) => stockMock(...args),
}));

import { ApiError } from "../../api/httpClient";
import { MonthlyReportsPanel } from "./MonthlyReportsPanel";

const PERIOD = "2026-10";

function recon(domain: string, overrides: Record<string, unknown> = {}) {
  return {
    domain,
    source_state: "AVAILABLE",
    expected_amount: "1000.00",
    reported_amount: "1000.00",
    divergence: "0.00",
    fetched_at: "2026-10-31T10:00:00Z",
    rule_version: "1",
    provenance: null,
    ...overrides,
  };
}

function p3State(
  reconciliations = [recon("ENTRADAS_SAIDAS"), recon("P7"), recon("H02")],
  overrides: Record<string, unknown> = {},
) {
  return {
    period: PERIOD,
    state: "READY_TO_CLOSE",
    canonical_stock_state: "OPEN",
    cutoff: null,
    reconciliations,
    last_revalidation: null,
    revalidation_valid: true,
    input_fingerprint: "fp",
    blockers: [],
    ...overrides,
  };
}

function matrixEntry(overrides: Record<string, unknown> = {}) {
  return {
    report_id: "R01",
    label: "Baixas a pagar",
    source_kind: "OPERATIONAL_VIEW",
    owner: "TOTVS/SE5",
    operational_view: null,
    note: "",
    checklist_items: 1,
    items_validated: 1,
    items_terminal: 1,
    items_pending: 0,
    coverage: "validated",
    ...overrides,
  };
}

function matrix(overrides: Record<string, unknown> = {}) {
  return { period: PERIOD, reports: [matrixEntry()], ...overrides };
}

function summary(overrides: Record<string, unknown> = {}) {
  return {
    report: "financial_settlements_summary",
    period: { start_date: `${PERIOD}-01`, end_date: `${PERIOD}-31` },
    status: "available",
    officialTotals: true,
    quality: {
      missingDocumentCount: 0,
      missingNatureCount: 0,
      unresolvedBranchCount: 0,
    },
    groups: [
      {
        side: "payable",
        currencyCode: "BRL",
        natureCode: "ALUG",
        natureDescription: "Aluguel",
        movementType: "PAG",
        movementDescription: "Pagamento",
        eventCount: 3,
        totalAmount: "4500.00",
      },
      {
        side: "receivable",
        currencyCode: "BRL",
        natureCode: "VND",
        natureDescription: "Venda",
        movementType: "REC",
        movementDescription: "Recebimento",
        eventCount: 2,
        totalAmount: "8000.00",
      },
    ],
    ...overrides,
  };
}

function stock(overrides: Record<string, unknown> = {}) {
  return {
    report: "stock_inventory",
    period: PERIOD,
    referenceDate: `${PERIOD}-31`,
    dataAsOf: "2026-10-31T23:59:59Z",
    branchCode: "all",
    reportScope: "all_products",
    source: "totvs_sb9",
    officialP7: true,
    parityStatus: "aligned",
    status: "available",
    branchesAvailable: ["01"],
    branchesMissing: [],
    historicalTotal: "123456.78",
    pagination: {
      page: 1,
      page_size: 25,
      total_items: 2,
      total_pages: 1,
      has_next: false,
      has_previous: false,
    },
    items: [],
    summariesByType: [],
    summariesByWarehouse: [],
    ...overrides,
  };
}

function mockAllReady() {
  p3Mock.mockResolvedValue(p3State());
  matrixMock.mockResolvedValue(matrix());
  summaryMock.mockResolvedValue(summary());
  stockMock.mockResolvedValue(stock());
}

function renderPanel(props: Partial<Parameters<typeof MonthlyReportsPanel>[0]> = {}) {
  return render(
    <MonthlyReportsPanel
      period={PERIOD}
      selectedReport={null}
      onOpenReport={vi.fn()}
      {...props}
    />,
  );
}

beforeEach(() => {
  mockAllReady();
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("indicadores e área de atenção", () => {
  it("divergência P3 comprovada aparece com valor, origem e causa honesta", async () => {
    p3Mock.mockResolvedValue(
      p3State([
        recon("ENTRADAS_SAIDAS", {
          expected_amount: "1000.00",
          reported_amount: "1100.00",
          divergence: "100.00",
        }),
        recon("P7"),
        recon("H02"),
      ]),
    );
    renderPanel();

    await screen.findByText("Divergência comprovada");
    expect(screen.getByText("Entradas e saídas (R05)")).toBeTruthy();
    expect(
      screen.getByRole("button", {
        name: /Divergências identificadas: 1/,
      }),
    ).toBeTruthy();

    fireEvent.click(screen.getByText("Ver detalhes"));
    await screen.findByText(/Valor esperado/);
    expect(screen.getByText(/1\.100,00/)).toBeTruthy();
    expect(
      screen.getByText(/A causa ainda não foi identificada/),
    ).toBeTruthy();
  });

  it("P7 com consulta disponível e P3 sem registro mostra conciliação pendente", async () => {
    p3Mock.mockResolvedValue(
      p3State([
        recon("ENTRADAS_SAIDAS"),
        recon("P7", {
          source_state: "UNAVAILABLE",
          expected_amount: null,
          reported_amount: null,
          divergence: null,
          fetched_at: null,
        }),
        recon("H02"),
      ]),
    );
    renderPanel();

    await screen.findByText("Conciliação pendente");
    expect(screen.getByText("Posição de estoque P7 (R03)")).toBeTruthy();
    expect(
      screen.getByText(
        /Consulta disponível — conciliação pendente/,
      ),
    ).toBeTruthy();
    // Indicador de divergências permanece 0 — todas as fontes responderam.
    expect(
      screen.getByRole("button", {
        name: /Divergências identificadas: 0/,
      }),
    ).toBeTruthy();
  });

  it("domínio P3 nunca registrado distingue-se de fonte indisponível", async () => {
    p3Mock.mockResolvedValue(
      p3State([
        recon("ENTRADAS_SAIDAS", {
          source_state: "UNAVAILABLE",
          expected_amount: null,
          reported_amount: null,
          divergence: null,
          fetched_at: null,
        }),
        recon("P7"),
        recon("H02"),
      ]),
    );
    renderPanel();

    await screen.findByText("Fonte não registrada");
    expect(screen.getByText("Entradas e saídas (R05)")).toBeTruthy();
    expect(
      screen.getByText(/Fonte da conciliação não registrada/),
    ).toBeTruthy();
  });

  it("fonte P3 registrada como indisponível mantém estado de indisponível", async () => {
    p3Mock.mockResolvedValue(
      p3State([
        recon("H02", {
          source_state: "UNAVAILABLE",
          expected_amount: null,
          reported_amount: null,
          divergence: null,
          fetched_at: "2026-10-31T10:00:00Z",
        }),
      ]),
    );
    renderPanel();

    await screen.findByText("Fonte indisponível");
    expect(screen.getByText("Posição H02 (R08)")).toBeTruthy();
  });

  it("competência não aberta vira conferência não realizada, não erro", async () => {
    const notOpened = new ApiError(404, "not found", "competence_not_opened");
    p3Mock.mockRejectedValue(notOpened);
    matrixMock.mockRejectedValue(notOpened);
    renderPanel();

    await screen.findByText("Conferência não realizada");
    expect(
      screen.getByText("Conciliação de estoque (P3)"),
    ).toBeTruthy();
    // A matriz permanece acessível como rastreabilidade técnica.
    fireEvent.click(
      screen.getByText(/Cobertura da matriz R01–R15/),
    );
    expect(
      screen.getByText(/a cobertura dos relatórios R01–R15 não foi gerada/),
    ).toBeTruthy();
  });

  it("erro de consulta não é ausência de divergência", async () => {
    summaryMock.mockRejectedValue(new ApiError(500, "falha interna"));
    renderPanel();

    await screen.findByText("Fonte indisponível");
    expect(
      screen.getByRole("button", {
        name: /Divergências identificadas: —/,
      }),
    ).toBeTruthy();
  });

  it("sem divergências nem pendências mostra estado vazio honesto", async () => {
    renderPanel();

    await screen.findByText(
      "Nenhuma divergência ou pendência identificada para este período.",
    );
    expect(
      screen.getByRole("button", {
        name: /Divergências identificadas: 0/,
      }),
    ).toBeTruthy();
  });

  it("inconsistências de vínculo contam como atenção comprovada", async () => {
    summaryMock.mockResolvedValue(
      summary({
        quality: {
          missingDocumentCount: 4,
          missingNatureCount: 0,
          unresolvedBranchCount: 0,
        },
      }),
    );
    renderPanel();

    await screen.findByText("Inconsistência identificada");
    expect(screen.getByText(/4 baixas sem número de documento/)).toBeTruthy();
  });

  it("entregáveis pendentes da matriz viram conferência não realizada", async () => {
    matrixMock.mockResolvedValue(
      matrix({
        reports: [
          matrixEntry({
            report_id: "R05",
            label: "Entradas/Saídas",
            checklist_items: 3,
            items_validated: 1,
            items_pending: 2,
            coverage: "partial",
          }),
        ],
      }),
    );
    renderPanel();

    await screen.findByText("Conferência não realizada");
    expect(
      screen.getByText(/2 de 3 entregáveis aguardando conferência/),
    ).toBeTruthy();
  });
});

describe("catálogo em cartões — navegação contextual", () => {
  it("item de atenção vinculado a família oferece a página contextual", async () => {
    const onOpen = vi.fn();
    p3Mock.mockResolvedValue(
      p3State([
        recon("P7", {
          source_state: "UNAVAILABLE",
          expected_amount: null,
          reported_amount: null,
          divergence: null,
          fetched_at: null,
        }),
      ]),
    );
    renderPanel({ onOpenReport: onOpen });

    await screen.findByText("Conciliação pendente");
    const buttons = screen.getAllByRole("button", {
      name: "Abrir relatório",
    });
    fireEvent.click(buttons[0]);
    expect(onOpen).toHaveBeenCalledWith("stock");
  });

  it("cartão abre a página do relatório via callback", async () => {
    const onOpen = vi.fn();
    renderPanel({ onOpenReport: onOpen });

    await screen.findByText("Relatórios para análise");
    fireEvent.click(
      screen.getByRole("button", { name: /Baixas financeiras/ }),
    );
    expect(onOpen).toHaveBeenCalledWith("settlements");

    fireEvent.click(
      screen.getByRole("button", { name: /Estoque e conciliação/ }),
    );
    expect(onOpen).toHaveBeenCalledWith("stock");
  });

  it("cartões compactos não repetem rótulos de campos", async () => {
    renderPanel();

    await screen.findByText("Relatórios para análise");
    expect(screen.queryByText("RELATÓRIO")).toBeNull();
    expect(screen.queryByText("DESCRIÇÃO")).toBeNull();
    expect(screen.getAllByText("Disponível").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Abrir relatório").length).toBe(2);
  });

  it("matriz R01–R15 fica em rastreabilidade técnica expansível", async () => {
    renderPanel();

    const summary = await screen.findByText(/Cobertura da matriz R01–R15/);
    const details = summary.closest("details");
    expect(details).toBeTruthy();
    // Fechada por padrão — fora do fluxo principal visual.
    expect(details?.hasAttribute("open")).toBe(false);
    // O conteúdo permanece acessível no DOM, colapsado.
    expect(screen.getByText(/Baixas a pagar/)).toBeTruthy();
  });

  it("sem período selecionado pede o mês de referência", async () => {
    renderPanel({ period: "" });
    await screen.findByText(
      "Selecione um mês de referência para consultar os relatórios.",
    );
  });

  it("troca de período refaz as consultas com a nova competência", async () => {
    const view = renderPanel();
    await screen.findByText("Relatórios para análise");

    view.rerender(
      <MonthlyReportsPanel
        period="2026-11"
        selectedReport={null}
        onOpenReport={vi.fn()}
      />,
    );

    await waitFor(() =>
      expect(p3Mock).toHaveBeenCalledWith("2026-11", expect.anything()),
    );
    expect(matrixMock).toHaveBeenCalledWith("2026-11", expect.anything());
    expect(stockMock).toHaveBeenCalledWith(
      expect.objectContaining({ period: "2026-11" }),
      expect.anything(),
    );
    expect(summaryMock).toHaveBeenCalledWith(
      expect.objectContaining({
        startDate: "2026-11-01",
        endDate: "2026-11-30",
      }),
      expect.anything(),
    );
  });
});
