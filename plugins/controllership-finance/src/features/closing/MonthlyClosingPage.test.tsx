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

const cockpitMock = vi.fn();
const listCompetencesMock = vi.fn();
const getCompetenceMock = vi.fn();
const openCompetenceMock = vi.fn();
const listP3EventsMock = vi.fn();

vi.mock("../../api/packagesApi", () => ({
  getClosingCockpit: (...args: unknown[]) => cockpitMock(...args),
}));

vi.mock("../../api/p3Api", () => ({
  listP3Events: (...args: unknown[]) => listP3EventsMock(...args),
}));

vi.mock("../../api/competencesApi", () => ({
  listCompetences: (...args: unknown[]) => listCompetencesMock(...args),
  getCompetence: (...args: unknown[]) => getCompetenceMock(...args),
  openCompetence: (...args: unknown[]) => openCompetenceMock(...args),
}));

vi.mock("./MonthlyDocumentsPanel", () => ({
  MonthlyDocumentsPanel: ({ period }: { period: string }) => (
    <div data-testid="documents-panel">documents:{period}</div>
  ),
}));

vi.mock("./DocumentDetailPanel", () => ({
  DocumentDetailPanel: ({
    documentRef,
  }: {
    documentRef: string;
  }) => <div data-testid="document-detail">detail:{documentRef}</div>,
}));

vi.mock("./MonthlyReportsPanel", () => ({
  MonthlyReportsPanel: ({
    period,
    onOpenReport,
  }: {
    period: string;
    onOpenReport?: (family: string) => void;
  }) => (
    <div data-testid="reports-panel">
      reports:{period}
      <button onClick={() => onOpenReport?.("settlements")}>
        open-report
      </button>
      <button onClick={() => onOpenReport?.("stock")}>open-stock</button>
    </div>
  ),
}));

vi.mock("./MonthlyReportPage", () => ({
  MonthlyReportPage: ({
    period,
    reportKey,
    onBack,
  }: {
    period: string;
    reportKey: string;
    onBack: () => void;
  }) => (
    <div data-testid="report-page">
      report:{reportKey}:{period}
      <button onClick={onBack}>report-back</button>
    </div>
  ),
  FAMILY_TO_REPORT_KEY: {
    settlements: "financial-settlements",
    stock: "stock-inventory",
  },
  REPORT_KEY_TO_FAMILY: {
    "financial-settlements": "settlements",
    "stock-inventory": "stock",
  },
  REPORT_KEY_LABELS: {
    "financial-settlements": "Baixas financeiras",
    "stock-inventory": "Estoque e conciliação",
  },
  isReportKey: (value: string | undefined) =>
    value === "financial-settlements" || value === "stock-inventory",
}));

import { ApiError } from "../../api/httpClient";
import { MonthlyClosingPage } from "./MonthlyClosingPage";

const BASE = "/apps/controllership-finance";

function cockpit(period = "2026-10", overrides: Record<string, unknown> = {}) {
  return {
    period,
    checklist: { EXPECTED: 8, ACCEPTED: 4, NOT_APPLICABLE: 1 },
    p3: {
      cutoff_confirmed: true,
      domains: [
        {
          domain: "AP",
          source_state: "AVAILABLE",
          provenance_kind: "OFFICIAL",
          divergence: "0.00",
        },
        {
          domain: "AR",
          source_state: "UNAVAILABLE",
          provenance_kind: null,
          divergence: null,
        },
        {
          domain: "STOCK",
          source_state: "AVAILABLE",
          provenance_kind: "DECLARED",
          divergence: "12.50",
        },
      ],
    },
    p4_pendencies: { OPEN: 2, RESOLVED: 5 },
    closing: {
      period,
      state: "PENDING",
      blocking_reasons: ["package_not_submitted:FISCAL"],
      packages: [],
      terminal_rejection: null,
    },
    ...overrides,
  };
}

const COMPETENCES = [
  {
    competence_id: "c-oct",
    period: "2026-10",
    template_version_id: "tv1",
    status: "OPEN",
    opened_at: "2026-10-01T00:00:00Z",
    item_count: 10,
  },
  {
    competence_id: "c-nov",
    period: "2026-11",
    template_version_id: "tv1",
    status: "OPEN",
    opened_at: "2026-11-01T00:00:00Z",
    item_count: 12,
  },
];

