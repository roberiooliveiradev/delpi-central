import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
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
const reconMock = vi.fn();

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

vi.mock("../../api/stockReconciliationApi", () => ({
  getStockReconciliation: (...args: unknown[]) => reconMock(...args),
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
    operational_view: "financial-settlements",
    official_parity: "PENDING",
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

function operand(
  value: string | null,
  overrides: Record<string, unknown> = {},
) {
  return {
    available: value !== null,
    status: value !== null ? "AVAILABLE" : "SOURCE_MISSING",
    errorCode: null,
    value,
    dataAsOf: "2026-10-31T23:59:59Z",
    parityStatus: "PENDING",
    ...overrides,
  };
}

function reconPayload(
  overrides: Record<string, unknown> = {},
) {
  return {
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
      entradasSaidas: operand("3890247.18"),
      p7: operand("3776994.69"),
      h02: operand("64591.71"),
    },
    components: {},
    divergence: "48660.78",
    divergenceCents: "48660.78",
    parity: "DIVERGENCE",
    parityTolerance: "NONE",
    provenance: {},
    parityNotes: [],
    ...overrides,
  };
}

function mockAllReady() {
  p3Mock.mockResolvedValue(p3State());
  matrixMock.mockResolvedValue(matrix());
  summaryMock.mockResolvedValue(summary());
  stockMock.mockResolvedValue(stock());
  reconMock.mockResolvedValue(
    reconPayload({
      divergence: "0.00",
      divergenceCents: "0.00",
      parity: "IDENTITY_ONLY",
    }),
  );
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
    expect(
      screen.getAllByText("Entradas e saídas (R05)").length,
    ).toBeGreaterThan(0);
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
    expect(
      screen.getAllByText("Posição de estoque P7 (R03)").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText(
        /Consulta disponível\. Validação para conciliação formal pendente/,
      ),
    ).toBeTruthy();
    // Com a conciliação P7 pendente de validação, o indicador não
    // pode declarar zero verificado — mostra «—» (não verificadas).
    expect(
      screen.getByRole("button", {
        name: /Divergências identificadas: —/,
      }),
    ).toBeTruthy();
    expect(screen.getByText(/Não verificadas/)).toBeTruthy();
  });

  it("R05 com consulta disponível e P3 sem registro mostra conciliação pendente", async () => {
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

    await screen.findByText("Conciliação pendente");
    expect(
      screen.getAllByText("Entradas e saídas (R05)").length,
    ).toBeGreaterThan(0);
    // Cartão exibe mensagem objetiva; explicação completa e
    // proveniência ficam em «Ver detalhes».
    const card = screen
      .getByText(
        /Consulta disponível\. Validação para conciliação formal pendente/,
      )
      .closest(".cf-attention-item");
    expect(card).toBeTruthy();
    fireEvent.click(
      within(card as HTMLElement).getByRole("button", {
        name: "Ver detalhes",
      }),
    );
    expect(
      await within(card as HTMLElement).findByText(
        /ainda não existe fonte registrada e validada/,
      ),
    ).toBeTruthy();
  });

  it("R08 com consulta disponível e P3 sem registro mostra conciliação pendente", async () => {
    p3Mock.mockResolvedValue(
      p3State([
        recon("ENTRADAS_SAIDAS"),
        recon("P7"),
        recon("H02", {
          source_state: "UNAVAILABLE",
          expected_amount: null,
          reported_amount: null,
          divergence: null,
          fetched_at: null,
        }),
      ]),
    );
    renderPanel();

    await screen.findByText("Conciliação pendente");
    expect(
      screen.getAllByText("Posição H02 (R08)").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText(
        /Consulta disponível\. Validação para conciliação formal pendente/,
      ),
    ).toBeTruthy();
  });

  it("snapshot ausente mostra posição histórica indisponível — não falha técnica", async () => {
    reconMock.mockResolvedValue(
      reconPayload({
        eligibility: "INELIGIBLE",
        ineligibleOperands: ["entradasSaidas"],
        operands: {
          entradasSaidas: operand(null),
          p7: operand("3776994.69"),
          h02: operand("64591.71"),
        },
        divergence: null,
        divergenceCents: null,
        parity: "NOT_COMPUTED",
      }),
    );
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

    await screen.findByText("Sem posição histórica");
    const snapshotCard = screen
      .getByText(
        /Posição histórica ainda não disponível para o mês selecionado/,
      )
      .closest(".cf-attention-item");
    expect(snapshotCard).toBeTruthy();
    // A distinção «não é zero nem falha» permanece — nos detalhes.
    fireEvent.click(
      within(snapshotCard as HTMLElement).getByRole("button", {
        name: "Ver detalhes",
      }),
    );
    expect(
      await within(snapshotCard as HTMLElement).findByText(
        /não é saldo zero nem falha técnica/,
      ),
    ).toBeTruthy();
  });

  it("falha técnica no operando mostra falha ao consultar a fonte", async () => {
    reconMock.mockResolvedValue(
      reconPayload({
        eligibility: "INELIGIBLE",
        ineligibleOperands: ["h02"],
        operands: {
          entradasSaidas: operand("3890247.18"),
          p7: operand("3776994.69"),
          h02: operand(null, { status: "UNAVAILABLE" }),
        },
        divergence: null,
        divergenceCents: null,
        parity: "NOT_COMPUTED",
      }),
    );
    p3Mock.mockResolvedValue(
      p3State([
        recon("ENTRADAS_SAIDAS"),
        recon("P7"),
        recon("H02", {
          source_state: "UNAVAILABLE",
          expected_amount: null,
          reported_amount: null,
          divergence: null,
          fetched_at: null,
        }),
      ]),
    );
    renderPanel();

    await screen.findByText("Falha na fonte");
    expect(
      screen.getAllByText(/Falha ao consultar a fonte/).length,
    ).toBeGreaterThan(0);
    // «Erro técnico na origem» permanece explicado nos detalhes.
    const failCard = screen
      .getAllByText(/Falha ao consultar a fonte/)[0]
      .closest(".cf-attention-item");
    fireEvent.click(
      within(failCard as HTMLElement).getByRole("button", {
        name: "Ver detalhes",
      }),
    );
    expect(
      await within(failCard as HTMLElement).findByText(
        /falhou por erro técnico na origem/,
      ),
    ).toBeTruthy();
  });

  it("domínio P3 nunca registrado sem consulta operacional mantém fonte não registrada", async () => {
    reconMock.mockResolvedValue(
      reconPayload({
        operands: {
          entradasSaidas: operand(null, {
            status: "NO_MATCHING_ITEMS",
          }),
          p7: operand("3776994.69"),
          h02: operand("64591.71"),
        },
      }),
    );
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
    expect(
      screen.getAllByText("Entradas e saídas (R05)").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Fonte da conciliação não registrada/).length,
    ).toBeGreaterThan(0);
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
    expect(
      screen.getAllByText("Posição H02 (R08)").length,
    ).toBeGreaterThan(0);
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

describe("conciliação analítica — superfície independente", () => {
  it("divergência analítica calculada aparece na seção e na atenção", async () => {
    reconMock.mockResolvedValue(reconPayload());
    renderPanel();

    await screen.findByText("Divergência analítica");
    expect(
      screen.getAllByText(/48\.660,78/).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/nem substitui a conciliação governada/)
        .length,
    ).toBeGreaterThan(0);
    // A divergência analítica também entra na área de atenção.
    expect(
      screen.getByRole("button", {
        name: /Divergências identificadas: 1/,
      }),
    ).toBeTruthy();
  });

  it("operando ausente torna a conciliação inelegível — nunca zero", async () => {
    reconMock.mockResolvedValue(
      reconPayload({
        eligibility: "INELIGIBLE",
        ineligibleOperands: ["h02"],
        operands: {
          entradasSaidas: operand("3890247.18"),
          p7: operand("3776994.69"),
          h02: operand(null),
        },
        divergence: null,
        divergenceCents: null,
        parity: "NOT_COMPUTED",
      }),
    );
    renderPanel();

    await screen.findByText("Conciliação pendente de validação");
    expect(
      screen.getAllByText(/Operandos indisponíveis/).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/fonte ausente nunca entra como zero/).length,
    ).toBeGreaterThan(0);
    // Nenhuma divergência analítica é declarada — e a contagem não
    // pode ser zero verificado enquanto houver operando pendente.
    expect(
      screen.getByRole("button", {
        name: /Divergências identificadas: —/,
      }),
    ).toBeTruthy();
  });

  it("falha da conciliação analítica não é ausência de divergência", async () => {
    reconMock.mockRejectedValue(new ApiError(502, "falha upstream"));
    renderPanel();

    const messages = await screen.findAllByText(
      /não é uma divergência zero/,
    );
    expect(messages.length).toBeGreaterThan(0);
    expect(
      screen.getByRole("button", {
        name: /Divergências identificadas: —/,
      }),
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
    expect(onOpen).toHaveBeenCalledWith("stock-inventory");
  });

  it("cartão abre a página do relatório via callback", async () => {
    const onOpen = vi.fn();
    renderPanel({ onOpenReport: onOpen });

    await screen.findByText("Relatórios para análise");
    fireEvent.click(
      screen.getByRole("button", { name: /Baixas financeiras/ }),
    );
    expect(onOpen).toHaveBeenCalledWith("financial-settlements");

    fireEvent.click(
      screen.getByRole("button", { name: /Estoque histórico — P7/ }),
    );
    expect(onOpen).toHaveBeenCalledWith("stock-inventory");

    fireEvent.click(
      screen.getByRole("button", { name: /Entradas e saídas — R05/ }),
    );
    expect(onOpen).toHaveBeenCalledWith("stock-movements");

    fireEvent.click(
      screen.getByRole("button", {
        name: /Despesas por centro de custo — R10/,
      }),
    );
    expect(onOpen).toHaveBeenCalledWith("cost-center-expenses");

    fireEvent.click(
      screen.getByRole("button", {
        name: /Notas fiscais a desconsiderar — R11/,
      }),
    );
    expect(onOpen).toHaveBeenCalledWith("billing-exclusion-roster");

    fireEvent.click(
      screen.getByRole("button", { name: /Material em processo — R08/ }),
    );
    expect(onOpen).toHaveBeenCalledWith("work-in-process");
  });

  it("cartões compactos não repetem rótulos de campos", async () => {
    renderPanel();

    await screen.findByText("Relatórios para análise");
    expect(screen.queryByText("RELATÓRIO")).toBeNull();
    expect(screen.queryByText("DESCRIÇÃO")).toBeNull();
    expect(screen.getAllByText("Disponível").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Abrir relatório").length).toBe(8);
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

  it("matriz separa consulta implementada, paridade e cobertura", async () => {
    matrixMock.mockResolvedValue(
      matrix({
        reports: [
          matrixEntry({
            report_id: "R05",
            label: "Entradas/Saídas",
            operational_view: "stock-movements",
            official_parity: "PENDING",
          }),
          matrixEntry({
            report_id: "R04",
            label: "Consumo por OP",
            source_kind: "PENDING_CONTRACT",
            owner: null,
            operational_view: null,
            official_parity: null,
            checklist_items: 0,
            items_validated: 0,
            items_terminal: 0,
            items_pending: 0,
            coverage: "pending",
          }),
        ],
      }),
    );
    renderPanel();

    await screen.findByText(/Cobertura da matriz R01–R15/);
    const table = screen.getByRole("table", {
      name: "Matriz R01–R15",
    });
    expect(
      within(table).getByRole("columnheader", { name: "Consulta" }),
    ).toBeTruthy();
    expect(
      within(table).getByRole("columnheader", {
        name: "Paridade oficial",
      }),
    ).toBeTruthy();
    // R05: consulta implementada + paridade pendente — dimensões
    // separadas, sem promover a consulta a relatório oficial.
    expect(within(table).getByText("Implementada")).toBeTruthy();
    expect(within(table).getByText("Paridade pendente")).toBeTruthy();
    // R04 sem contrato: nenhuma dimensão inventada.
    const r04Row = within(table)
      .getByText("Consumo por OP")
      .closest("tr");
    expect(r04Row?.textContent).toContain("Contrato pendente");
  });

  it("colunas da matriz explicam consulta, paridade e cobertura", async () => {
    renderPanel();

    await screen.findByText(/Cobertura da matriz R01–R15/);
    const table = screen.getByRole("table", {
      name: "Matriz R01–R15",
    });
    const headerHint = (name: string) =>
      within(table)
        .getByRole("columnheader", { name })
        .querySelector("[data-hint]")
        ?.getAttribute("data-hint");

    expect(headerHint("Consulta")).toContain("consulta operacional");
    expect(headerHint("Paridade oficial")).toContain("emissão oficial");
    expect(headerHint("Cobertura")).toContain("catálogo");
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
