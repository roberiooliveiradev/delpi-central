import { afterEach, describe, expect, it, vi } from "vitest";

import {
  DIAGNOSTIC_ACTION_ALLOWLIST,
  DIAGNOSTIC_CONCLUSION_LIFECYCLE_ACTIONS,
  DIAGNOSTIC_ENTITY_ACTIONS,
  DIAGNOSTIC_HYPOTHESIS_LIFECYCLE_ACTIONS,
  DIAGNOSTIC_HYPOTHESIS_MARK_ACTIONS,
  commitGovernedProposal,
  fetchDiagnostic,
  isDiagnosticManageAction,
  listRevisionDiagnostics,
  prepareCreateDiagnostic,
  prepareManageDiagnostic,
} from "./transformometroDiagnosticApi";
import { TransformometroHttpError } from "./transformometroHttp";

const BASE = "/apps/transformometro-api/transformometro";

function okEnvelope(data: unknown) {
  return new Response(JSON.stringify({ success: true, message: "OK", data }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

function failEnvelope(status: number, message: string, data?: unknown) {
  return new Response(
    JSON.stringify({ success: false, message, data: data ?? null }),
    { status, headers: { "Content-Type": "application/json" } },
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("DIAGNOSTIC_ACTION_ALLOWLIST", () => {
  it("contém exatamente as 13 actions canônicas do backend", () => {
    expect(DIAGNOSTIC_ACTION_ALLOWLIST).toHaveLength(13);
    expect([...DIAGNOSTIC_ACTION_ALLOWLIST].sort()).toEqual(
      [
        "add_finding",
        "add_hypothesis",
        "add_causal_link",
        "add_evidence_link",
        "add_conclusion",
        "validate_hypothesis",
        "reject_hypothesis",
        "supersede_hypothesis",
        "mark_hypothesis_stale_evidence",
        "mark_hypothesis_revalidation_required",
        "validate_conclusion",
        "reject_conclusion",
        "supersede_conclusion",
      ].sort(),
    );
    // Sem ações genéricas.
    for (const action of DIAGNOSTIC_ACTION_ALLOWLIST) {
      expect(action).not.toMatch(/edit|update|delete|remove|unlink/i);
    }
    expect(new Set(DIAGNOSTIC_ACTION_ALLOWLIST).size).toBe(13);
    expect(DIAGNOSTIC_ENTITY_ACTIONS).toHaveLength(5);
    expect(DIAGNOSTIC_HYPOTHESIS_LIFECYCLE_ACTIONS).toHaveLength(3);
    expect(DIAGNOSTIC_HYPOTHESIS_MARK_ACTIONS).toHaveLength(2);
    expect(DIAGNOSTIC_CONCLUSION_LIFECYCLE_ACTIONS).toHaveLength(3);
  });

  it("isDiagnosticManageAction valida somente o allowlist", () => {
    expect(isDiagnosticManageAction("add_finding")).toBe(true);
    expect(isDiagnosticManageAction("edit_finding")).toBe(false);
    expect(isDiagnosticManageAction("remove_evidence_link")).toBe(false);
    expect(isDiagnosticManageAction("")).toBe(false);
  });
});

describe("diagnostic api client", () => {
  it("lista diagnósticos da revisão pelo endpoint canônico", async () => {
    const spy = vi.fn().mockResolvedValue(okEnvelope({ items: [], total: 0 }));
    vi.stubGlobal("fetch", spy);
    const result = await listRevisionDiagnostics("rev-1", () => "tok");
    const [url, init] = spy.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(`${BASE}/revisions/rev-1/diagnostics`);
    expect((init.headers as Record<string, string>).Authorization).toBe("Bearer tok");
    expect(result.items).toEqual([]);
  });

  it("lê o diagnóstico por id pelo endpoint canônico", async () => {
    const spy = vi.fn().mockResolvedValue(okEnvelope({ diagnostic: {} }));
    vi.stubGlobal("fetch", spy);
    await fetchDiagnostic("diag-1", () => "tok");
    expect(spy.mock.calls[0][0]).toBe(`${BASE}/diagnostics/diag-1`);
  });

  it("PREPARE create envia somente problem_statement (sem ids de cliente)", async () => {
    const spy = vi.fn().mockResolvedValue(okEnvelope({ proposal_handle: "gp_1" }));
    vi.stubGlobal("fetch", spy);
    await prepareCreateDiagnostic("rev-1", "Problema X", () => "tok");
    const [url, init] = spy.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(`${BASE}/revisions/rev-1/diagnostics/prepare`);
    expect(init.method).toBe("POST");
    const body = JSON.parse(String(init.body));
    expect(body).toEqual({ problem_statement: "Problema X" });
    expect(body).not.toHaveProperty("diagnostic_id");
    expect(body).not.toHaveProperty("provenance");
  });

  it("PREPARE manage envia action + payload sem campos server-owned", async () => {
    const spy = vi.fn().mockResolvedValue(okEnvelope({ proposal_handle: "gp_2" }));
    vi.stubGlobal("fetch", spy);
    await prepareManageDiagnostic(
      "diag-1",
      "add_hypothesis",
      { statement: "Hipótese Y" },
      () => "tok",
    );
    const [url, init] = spy.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(`${BASE}/diagnostics/diag-1/prepare`);
    const body = JSON.parse(String(init.body));
    expect(body).toEqual({ action: "add_hypothesis", payload: { statement: "Hipótese Y" } });
    expect(body.payload).not.toHaveProperty("hypothesis_id");
  });

  it("COMMIT usa a rota compartilhada com confirmation=true", async () => {
    const spy = vi.fn().mockResolvedValue(okEnvelope({ capability: "manage_diagnostic" }));
    vi.stubGlobal("fetch", spy);
    await commitGovernedProposal("gp_9", () => "tok");
    const [url, init] = spy.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(`${BASE}/governed-proposals/commit`);
    const body = JSON.parse(String(init.body));
    expect(body).toEqual({ proposal_handle: "gp_9", confirmation: true });
  });

  it("mapeia erros HTTP e preserva error_code canônico", async () => {
    const spy = vi
      .fn()
      .mockResolvedValue(failEnvelope(403, "Sem permissão", { error_code: "FORBIDDEN" }));
    vi.stubGlobal("fetch", spy);
    await expect(listRevisionDiagnostics("rev-1", () => "tok")).rejects.toMatchObject({
      status: 403,
      code: "FORBIDDEN",
    });

    spy.mockResolvedValue(failEnvelope(409, "stale", { error_code: "PROPOSAL_STALE" }));
    await expect(commitGovernedProposal("gp_x", () => "tok")).rejects.toMatchObject({
      status: 409,
      code: "PROPOSAL_STALE",
    });

    spy.mockResolvedValue(
      failEnvelope(422, "Confirmação exigida", { error_code: "CONFIRMATION_REQUIRED" }),
    );
    await expect(commitGovernedProposal("gp_y", () => "tok")).rejects.toBeInstanceOf(
      TransformometroHttpError,
    );
  });
});
