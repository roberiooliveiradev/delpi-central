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

vi.mock("../../api/packagesApi", () => ({
  getClosingCockpit: (...args: unknown[]) => cockpitMock(...args),
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

import { MonthlyClosingPage } from "./MonthlyClosingPage";

const BASE = "/apps/controllership-finance";

function cockpit(overrides: Record<string, unknown> = {}) {
  return {
    period: "2026-10",
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
      period: "2026-10",
      state: "PENDING",
      blocking_reasons: ["Package FISCAL not submitted"],
      packages: [],
      terminal_rejection: null,
    },
    ...overrides,
  };
}

function setLocation(search = "") {
  window.history.pushState(
    null,
    "",
    `${BASE}/closing/monthly-closing${search}`,
  );
}

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  setLocation();
});

describe("MonthlyClosingPage — estrutura das três abas", () => {
  it("renderiza título, três abas e três indicadores", async () => {
    setLocation();
    cockpitMock.mockResolvedValue(cockpit());
    render(<MonthlyClosingPage basePath={BASE} />);

    expect(screen.getByText("Fechamento mensal")).toBeTruthy();
    for (const label of [
      "Visão geral",
      "Documentos e interações",
      "Relatórios e divergências",
    ]) {
      expect(screen.getByRole("button", { name: label })).toBeTruthy();
    }
    for (const indicator of [
      "Bloqueios",
      "Divergências",
      "Documentos a tratar",
    ]) {
      expect(screen.getByText(indicator)).toBeTruthy();
    }

    await waitFor(() =>
      expect(cockpitMock).toHaveBeenCalledWith(expect.any(String)),
    );
  });

  it("indicadores mostram contagens reais do cockpit, nunca inventadas", async () => {
    setLocation();
    cockpitMock.mockResolvedValue(cockpit());
    render(<MonthlyClosingPage basePath={BASE} />);

    await screen.findByText("Conclusão mensal");
    // 1 blocking_reason, 1 divergência não-zero (12.50), 8 EXPECTED.
    expect(
      screen.getByRole("button", { name: "Bloqueios: 1" }),
    ).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Divergências: 1" }),
    ).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Documentos a tratar: 8" }),
    ).toBeTruthy();
  });

  it("sem dados carregados os indicadores mostram «—», não zero", () => {
    setLocation();
    cockpitMock.mockReturnValue(new Promise(() => {}));
    render(<MonthlyClosingPage basePath={BASE} />);
    expect(
      screen.getByRole("button", { name: "Bloqueios: —" }),
    ).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Documentos a tratar: —" }),
    ).toBeTruthy();
  });
});

describe("MonthlyClosingPage — navegação entre abas", () => {
  it("troca para Documentos e interações preservando a competência", async () => {
    setLocation();
    cockpitMock.mockResolvedValue(cockpit());
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);
    await screen.findByText("Conclusão mensal");

    fireEvent.click(
      screen.getByRole("button", { name: "Documentos e interações" }),
    );

    expect(screen.getByTestId("documents-panel").textContent).toBe(
      "documents:2026-10",
    );
    expect(
      screen.getByRole("button", { name: "Abrir checklist da competência" }),
    ).toBeTruthy();
    expect(window.location.search).toContain("tab=documents");
  });

  it("troca para Relatórios e divergências com matriz, links e slot de PDF", async () => {
    setLocation();
    cockpitMock.mockResolvedValue(cockpit());
    render(<MonthlyClosingPage basePath={BASE} period="2026-10" />);
    await screen.findByText("Conclusão mensal");

    fireEvent.click(
      screen.getByRole("button", { name: "Relatórios e divergências" }),
    );

    expect(screen.getByTestId("reports-panel").textContent).toBe(
      "reports:2026-10",
    );
    expect(
      screen.getByRole("button", { name: "Baixas financeiras" }),
    ).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Estoque histórico — P7" }),
    ).toBeTruthy();
    expect(screen.getByText("Prévia do PDF")).toBeTruthy();
    expect(window.location.search).toContain("tab=reports");
  });

  it("indicador clicável abre a aba correspondente", async () => {
    setLocation();
    cockpitMock.mockResolvedValue(cockpit());
    render(<MonthlyClosingPage basePath={BASE} />);
    await screen.findByText("Conclusão mensal");

    fireEvent.click(
      screen.getByRole("button", { name: "Documentos a tratar: 8" }),
    );
    expect(screen.getByTestId("documents-panel")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Divergências: 1" }));
    expect(screen.getByTestId("reports-panel")).toBeTruthy();
  });

  it("deep link ?tab=reports abre direto na aba de relatórios", async () => {
    setLocation("?tab=reports");
    cockpitMock.mockResolvedValue(cockpit());
    render(<MonthlyClosingPage basePath={BASE} />);

    await waitFor(() =>
      expect(screen.getByTestId("reports-panel")).toBeTruthy(),
    );
  });

  it("erro da API exibe banner honesto com retry", async () => {
    setLocation();
    cockpitMock.mockRejectedValue(
      new (await import("../../api/httpClient")).ApiError(
        404,
        "not found",
        "competence_not_opened",
      ),
    );
    render(<MonthlyClosingPage basePath={BASE} />);
    await waitFor(() =>
      expect(screen.getByText(/Competência não aberta/)).toBeTruthy(),
    );
  });
});
