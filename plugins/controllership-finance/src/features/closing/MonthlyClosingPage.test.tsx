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

vi.mock("./ClosingDocumentsPanel", () => ({
  ClosingDocumentsPanel: ({ period }: { period: string }) => (
    <div data-testid="documents-panel">documents:{period}</div>
  ),
}));

vi.mock("./ReportsMatrixPanel", () => ({
  ReportsMatrixPanel: ({ period }: { period: string }) => (
    <div data-testid="reports-panel">reports:{period}</div>
  ),
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

  it("relatórios explicam a dependência sem fingir dado", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-09?tab=reports`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockClosedMonth();
    render(<MonthlyClosingPage basePath={BASE} period="2026-09" />);

    await screen.findByText(/ainda não foi aberto/);
    expect(screen.queryByTestId("reports-panel")).toBeNull();
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
      screen.queryByText(/Pacote de FISCAL ainda não enviado/),
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
    await screen.findByText(/Pacote de FISCAL ainda não enviado/);

    rerender(<MonthlyClosingPage basePath={BASE} period="2026-11" />);

    await screen.findByText(/ainda não foi aberto/);
    expect(
      screen.queryByText(/Pacote de FISCAL ainda não enviado/),
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
    await screen.findByText("Conclusão da etapa da Controladoria");

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
      expect(screen.getByTestId("reports-panel").textContent).toBe(
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
    await screen.findByText("contagem aguardando contrato do owner P2");
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
    expect(
      screen.getByRole("button", { name: "Abrir checklist do fechamento" }),
    ).toBeTruthy();
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
});

describe("Visão geral V0.2 — atenção traduzida, eixos e conclusão/envio", () => {
  it("traduz códigos técnicos de blocking_reasons para PT-BR", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockOpenMonth();
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);

    await screen.findByText(
      "Pacote de FISCAL ainda não enviado para revisão",
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
      "Fonte P7 indisponível — não foi possível verificar a conciliação",
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Ver relatórios" }),
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

    await screen.findByText("Estoque");
    expect(screen.getByText("Documentos")).toBeTruthy();
    expect(screen.getByText("Pacote DRE")).toBeTruthy();
    expect(screen.getByText(/Cutoff:/)).toBeTruthy();
    expect(screen.getByText(/8 aguardando evidência/)).toBeTruthy();
    expect(
      screen.getByText("Nenhum pacote aplicável neste mês."),
    ).toBeTruthy();
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

    await screen.findByText(/Sem exigências cadastradas/);
    expect(
      screen.getAllByText(/sem checklist publicado/).length,
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
      "Nenhuma atividade registrada para esta competência.",
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
    await screen.findByText("Cutoff confirmado");
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

    await screen.findByText("Conclusão da etapa da Controladoria");
    expect(screen.getByText("Envio do pacote documental")).toBeTruthy();
    expect(
      screen.getByText(/condição\(ões\) impeditiva/),
    ).toBeTruthy();

    fireEvent.click(
      screen.getByRole("button", { name: "Gerenciar pacotes" }),
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
        "Nenhuma pendência identificada neste fechamento.",
      ),
    ).toBeTruthy();
  });

  it("pendências P4 e checklist geram itens de atenção reais", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockOpenMonth();
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);

    await screen.findByText("2 pendência(s) em aberto");
    expect(
      screen.getByText("8 item(ns) do checklist aguardando evidência"),
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
      screen.getByRole("button", { name: "Bloqueios: 1" }),
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
});