const NOT_OPENED = new ApiError(404, "not found", "competence_not_opened");
const OPEN_COMPETENCE = {
  competence_id: "c-oct",
  period: "2026-10",
  template_version_id: "tv1",
  status: "OPEN",
  opened_at: "2026-10-01T00:00:00Z",
  item_count: 10,
};

function setLocation(path = `${BASE}/closing/monthly-closing`) {
  window.history.pushState(null, "", path);
}

function mockOpenMonth() {
  cockpitMock.mockResolvedValue(cockpit());
  getCompetenceMock.mockResolvedValue(OPEN_COMPETENCE);
  listP3EventsMock.mockResolvedValue([]);
}

function mockClosedMonth() {
  cockpitMock.mockRejectedValue(NOT_OPENED);
  getCompetenceMock.mockRejectedValue(NOT_OPENED);
}

beforeEach(() => {
  listP3EventsMock.mockResolvedValue([]);
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  setLocation();
});

describe("mês de referência — seleção livre e landing honesta", () => {
  it("oferece input de mês sem competência pré-selecionada", async () => {
    setLocation();
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    render(<MonthlyClosingPage basePath={BASE} />);

    const input = screen.getByLabelText("Mês de referência");
    expect(input).toHaveProperty("type", "month");
    expect(input).toHaveProperty("value", "");
    // Nenhuma chamada de cockpit sem mês selecionado.
    expect(cockpitMock).not.toHaveBeenCalled();
    // A abertura NUNCA é disparada pela seleção.
    expect(openCompetenceMock).not.toHaveBeenCalled();
  });

  it("landing lista competências abertas reais como atalho", async () => {
    setLocation();
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    render(<MonthlyClosingPage basePath={BASE} />);

    await screen.findByText("Fechamentos abertos");
    fireEvent.click(screen.getByRole("button", { name: /10\/2026/ }));
    expect(window.location.pathname).toBe(
      `${BASE}/closing/monthly-closing/2026-10`,
    );
  });

  it("lista vazia exibe estado honesto e orienta a consulta por mês", async () => {
    setLocation();
    listCompetencesMock.mockResolvedValue([]);
    render(<MonthlyClosingPage basePath={BASE} />);
    await screen.findByText(/Nenhum fechamento aberto ainda/);
    expect(screen.getByLabelText("Mês de referência")).toBeTruthy();
  });

  it("selecionar mês navega para o período sem abrir competência", async () => {
    setLocation();
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    render(<MonthlyClosingPage basePath={BASE} />);

    fireEvent.change(screen.getByLabelText("Mês de referência"), {
      target: { value: "2026-09" },
    });
    expect(window.location.pathname).toBe(
      `${BASE}/closing/monthly-closing/2026-09`,
    );
    expect(openCompetenceMock).not.toHaveBeenCalled();
  });
});

