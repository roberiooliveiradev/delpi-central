import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@delpi/plugin-ui/index", async () => await import("../../test/pluginUiMock"));

const getBatchMock = vi.fn();
const recordBatchMock = vi.fn();
const getProposalMock = vi.fn();
const recordProposalMock = vi.fn();

vi.mock("../../api/claraConsentApi", () => ({
  getClaraBatchConsentView: (...args: unknown[]) => getBatchMock(...args),
  recordClaraBatchConsent: (...args: unknown[]) => recordBatchMock(...args),
  getClaraProposalConsentView: (...args: unknown[]) =>
    getProposalMock(...args),
  recordClaraProposalConsent: (...args: unknown[]) =>
    recordProposalMock(...args),
}));

import { ClaraConsentPage } from "./ClaraConsentPage";

const UUID = "123e4567-e89b-42d3-a456-426614174000";

function setSearch(search: string) {
  window.history.replaceState(null, "", `?${search}`);
}

function batch(overrides: Record<string, unknown> = {}) {
  return {
    batch_id: UUID,
    status: "PREPARED",
    plan_hash: "a".repeat(64),
    consent_mode: "NONE",
    expires_at: new Date(Date.now() + 600_000).toISOString(),
    created_at: new Date().toISOString(),
    operations: [
      {
        seq: 0,
        capability: "review.decide",
        resource_type: "package",
        resource_key: "pkg-1",
        state: "PREPARED",
        depends_on: [],
      },
      {
        seq: 1,
        capability: "clarification.open",
        resource_type: "review",
        resource_key: "rev-1",
        state: "PREPARED",
        depends_on: [0],
      },
    ],
    ...overrides,
  };
}

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  window.history.replaceState(null, "", "/");
});

describe("ClaraConsentPage", () => {
  it("mostra estado honesto quando o link não traz alvo", async () => {
    setSearch("");
    render(<ClaraConsentPage />);
    await waitFor(() =>
      expect(
        screen.getByText(/Nenhum lote ou proposta informado/),
      ).toBeTruthy(),
    );
    expect(getBatchMock).not.toHaveBeenCalled();
  });

  it("carrega o lote e registra o consentimento consolidado", async () => {
    setSearch(`batch=${UUID}`);
    getBatchMock.mockResolvedValue(batch());
    recordBatchMock.mockResolvedValue({
      batch_id: UUID,
      status: "CONFIRMED",
      consent_mode: "CONSOLIDATED",
      confirmed_at: new Date().toISOString(),
    });
    render(<ClaraConsentPage />);
    await waitFor(() =>
      expect(screen.getByText("review.decide")).toBeTruthy(),
    );
    fireEvent.click(
      screen.getByRole("button", { name: /Consentir as 2 operações/ }),
    );
    await waitFor(() =>
      expect(recordBatchMock).toHaveBeenCalledWith(UUID),
    );
    await waitFor(() =>
      expect(
        screen.getByText(/Consentimento do lote registrado/),
      ).toBeTruthy(),
    );
  });

  it("não oferece consentir um lote já confirmado", async () => {
    setSearch(`batch=${UUID}`);
    getBatchMock.mockResolvedValue(batch({ status: "CONFIRMED" }));
    render(<ClaraConsentPage />);
    await waitFor(() =>
      expect(screen.getByText("clarification.open")).toBeTruthy(),
    );
    expect(
      screen.queryByRole("button", { name: /Consentir/ }),
    ).toBeNull();
  });

  it("traduz erro de ator divergente", async () => {
    setSearch(`batch=${UUID}`);
    getBatchMock.mockRejectedValue(
      Object.assign(new Error("forbidden"), {
        status: 403,
        code: "batch_actor_mismatch",
      }),
    );
    render(<ClaraConsentPage />);
    await waitFor(() =>
      expect(
        screen.getByText(/pertence a outro usuário/),
      ).toBeTruthy(),
    );
  });

  it("carrega a proposta e registra consentimento single-op", async () => {
    setSearch(`proposal=${UUID}`);
    getProposalMock.mockResolvedValue({
      proposal_id: UUID,
      capability: "review.decide",
      resource_type: "package",
      resource_key: "pkg-1",
      params: { period: "2025-09" },
      expected_state: {},
      execution_state: "PREPARED",
      consented_at: null,
      expires_at: new Date(Date.now() + 600_000).toISOString(),
      created_at: new Date().toISOString(),
    });
    recordProposalMock.mockResolvedValue({
      proposal_id: UUID,
      consented_at: new Date().toISOString(),
    });
    render(<ClaraConsentPage />);
    await waitFor(() =>
      expect(screen.getByText(/review.decide/)).toBeTruthy(),
    );
    fireEvent.click(
      screen.getByRole("button", { name: /Consentir esta operação/ }),
    );
    await waitFor(() =>
      expect(recordProposalMock).toHaveBeenCalledWith(UUID),
    );
  });
});
