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
const CHALLENGE = "999e4567-e89b-42d3-a456-426614174999";

function setSearch(search: string) {
  window.history.replaceState(null, "", `?${search}`);
}

function presentation(overrides: Record<string, unknown> = {}) {
  return {
    displayable: true,
    action: "Abrir esclarecimento",
    target: "para a área CONTÁBIL sobre o pacote CONTÁBIL v2",
    effect: "o pacote fica com um esclarecimento aberto",
    motivation: null,
    summary:
      "Abrir esclarecimento para a área CONTÁBIL sobre o pacote CONTÁBIL v2 da competência setembro de 2026.",
    ...overrides,
  };
}

function batch(overrides: Record<string, unknown> = {}) {
  return {
    batch_id: UUID,
    status: "PREPARED",
    plan_hash: "a".repeat(64),
    consent_mode: "NONE",
    actor_sub: "44444444-4444-4444-8444-444444444444",
    expires_at: new Date(Date.now() + 600_000).toISOString(),
    created_at: new Date().toISOString(),
    confirmed_at: null,
    challenge: {
      challenge_id: CHALLENGE,
      status: "PENDING",
      created_at: new Date().toISOString(),
      approved_at: null,
      expires_at: new Date(Date.now() + 600_000).toISOString(),
    },
    competence: { period: "2026-09", period_label: "setembro de 2026" },
    totals: { total: 3, executable: 2, blocked: 1, dependent: 1 },
    consentable: true,
    consent_block_reason: null,
    operations: [
      {
        index: 0,
        seq: 0,
        capability: "review.record_decision",
        viability: "executable",
        state: "PREPARED",
        presentation: presentation({
          summary:
            "Aprovar o pacote CONTÁBIL v2 da competência setembro de 2026 (revisão da área CONTABIL).",
          effect: "a decisão da área fica registrada na revisão",
          motivation: "Revisão mensal",
        }),
        resource_type: "closing_package_version",
        resource_key: "ver-1",
        period: "2026-09",
        depends_on: [],
        block_reason: null,
        block_message: null,
        missing_params: [],
      },
      {
        index: 1,
        seq: 1,
        capability: "clarification.open",
        viability: "executable",
        state: "PREPARED",
        presentation: presentation({
          motivation: "«Confirma a conciliação bancária?»",
        }),
        resource_type: "closing_package_version",
        resource_key: "ver-1",
        period: "2026-09",
        depends_on: [0],
        block_reason: null,
        block_message: null,
        missing_params: [],
      },
      {
        index: 2,
        seq: 2,
        capability: "evidence.decide_version",
        viability: "blocked",
        state: "BLOCKED",
        presentation: presentation({
          summary:
            "Rejeitar o documento «Extrato Bancário» da competência setembro de 2026.",
        }),
        resource_type: "closing_document",
        resource_key: "doc-1",
        period: "2026-09",
        depends_on: [],
        block_reason: "snapshot_unavailable",
        block_message:
          "O estado atual do recurso não pôde ser confirmado — a operação ficou bloqueada por segurança.",
        missing_params: [],
      },
    ],
    ...overrides,
  };
}