describe("mês sem competência aberta — consulta possível, estados honestos", () => {
  it("visão geral explica e oferece abertura autorizada", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-09`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockClosedMonth();
    render(<MonthlyClosingPage basePath={BASE} period="2026-09" />);

    await screen.findByText(/ainda não foi aberto/);
    expect(
      screen.getByRole("button", { name: "Abrir fechamento" }),
    ).toBeTruthy();
  });

  it("documentos não oferece uploader sem competência aberta", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-09?tab=documents`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockClosedMonth();
    render(<MonthlyClosingPage basePath={BASE} period="2026-09" />);

    await screen.findByText(/ainda não foi aberto/);
    expect(screen.queryByTestId("documents-panel")).toBeNull();
    expect(
      screen.getByRole("button", { name: "Abrir fechamento" }),
    ).toBeTruthy();
  });

  it("relatórios são consultáveis por período mesmo sem competência aberta", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-09?tab=reports`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockClosedMonth();
    render(<MonthlyClosingPage basePath={BASE} period="2026-09" />);

    await screen.findByTestId("reports-panel");
expect(screen.getByTestId("reports-panel").textContent).toContain(
      "reports:2026-09",
    );
  });

  it("abrir competência chama o contrato real e recarrega o mês", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-09`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockClosedMonth();
    openCompetenceMock.mockResolvedValue(OPEN_COMPETENCE);
    render(<MonthlyClosingPage basePath={BASE} period="2026-09" />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Abrir fechamento" }),
    );
    await waitFor(() =>
      expect(openCompetenceMock).toHaveBeenCalledWith("2026-09"),
    );
    // Após abrir, cockpit/probe são recarregados (retry bump).
    await waitFor(() =>
      expect(cockpitMock.mock.calls.length).toBeGreaterThanOrEqual(2),
    );
  });

  it("falha de abertura (sem template publicado) é honesta", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-09`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockClosedMonth();
    openCompetenceMock.mockRejectedValue(
      new ApiError(409, "conflict", "no_published_template"),
    );
    render(<MonthlyClosingPage basePath={BASE} period="2026-09" />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Abrir fechamento" }),
    );
    await screen.findByText(
      /Não existe versão publicada vigente do checklist/,
    );
  });
});

describe("isolamento de dados por mês de referência", () => {
  it("resposta fora de ordem nunca mostra dados de A sob período B", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    getCompetenceMock.mockResolvedValue(OPEN_COMPETENCE);
    let resolveA: (v: unknown) => void = () => {};
    const slowA = new Promise((resolve) => {
      resolveA = resolve;
    });
    cockpitMock.mockImplementation((p: string) =>
      p === "2026-10"
        ? slowA
        : Promise.resolve(
            cockpit("2026-11", {
              closing: {
                period: "2026-11",
                state: "MONTHLY_CLOSING_COMPLETED",
                blocking_reasons: [],
                packages: [],
                terminal_rejection: null,
              },
              checklist: { EXPECTED: 2 },
            }),
          ),
    );
    const { rerender } = render(
      <MonthlyClosingPage basePath={BASE} period="2026-10" />,
    );

    rerender(<MonthlyClosingPage basePath={BASE} period="2026-11" />);
    await screen.findAllByText("Concluído");

    resolveA(cockpit("2026-10"));
    await waitFor(() => expect(cockpitMock).toHaveBeenCalledTimes(2));
    expect(
      screen.queryByText(/Documentos para fiscal ainda não enviados/),
    ).toBeNull();
    expect(
      screen.getByRole("button", { name: "Documentos a tratar: —" }),
    ).toBeTruthy();
  });

  it("mês sem abertura no novo período não preserva dados do anterior", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    getCompetenceMock.mockResolvedValue(OPEN_COMPETENCE);
    listP3EventsMock.mockResolvedValue([]);
    cockpitMock.mockImplementation((p: string) =>
      p === "2026-10" ? Promise.resolve(cockpit()) : Promise.reject(NOT_OPENED),
    );
    const { rerender } = render(
      <MonthlyClosingPage basePath={BASE} period="2026-10" />,
    );
    await screen.findByText(/Documentos para fiscal ainda não enviados/);

    rerender(<MonthlyClosingPage basePath={BASE} period="2026-11" />);

    await screen.findByText(/ainda não foi aberto/);
    expect(
      screen.queryByText(/Documentos para fiscal ainda não enviados/),
    ).toBeNull();
    // Sem competência aberta, a V0.2 não exibe indicadores fabricados.
    expect(screen.queryByText("O que precisa de atenção")).toBeNull();
  });
});

describe("período e aba preservados na URL", () => {
  it("troca de aba mantém /YYYY-MM no path", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockOpenMonth();
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);
    await screen.findByText("Concluir fechamento");

    fireEvent.click(
      screen.getByRole("button", { name: "Documentos e interações" }),
    );
    expect(window.location.pathname).toBe(
      `${BASE}/closing/monthly-closing/2026-10`,
    );
    expect(window.location.search).toContain("tab=documents");

    fireEvent.click(
      screen.getByRole("button", { name: "Relatórios e divergências" }),
    );
    expect(window.location.pathname).toBe(
      `${BASE}/closing/monthly-closing/2026-10`,
    );
    expect(window.location.search).toContain("tab=reports");
  });

  it("troca de mês pelo seletor preserva a aba corrente", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10?tab=reports`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockOpenMonth();
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);
    await screen.findByTestId("reports-panel");

    fireEvent.change(screen.getByLabelText("Mês de referência"), {
      target: { value: "2026-11" },
    });
    expect(window.location.pathname).toBe(
      `${BASE}/closing/monthly-closing/2026-11`,
    );
    expect(window.location.search).toContain("tab=reports");
  });

  it("deep link período+aba abre direto no destino", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10?tab=reports`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockOpenMonth();
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);
    await waitFor(() =>
      expect(screen.getByTestId("reports-panel").textContent).toContain(
        "reports:2026-10",
      ),
    );
  });
});

describe("indicadores honestos e gate documental", () => {
  it("Documentos a tratar fica indisponível sem contrato P2", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockOpenMonth();
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);
    await screen.findByText("contagem ainda não disponível");
    expect(
      screen.getByRole("button", { name: "Documentos a tratar: —" }),
    ).toBeTruthy();
  });

  it("competência válida libera o painel P2 real", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10?tab=documents`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockOpenMonth();
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);

    await waitFor(() =>
      expect(screen.getByTestId("documents-panel").textContent).toBe(
        "documents:2026-10",
      ),
    );
    // Validação item a item acontece no detalhe do documento — a aba não
    // obriga o usuário a sair para o checklist legado.
    expect(
      screen.queryByRole("button", { name: "Abrir checklist do fechamento" }),
    ).toBeNull();
  });

  it("indicador clicável abre a aba correspondente mantendo período", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockOpenMonth();
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);
    await screen.findByText("O que precisa de atenção");

    fireEvent.click(
      screen.getByRole("button", { name: "Documentos a tratar: —" }),
    );
    await waitFor(() =>
      expect(screen.getByTestId("documents-panel")).toBeTruthy(),
    );
    expect(window.location.pathname).toBe(
      `${BASE}/closing/monthly-closing/2026-10`,
    );
  });

  it("deep link de documento abre o detalhe preservando o período", async () => {
    setLocation(
      `${BASE}/closing/monthly-closing/2026-10/documents/item:CK-E-01`,
    );
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockOpenMonth();
    render(
      <MonthlyClosingPage
        basePath={BASE}
        period="2026-10"
        documentRef="item:CK-E-01"
      />,
    );

    await waitFor(() =>
      expect(screen.getByTestId("document-detail").textContent).toBe(
        "detail:item:CK-E-01",
      ),
    );
    // Três abas ficam ocultas no detalhe; caminho mostra o contexto.
    expect(screen.queryByRole("button", { name: "Relatórios e divergências" })).toBeNull();
    expect(screen.getByText("Documentos e interações")).toBeTruthy();
  });
});

