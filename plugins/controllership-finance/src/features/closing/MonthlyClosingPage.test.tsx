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

vi.mock("../../api/packagesApi", () => ({
  getClosingCockpit: (...args: unknown[]) => cockpitMock(...args),
}));

vi.mock("../../api/competencesApi", () => ({
  listCompetences: (...args: unknown[]) => listCompetencesMock(...args),
  getCompetence: (...args: unknown[]) => getCompetenceMock(...args),
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

function setLocation(path = `${BASE}/closing/monthly-closing`) {
  window.history.pushState(null, "", path);
}

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  setLocation();
});

describe("RW01 — seletor somente com competências existentes/autorizadas", () => {
  it("popula o select apenas com o que a BFF retorna (MM/AAAA)", async () => {
    setLocation();
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    cockpitMock.mockResolvedValue(cockpit());
    render(<MonthlyClosingPage basePath={BASE} />);

    await waitFor(() =>
      expect(listCompetencesMock).toHaveBeenCalledTimes(1),
    );
    const select = screen.getByLabelText("Competência");
    const options = Array.from(select.querySelectorAll("option"))
      .filter((o) => o.getAttribute("value") !== "")
      .map((o) => `${o.getAttribute("value")}|${o.textContent}`);
    expect(options).toEqual(["2026-11|11/2026", "2026-10|10/2026"]);
    // Nenhum input type=month arbitrário.
    expect(document.querySelector('input[type="month"]')).toBeNull();
  });

  it("landing sem competência na URL lista competências reais", async () => {
    setLocation();
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    render(<MonthlyClosingPage basePath={BASE} />);

    await screen.findByText("Competências disponíveis");
    fireEvent.click(screen.getByRole("button", { name: /10\/2026/ }));
    expect(window.location.pathname).toBe(
      `${BASE}/closing/monthly-closing/2026-10`,
    );
  });

  it("lista vazia exibe estado honesto, nunca inventa competência", async () => {
    setLocation();
    listCompetencesMock.mockResolvedValue([]);
    render(<MonthlyClosingPage basePath={BASE} />);
    await screen.findByText(
      "Nenhuma competência aberta e autorizada para o seu perfil.",
    );
  });
});

describe("RW02 — isolamento de dados por competência", () => {
  it("resposta fora de ordem nunca mostra dados de A sob período B", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    let resolveA: (v: unknown) => void = () => {};
    const slowA = new Promise((resolve) => {
      resolveA = resolve;
    });
    cockpitMock.mockImplementation((p: string) =>
      p === "2026-10" ? slowA : Promise.resolve(cockpit("2026-11", {
        closing: {
          period: "2026-11",
          state: "MONTHLY_CLOSING_COMPLETED",
          blocking_reasons: [],
          packages: [],
          terminal_rejection: null,
        },
        checklist: { EXPECTED: 2 },
      })),
    );
    const { rerender } = render(
      <MonthlyClosingPage basePath={BASE} period="2026-10" />,
    );

    // Muda para B antes de A resolver.
    rerender(<MonthlyClosingPage basePath={BASE} period="2026-11" />);
    await screen.findByText("Fechamento mensal concluído");

    // A resolve tarde demais — não deve aparecer.
    resolveA(cockpit("2026-10"));
    await waitFor(() => expect(cockpitMock).toHaveBeenCalledTimes(2));
    expect(screen.queryByText("Package FISCAL not submitted")).toBeNull();
    expect(
      screen.getByRole("button", { name: "Documentos a tratar: —" }),
    ).toBeTruthy();
  });

  it("erro no novo período não preserva dados do anterior", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    cockpitMock.mockImplementation((p: string) =>
      p === "2026-10"
        ? Promise.resolve(cockpit())
        : Promise.reject(
            new ApiError(404, "not found", "competence_not_opened"),
          ),
    );
    const { rerender } = render(
      <MonthlyClosingPage basePath={BASE} period="2026-10" />,
    );
    await screen.findByText("Package FISCAL not submitted");

    rerender(<MonthlyClosingPage basePath={BASE} period="2026-11" />);

    // O erro do novo período aparece; os dados de outubro somem.
    await screen.findByText(/Competência não aberta/);
    expect(screen.queryByText("Package FISCAL not submitted")).toBeNull();
    expect(
      screen.getByRole("button", { name: "Documentos a tratar: —" }),
    ).toBeTruthy();
  });
});

describe("RW03 — período e aba preservados na URL", () => {
  it("troca de aba mantém /YYYY-MM no path", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    cockpitMock.mockResolvedValue(cockpit());
    getCompetenceMock.mockResolvedValue({ period: "2026-10", status: "OPEN" });
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

  it("troca de competência pelo seletor preserva a aba corrente", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10?tab=reports`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    cockpitMock.mockResolvedValue(cockpit());
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);
    await screen.findByTestId("reports-panel");

    fireEvent.change(screen.getByLabelText("Competência"), {
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
    cockpitMock.mockResolvedValue(cockpit());
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);
    await waitFor(() =>
      expect(screen.getByTestId("reports-panel").textContent).toBe(
        "reports:2026-10",
      ),
    );
  });
});

describe("RW04/RW05 — indicadores honestos e gate documental", () => {
  it("Documentos a tratar fica indisponível sem contrato P2", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    cockpitMock.mockResolvedValue(cockpit());
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);
    await screen.findByText("contagem aguardando contrato do owner P2");
    expect(
      screen.getByRole("button", { name: "Documentos a tratar: —" }),
    ).toBeTruthy();
  });

  it("sem competência aberta, upload documental não é oferecido", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10?tab=documents`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    cockpitMock.mockRejectedValue(
      new ApiError(404, "not found", "competence_not_opened"),
    );
    getCompetenceMock.mockRejectedValue(
      new ApiError(404, "not found", "competence_not_found"),
    );
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);

    await waitFor(() =>
      expect(
        screen.getByText(/não está aberta ou não está acessível/),
      ).toBeTruthy(),
    );
    expect(screen.queryByTestId("documents-panel")).toBeNull();
  });

  it("competência válida libera o painel P2 real", async () => {
    setLocation(`${BASE}/closing/monthly-closing/2026-10?tab=documents`);
    listCompetencesMock.mockResolvedValue(COMPETENCES);
    cockpitMock.mockResolvedValue(cockpit());
    getCompetenceMock.mockResolvedValue({ period: "2026-10", status: "OPEN" });
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
    cockpitMock.mockResolvedValue(cockpit());
    getCompetenceMock.mockResolvedValue({ period: "2026-10", status: "OPEN" });
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
