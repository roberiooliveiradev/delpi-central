import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@delpi/plugin-ui/index", async () => await import("../../test/pluginUiMock"));

const getP3Mock = vi.fn();
const confirmCutoffMock = vi.fn();
const revalidateMock = vi.fn();
const upsertReconMock = vi.fn();
let manageCap = false;

vi.mock("../../api/p3Api", () => ({
  getP3State: (...args: unknown[]) => getP3Mock(...args),
  confirmP3Cutoff: (...args: unknown[]) => confirmCutoffMock(...args),
  revalidateP3: (...args: unknown[]) => revalidateMock(...args),
  upsertP3Reconciliation: (...args: unknown[]) =>
    upsertReconMock(...args),
}));

vi.mock("../../app/ViewerContext", () => ({
  useViewerCapabilities: () => ({ access: true, manage: manageCap }),
}));

import { P3CutoffPanel } from "./P3CutoffPanel";

const PERIOD = "2026-07";

function p3State(overrides: Record<string, unknown> = {}) {
  return {
    period: PERIOD,
    state: "WAITING_FOR_CUTOFF",
    canonical_stock_state: "UNAVAILABLE",
    cutoff: null,
    reconciliations: [
      { domain: "ENTRADAS_SAIDAS", source_state: "UNAVAILABLE",
        expected_amount: null, reported_amount: null,
        divergence: null, fetched_at: null, rule_version: null,
        provenance: null },
      { domain: "P7", source_state: "UNAVAILABLE",
        expected_amount: null, reported_amount: null,
        divergence: null, fetched_at: null, rule_version: null,
        provenance: null },
      { domain: "H02", source_state: "UNAVAILABLE",
        expected_amount: null, reported_amount: null,
        divergence: null, fetched_at: null, rule_version: null,
        provenance: null },
    ],
    last_revalidation: null,
    revalidation_valid: false,
    input_fingerprint: "fp",
    blockers: [
      "cutoff_not_confirmed",
      "source_unavailable:ENTRADAS_SAIDAS",
      "source_unavailable:P7",
      "source_unavailable:H02",
    ],
    ...overrides,
  };
}

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  manageCap = false;
});

describe("P3CutoffPanel", () => {
  it("exibe bloqueios honestos sem cutoff e sem fontes", async () => {
    getP3Mock.mockResolvedValue(p3State());
    render(<P3CutoffPanel period={PERIOD} />);
    await waitFor(() =>
      expect(
        screen.getByText("Aguardando cutoff"),
      ).toBeTruthy(),
    );
    expect(
      screen.getByText(/Nenhum cutoff confirmado/),
    ).toBeTruthy();
    expect(screen.getAllByText(/Fonte indisponível/)).toHaveLength(3);
  });

  it("ator sem manage não vê ações governadas", async () => {
    getP3Mock.mockResolvedValue(p3State());
    render(<P3CutoffPanel period={PERIOD} />);
    await waitFor(() =>
      expect(screen.getByText("Aguardando cutoff")).toBeTruthy(),
    );
    expect(
      screen.queryByRole("button", { name: "Confirmar cutoff" }),
    ).toBeNull();
  });

  it("ator manage confirma cutoff", async () => {
    manageCap = true;
    getP3Mock.mockResolvedValue(p3State());
    confirmCutoffMock.mockResolvedValue({ cutoff_id: "c-1" });
    render(<P3CutoffPanel period={PERIOD} />);
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Confirmar cutoff" }),
      ).toBeTruthy(),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Confirmar cutoff" }),
    );
    await waitFor(() =>
      expect(confirmCutoffMock).toHaveBeenCalledWith(PERIOD),
    );
  });

  it("READY_TO_CLOSE só com paridade zero exibida pelo backend", async () => {
    getP3Mock.mockResolvedValue(
      p3State({
        state: "READY_TO_CLOSE",
        cutoff: {
          cutoff_id: "c-1",
          competence_id: "comp-1",
          confirmed_by: "ana",
          confirmed_at: "2026-07-31T12:00:00+00:00",
          notes: null,
          revision: 1,
        },
        blockers: [],
        revalidation_valid: true,
      }),
    );
    render(<P3CutoffPanel period={PERIOD} />);
    await waitFor(() =>
      expect(
        screen.getByText("Pronto para fechar"),
      ).toBeTruthy(),
    );
  });
});