describe("Relatórios V0.3 — páginas contextuais de relatório (UX-011)", () => {
  it("cartão do hub navega para a página contextual do relatório", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10?tab=reports`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockOpenMonth();
    const view = render(
      <MonthlyClosingPage basePath={BASE} period="2026-10" />,
    );

    await screen.findByTestId("reports-panel");
    fireEvent.click(screen.getByText("open-report"));

    // O pushState atualiza a URL; o App resolve a rota e injeta reportKey.
    await waitFor(() =>
      expect(window.location.pathname).toBe(
        `${BASE}/closing/monthly-closing/2026-10/reports/financial-settlements`,
      ),
    );
    view.rerender(
      <MonthlyClosingPage
        basePath={BASE}
        period="2026-10"
        reportKey="financial-settlements"
      />,
    );

    await waitFor(() =>
      expect(screen.getByTestId("report-page").textContent).toContain(
        "report:financial-settlements:2026-10",
      ),
    );
  });

  it("voltar restaura aba reports e seleção anterior", async () => {
    setLocation(
      `${BASE}/closing/monthly-closing/2026-10/reports/stock-inventory`,
    );
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockOpenMonth();
    const view = render(
      <MonthlyClosingPage
        basePath={BASE}
        period="2026-10"
        reportKey="stock-inventory"
      />,
    );

    await waitFor(() =>
      expect(
        screen.getByTestId("report-page").textContent,
      ).toContain("report:stock-inventory:2026-10"),
    );

    fireEvent.click(screen.getByText("report-back"));

    await waitFor(() =>
      expect(window.location.search).toContain("report=stock"),
    );
    expect(window.location.search).toContain("tab=reports");
    expect(window.location.pathname).toBe(
      `${BASE}/closing/monthly-closing/2026-10`,
    );

    // App resolve o hub de novo — painel de relatórios volta ao foco.
    view.rerender(
      <MonthlyClosingPage basePath={BASE} period="2026-10" />,
    );
    await waitFor(() =>
      expect(screen.getByTestId("reports-panel")).toBeTruthy(),
    );
  });

  it("deep link de relatório abre a página contextual preservando o período", async () => {
    setLocation(
      `${BASE}/closing/monthly-closing/2026-10/reports/financial-settlements`,
    );
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockOpenMonth();
    render(
      <MonthlyClosingPage
        basePath={BASE}
        period="2026-10"
        reportKey="financial-settlements"
      />,
    );

    await waitFor(() =>
      expect(screen.getByTestId("report-page").textContent).toContain(
        "report:financial-settlements:2026-10",
      ),
    );
    // Abas primárias ocultas; breadcrumb contextual mostra o caminho.
    expect(screen.queryByRole("tablist")).toBeNull();
    expect(screen.getAllByText("Relatórios e divergências").length)
      .toBeGreaterThan(0);
    expect(screen.getByText("Baixas financeiras")).toBeTruthy();
  });

  it("chave de relatório desconhecida cai no estado honesto da página", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10/reports/outra`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockOpenMonth();
    render(
      <MonthlyClosingPage
        basePath={BASE}
        period="2026-10"
        reportKey="outra"
      />,
    );

    await waitFor(() =>
      expect(screen.getByTestId("report-page")).toBeTruthy(),
    );
    expect(
      screen.getByTestId("report-page").textContent,
    ).toContain("report:outra:2026-10");
  });

  it("voltar preserva os filtros da família na URL do hub (RW01)", async () => {
    setLocation(
      `${BASE}/closing/monthly-closing/2026-10/reports/financial-settlements` +
        "?side=receivable&nature=100&page=3",
    );
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockOpenMonth();
    render(
      <MonthlyClosingPage
        basePath={BASE}
        period="2026-10"
        reportKey="financial-settlements"
      />,
    );

    await waitFor(() =>
      expect(screen.getByTestId("report-page")).toBeTruthy(),
    );
    fireEvent.click(screen.getByText("report-back"));

    await waitFor(() =>
      expect(window.location.search).toContain("report=settlements"),
    );
    expect(window.location.search).toContain("tab=reports");
    expect(window.location.search).toContain("side=receivable");
    expect(window.location.search).toContain("nature=100");
    expect(window.location.search).toContain("page=3");
    expect(window.location.pathname).toBe(
      `${BASE}/closing/monthly-closing/2026-10`,
    );
  });

  it("reabrir a última família repassa os filtros preservados (RW01)", async () => {
    setLocation(
      `${BASE}/closing/monthly-closing/2026-10` +
        "?tab=reports&report=stock&branch=01&warehouse=04&page=2",
    );
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockOpenMonth();
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);

    await screen.findByTestId("reports-panel");
    fireEvent.click(screen.getByText("open-stock"));

    await waitFor(() =>
      expect(window.location.pathname).toBe(
        `${BASE}/closing/monthly-closing/2026-10/reports/stock-inventory`,
      ),
    );
    expect(window.location.search).toContain("branch=01");
    expect(window.location.search).toContain("warehouse=04");
    expect(window.location.search).toContain("page=2");
  });

  it("abrir família diferente não carrega filtros da anterior (RW01)", async () => {
    setLocation(
      `${BASE}/closing/monthly-closing/2026-10` +
        "?tab=reports&report=settlements&nature=100&page=3",
    );
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockOpenMonth();
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);

    await screen.findByTestId("reports-panel");
    fireEvent.click(screen.getByText("open-stock"));

    await waitFor(() =>
      expect(window.location.pathname).toBe(
        `${BASE}/closing/monthly-closing/2026-10/reports/stock-inventory`,
      ),
    );
    // Os parâmetros pertencem à família de Baixas — Estoque abre limpo.
    expect(window.location.search).not.toContain("nature");
    expect(window.location.search).not.toContain("page");
  });
});

