import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@delpi/plugin-ui/index", async () => await import("../../test/pluginUiMock"));

const cockpitMock = vi.fn();
const listCompetencesMock = vi.fn();
const getCompetenceMock = vi.fn();
const openCompetenceMock = vi.fn();

vi.mock("../../api/packagesApi", () => ({
  getClosingCockpit: (...args: unknown[]) => cockpitMock(...args),
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
      blocking_reasons: ["Package FISCAL not submitted"],
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
const OPEN_COMPETENCE = { period: "2026-10", status: "OPEN" };

function setLocation(path = `${BASE}/closing/monthly-closing`) {
  window.history.pushState(null, "", path);
}

function mockOpenMonth() {
  cockpitMock.mockResolvedValue(cockpit());
  getCompetenceMock.mockResolvedValue(OPEN_COMPETENCE);
}

function mockClosedMonth() {
  cockpitMock.mockRejectedValue(NOT_OPENED);
  getCompetenceMock.mockRejectedValue(NOT_OPENED);
}

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

    await screen.findByText("Competências abertas");
    fireEvent.click(screen.getByRole("button", { name: /10\/2026/ }));
    expect(window.location.pathname).toBe(
      `${BASE}/closing/monthly-closing/2026-10`,
    );
  });

  it("lista vazia exibe estado honesto e orienta a consulta por mês", async () => {
    setLocation();
    listCompetencesMock.mockResolvedValue([]);
    render(<MonthlyClosingPage basePath={BASE} />);
    await screen.findByText(/Nenhuma competência aberta ainda/);
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

    await screen.findByText(/ainda não tem competência aberta/);
    expect(
      screen.getByRole("button", { name: "Abrir competência" }),
    ).toBeTruthy();
  });

  it("documentos não oferece uploader sem competência aberta", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-09?tab=documents`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockClosedMonth();
    render(<MonthlyClosingPage basePath={BASE} period="2026-09" />);

    await screen.findByText(/ainda não tem competência aberta/);
    expect(screen.queryByTestId("documents-panel")).toBeNull();
    expect(
      screen.getByRole("button", { name: "Abrir competência" }),
    ).toBeTruthy();
  });

  it("relatórios explicam a dependência sem fingir dado", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-09?tab=reports`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockClosedMonth();
    render(<MonthlyClosingPage basePath={BASE} period="2026-09" />);

    await screen.findByText(/ainda não tem competência aberta/);
    expect(screen.queryByTestId("reports-panel")).toBeNull();
  });

  it("abrir competência chama o contrato real e recarrega o mês", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-09`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockClosedMonth();
    openCompetenceMock.mockResolvedValue(OPEN_COMPETENCE);
    render(<MonthlyClosingPage basePath={BASE} period="2026-09" />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Abrir competência" }),
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
      await screen.findByRole("button", { name: "Abrir competência" }),
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
    await screen.findByText("Fechamento mensal concluído");

    resolveA(cockpit("2026-10"));
    await waitFor(() => expect(cockpitMock).toHaveBeenCalledTimes(2));
    expect(screen.queryByText("Package FISCAL not submitted")).toBeNull();
    expect(
      screen.getByRole("button", { name: "Documentos a tratar: —" }),
    ).toBeTruthy();
  });

  it("mês sem abertura no novo período não preserva dados do anterior", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    getCompetenceMock.mockResolvedValue(OPEN_COMPETENCE);
    cockpitMock.mockImplementation((p: string) =>
      p === "2026-10" ? Promise.resolve(cockpit()) : Promise.reject(NOT_OPENED),
    );
    const { rerender } = render(
      <MonthlyClosingPage basePath={BASE} period="2026-10" />,
    );
    await screen.findByText("Package FISCAL not submitted");

    rerender(<MonthlyClosingPage basePath={BASE} period="2026-11" />);

    await screen.findByText(/ainda não tem competência aberta/);
    expect(screen.queryByText("Package FISCAL not submitted")).toBeNull();
    expect(
      screen.getByRole("button", { name: "Documentos a tratar: —" }),
    ).toBeTruthy();
  });
});

describe("período e aba preservados na URL", () => {
  it("troca de aba mantém /YYYY-MM no path", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockOpenMonth();
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);
    await screen.findByText("Conclusão mensal");

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
      screen.getByRole("button", { name: "Abrir checklist da competência" }),
    ).toBeTruthy();
  });

  it("indicador clicável abre a aba correspondente mantendo período", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    mockOpenMonth();
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);
    await screen.findByText("Conclusão mensal");

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
