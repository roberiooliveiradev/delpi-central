import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@delpi/plugin-ui/index", async () => await import("../../test/pluginUiMock"));

const apiMock = vi.fn();
vi.mock("../../api/costClosingStateApi", () => ({
  getCostClosingState: (...args: unknown[]) => apiMock(...args),
}));

import { CostClosingStatePage } from "./CostClosingStatePage";

const node = (state: string, limitations: string[] = []) => ({
  state,
  evidenceRefs: {},
  limitations,
});

const payload = {
  report: "cost-closing-state",
  period: "2026-09",
  referenceDate: "2026-09-30",
  officiality: "technical_markers",
  observedAt: "2026-10-31T20:02:30Z",
  branches: {
    "01": {
      snapshot: node("available"),
      cutoff_marker: node("observed"),
      cost_evidence: node("observed", [
        "Evidência de escrita TTAT não prova conclusão da rotina.",
      ]),
      wizard_lifecycle: node("unavailable"),
      human_acceptance: node("not_informed"),
    },
    "02": {
      snapshot: node("missing"),
      cutoff_marker: node("not_advanced"),
      cost_evidence: node("unavailable"),
      wizard_lifecycle: node("unavailable"),
      human_acceptance: node("not_informed"),
    },
  },
  limitations: ["Marcadores técnicos observados — não são homologação."],
};

describe("CostClosingStatePage — trilha de nós R12/R15", () => {
  beforeEach(() => {
    apiMock.mockResolvedValue(payload);
  });
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("renderiza nós por filial com estados honestos", async () => {
    render(<CostClosingStatePage reportContext={{ period: "2026-09" }} />);
    await screen.findByText("Filial 01");
    expect(screen.getByText("Filial 02")).toBeTruthy();
    // f01 observada; f02 honestamente negativa
    expect(screen.getAllByText("Observado").length).toBe(2);
    expect(screen.getByText("Snapshot ausente")).toBeTruthy();
    expect(screen.getByText("Não avançado")).toBeTruthy();
    // wizard e homologação nunca inferidos
    expect(screen.getAllByText("Indisponível").length).toBeGreaterThanOrEqual(
      3,
    );
    expect(screen.getAllByText("Não informado").length).toBe(2);
    // nunca afirma conclusão
    expect(screen.queryByText("Concluído")).toBeNull();
    expect(screen.queryByText("Fechado")).toBeNull();
    // limitações e oficialidade exibidas
    expect(
      screen.getAllByText(/Marcadores técnicos observados/).length,
    ).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/technical_markers/).length).toBeGreaterThanOrEqual(1);
  });

  it("estado de erro oferece retry sem mascarar falha", async () => {
    apiMock.mockRejectedValueOnce(new Error("falha de rede"));
    render(<CostClosingStatePage reportContext={{ period: "2026-09" }} />);
    await screen.findAllByText(/Falha|erro|Erro/i);
    expect(apiMock).toHaveBeenCalledWith("2026-09");
  });
});