function proposal(overrides: Record<string, unknown> = {}) {
  return {
    proposal_id: UUID,
    capability: "clarification.open",
    resource_type: "closing_package_version",
    resource_key: "ver-1",
    params: { period: "2026-09" },
    presentation: presentation(),
    expected_state: {},
    execution_state: "PREPARED",
    consented_at: null,
    expires_at: new Date(Date.now() + 600_000).toISOString(),
    created_at: new Date().toISOString(),
    challenge: {
      challenge_id: CHALLENGE,
      status: "PENDING",
      created_at: new Date().toISOString(),
      approved_at: null,
      expires_at: new Date(Date.now() + 600_000).toISOString(),
    },
    period: "2026-09",
    period_label: "setembro de 2026",
    consentable: true,
    consent_block_reason: null,
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

  it("apresenta o plano completo: resumo, descrições, bloqueada e dependência", async () => {
    setSearch(`batch=${UUID}`);
    getBatchMock.mockResolvedValue(batch());
    render(<ClaraConsentPage />);
    await waitFor(() =>
      expect(
        screen.getAllByText(/setembro de 2026/).length,
      ).toBeGreaterThan(0),
    );
    // Resumo do lote
    expect(screen.getByText(/3 no total/)).toBeTruthy();
    expect(screen.getByText(/2 executáveis/)).toBeTruthy();
    // Descrições funcionais — nunca capability crua como texto único
    expect(
      screen.getByText(/Aprovar o pacote CONTÁBIL v2/),
    ).toBeTruthy();
    expect(
      screen.getByText(/Abrir esclarecimento para a área CONTÁBIL/),
    ).toBeTruthy();
    // Operação bloqueada identificada com impedimento
    expect(screen.getByText("Bloqueada")).toBeTruthy();
    expect(screen.getByText(/Impedimento:/)).toBeTruthy();
    // Dependência legível
    expect(screen.getByText(/operação 1/)).toBeTruthy();
    // Motivo apresentado
    expect(screen.getByText(/Confirma a conciliação bancária?/)).toBeTruthy();
  });

  it("autoriza o lote uma única vez devolvendo o challenge_id", async () => {
    setSearch(`batch=${UUID}`);
    getBatchMock.mockResolvedValue(batch());
    recordBatchMock.mockResolvedValue({
      batch_id: UUID,
      status: "CONFIRMED",
      consent_mode: "CONSOLIDATED",
      challenge_id: CHALLENGE,
      confirmed_at: new Date().toISOString(),
    });
    render(<ClaraConsentPage />);
    await waitFor(() =>
      expect(
        screen.getByRole("button", {
          name: /Autorizar as 2 operações executáveis/,
        }),
      ).toBeTruthy(),
    );
    fireEvent.click(
      screen.getByRole("button", {
        name: /Autorizar as 2 operações executáveis/,
      }),
    );
    await waitFor(() =>
      expect(recordBatchMock).toHaveBeenCalledWith(UUID, CHALLENGE),
    );
    await waitFor(() =>
      expect(
        screen.getByText(/Autorização do lote registrada/),
      ).toBeTruthy(),
    );
  });

  it("não oferece autorizar um lote já confirmado", async () => {
    setSearch(`batch=${UUID}`);
    getBatchMock.mockResolvedValue(
      batch({ status: "CONFIRMED", consentable: false }),
    );
    render(<ClaraConsentPage />);
    await waitFor(() =>
      expect(
        screen.getByText(/Aprovar o pacote CONTÁBIL v2/),
      ).toBeTruthy(),
    );
    expect(
      screen.queryByRole("button", { name: /Autorizar/ }),
    ).toBeNull();
  });

  it("bloqueia o botão quando o plano não é consentível", async () => {
    setSearch(`batch=${UUID}`);
    getBatchMock.mockResolvedValue(
      batch({
        consentable: false,
        consent_block_reason: "operation_not_displayable",
      }),
    );
    render(<ClaraConsentPage />);
    await waitFor(() =>
      expect(screen.getByText(/sem descrição clara/)).toBeTruthy(),
    );
    expect(
      screen.queryByRole("button", { name: /Autorizar as/ }),
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

  it("carrega a proposta e autoriza com o challenge_id", async () => {
    setSearch(`proposal=${UUID}`);
    getProposalMock.mockResolvedValue(proposal());
    recordProposalMock.mockResolvedValue({
      proposal_id: UUID,
      consented_at: new Date().toISOString(),
    });
    render(<ClaraConsentPage />);
    await waitFor(() =>
      expect(
        screen.getByText(/Abrir esclarecimento para a área CONTÁBIL/),
      ).toBeTruthy(),
    );
    fireEvent.click(
      screen.getByRole("button", { name: /Autorizar esta operação/ }),
    );
    await waitFor(() =>
      expect(recordProposalMock).toHaveBeenCalledWith(UUID, CHALLENGE),
    );
  });
});