describe("Visão geral V0.2 — atenção traduzida, eixos e conclusão/envio", () => {
  it("traduz códigos técnicos de blocking_reasons para PT-BR", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockOpenMonth();
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);

    await screen.findByText(
      "Documentos para fiscal ainda não enviados para revisão",
    );
    expect(
      screen.queryByText(/package_not_submitted/),
    ).toBeNull();
  });

  it("fonte P3 indisponível vira mensagem humana e leva a Relatórios", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    cockpitMock.mockResolvedValue(
      cockpit("2026-10", {
        closing: {
          period: "2026-10",
          state: "PENDING",
          blocking_reasons: ["p3_source_unavailable:P7"],
          packages: [],
          terminal_rejection: null,
        },
      }),
    );
    getCompetenceMock.mockResolvedValue(OPEN_COMPETENCE);
    listP3EventsMock.mockResolvedValue([]);
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);

    await screen.findByText(
      "Não foi possível consultar o relatório P7",
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Ver divergências" }),
    );
    await waitFor(() =>
      expect(window.location.search).toContain("tab=reports"),
    );
    expect(window.location.pathname).toBe(
      `${BASE}/closing/monthly-closing/2026-10`,
    );
  });

  it("divergências exibem «—» com fonte indisponível, nunca falso zero", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockOpenMonth();
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);

    await screen.findByText("O que precisa de atenção");
    expect(
      screen.getByRole("button", { name: "Divergências: —" }),
    ).toBeTruthy();
  });

  it("divergências contam domínios reais quando fontes estão disponíveis", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    cockpitMock.mockResolvedValue(
      cockpit("2026-10", {
        p3: {
          cutoff_confirmed: true,
          domains: [
            {
              domain: "P7",
              source_state: "AVAILABLE",
              provenance_kind: "OFFICIAL",
              divergence: "0.00",
            },
            {
              domain: "H02",
              source_state: "AVAILABLE",
              provenance_kind: "OFFICIAL",
              divergence: "12.50",
            },
          ],
        },
      }),
    );
    getCompetenceMock.mockResolvedValue(OPEN_COMPETENCE);
    listP3EventsMock.mockResolvedValue([]);
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);

    await screen.findByText("O que precisa de atenção");
    expect(
      screen.getByRole("button", { name: "Divergências: 1" }),
    ).toBeTruthy();
  });

  it("eixos Estoque, Documentos e Pacote DRE são independentes", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockOpenMonth();
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);

    await screen.findByText("Conferência do estoque");
    expect(screen.getByText("Documentos do mês")).toBeTruthy();
    expect(screen.getByText("Documentos para a Contabilidade")).toBeTruthy();
    expect(
      screen.getByText("Não foi possível consultar 1 de 3 relatórios necessários."),
    ).toBeTruthy();
    expect(screen.getByText(/8 aguardando evidência/)).toBeTruthy();
    expect(
      screen.getAllByText(
        "Não há um conjunto de documentos para envio definido neste mês.",
      ).length,
    ).toBeGreaterThan(0);
  });

  it("checklist vazio (aberto sem template) é estado normal, não erro", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    cockpitMock.mockResolvedValue(
      cockpit("2026-10", { checklist: {} }),
    );
    getCompetenceMock.mockResolvedValue({
      ...OPEN_COMPETENCE,
      template_version_id: null,
    });
    listP3EventsMock.mockResolvedValue([]);
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);

    await screen.findByText(/Nenhum documento exigido para este fechamento/);
    expect(
      screen.getAllByText(/sem lista de documentos definida/).length,
    ).toBeGreaterThanOrEqual(1);
  });

  it("atividade recente mostra somente eventos reais ou estado vazio", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockOpenMonth();
    const { rerender } = render(
      <MonthlyClosingPage basePath={BASE} period="2026-10" />,
    );

    await screen.findByText(
      "Ainda não há atividades registradas nesta conferência.",
    );

    listP3EventsMock.mockResolvedValue([
      {
        event_id: 7,
        event_type: "CUTOFF_CONFIRMED",
        actor_subject: "user-1",
        detail: {},
        created_at: "2026-10-26T10:00:00Z",
      },
    ]);
    rerender(<MonthlyClosingPage basePath={BASE} period="2026-11" />);
    rerender(<MonthlyClosingPage basePath={BASE} period="2026-10" />);
    await screen.findByText("Conferência do mês finalizada");
    expect(screen.getByText(/user-1/)).toBeTruthy();
    expect(listP3EventsMock).toHaveBeenCalledWith(
      "2026-10",
      expect.any(AbortSignal),
    );
  });

  it("conclusão e envio são blocos separados com navegação real", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockOpenMonth();
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);

    await screen.findByText("Concluir fechamento");
    expect(screen.getByText("Enviar documentos à Contabilidade")).toBeTruthy();
    expect(
      screen.getByText(/situação\(ões\) ainda impedem/),
    ).toBeTruthy();

    fireEvent.click(
      screen.getByRole("button", { name: "Gerenciar envio" }),
    );
    expect(window.location.pathname).toBe(
      `${BASE}/closing/packages/2026-10`,
    );
  });

  it("fechamento concluído mostra estado final sem bloqueios", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    cockpitMock.mockResolvedValue(
      cockpit("2026-10", {
        checklist: {},
        p4_pendencies: {},
        closing: {
          period: "2026-10",
          state: "MONTHLY_CLOSING_COMPLETED",
          blocking_reasons: [],
          packages: [],
          terminal_rejection: null,
        },
      }),
    );
    getCompetenceMock.mockResolvedValue(OPEN_COMPETENCE);
    listP3EventsMock.mockResolvedValue([]);
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);

    await screen.findAllByText("Este fechamento está concluído.");
    expect(
      screen.getByText(
        "Nada pendente neste fechamento.",
      ),
    ).toBeTruthy();
  });

  it("pendências P4 e checklist geram itens de atenção reais", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockOpenMonth();
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);

    await screen.findByText("2 pendência(s) aguardando tratamento");
    expect(
      screen.getByText("8 documento(s) aguardando evidência"),
    ).toBeTruthy();

    fireEvent.click(
      screen.getByRole("button", { name: "Ver pendências" }),
    );
    expect(window.location.pathname).toBe(`${BASE}/closing/pendencies`);
  });

  it("seção de atenção recebe foco ao ativar o indicador Bloqueios", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockOpenMonth();
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);

    await screen.findByText("O que precisa de atenção");
    fireEvent.click(
      screen.getByRole("button", { name: "O que falta resolver: 1" }),
    );
    const attention = document.getElementById("cf-monthly-attention");
    expect(attention).toBeTruthy();
    expect(document.activeElement).toBe(attention);
  });

  it("erro de autorização no cockpit permanece fail-closed", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    cockpitMock.mockRejectedValue(
      new ApiError(403, "forbidden", "forbidden"),
    );
    getCompetenceMock.mockRejectedValue(
      new ApiError(403, "forbidden", "forbidden"),
    );
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);

    await screen.findAllByText(
      /Você não tem autorização para consultar/,
    );
    expect(screen.queryByText("O que precisa de atenção")).toBeNull();
  });

  it("expande todas as situações na própria Visão geral", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockOpenMonth();
    cockpitMock.mockResolvedValue(
      cockpit("2026-10", {
        closing: {
          period: "2026-10",
          state: "PENDING",
          blocking_reasons: [
            "p3_cutoff_not_confirmed",
            "p3_source_unavailable:P7",
            "p3_source_unavailable:ENTRADAS_SAIDAS",
            "p3_source_unavailable:H02",
            "no_applicable_packages",
            "package_not_submitted:FISCAL",
          ],
          packages: [],
          terminal_rejection: null,
        },
      }),
    );
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);

    await screen.findByText(/Mostrando 4 de \d+ situações/);
    expect(
      screen.queryByText("Documentos para fiscal ainda não enviados para revisão"),
    ).toBeNull();
    fireEvent.click(
      screen.getByRole("button", { name: /Mostrar todas as \d+ situações/ }),
    );
    expect(
      screen.getByText("Documentos para fiscal ainda não enviados para revisão"),
    ).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Mostrar menos" }));
    expect(
      screen.queryByText("Documentos para fiscal ainda não enviados para revisão"),
    ).toBeNull();
  });

  it("código de bloqueio desconhecido usa mensagem genérica sem código cru", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockOpenMonth();
    cockpitMock.mockResolvedValue(
      cockpit("2026-10", {
        closing: {
          period: "2026-10",
          state: "PENDING",
          blocking_reasons: ["mystery_blocker_xyz"],
          packages: [],
          terminal_rejection: null,
        },
      }),
    );
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);

    await screen.findByText(
      "Existe uma situação pendente que precisa ser verificada",
    );
    expect(screen.queryByText(/mystery_blocker_xyz/)).toBeNull();
  });
});
