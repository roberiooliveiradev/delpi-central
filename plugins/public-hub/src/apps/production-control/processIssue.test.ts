import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { ApiError, createProcessIssue } from "./api.ts";
import {
  PROCESS_ISSUE_REASONS,
  PROCESS_ISSUE_REASON_REQUIRED,
  beginProcessIssueAttempt,
  isProcessIssueDraftValid,
  processIssueConfirmationMessage,
  processIssueDraftSignature,
  processIssueReason,
  processIssueSubmitErrorMessage,
  submitKeyForDraft,
  type ProcessIssueDraft,
} from "./processIssue.ts";

const DRAFT: ProcessIssueDraft = {
  issueCode: "tool_not_linked",
  toolCode: "F12345",
  materialCode: null,
  note: "Ferramenta não consta na operação.",
};

function draft(partial: Partial<ProcessIssueDraft> = {}): ProcessIssueDraft {
  return { ...DRAFT, ...partial };
}

// --- catálogo -----------------------------------------------------------------

describe("process issue catalog", () => {
  it("has exactly the six canonical codes", () => {
    assert.deepEqual(
      PROCESS_ISSUE_REASONS.map((item) => item.code),
      [
        "work_center_incompatible",
        "machine_limitation",
        "tool_not_linked",
        "material_not_linked",
        "process_information_missing",
        "other",
      ],
    );
  });

  it("labels are business copy without internal jargon", () => {
    assert.equal(
      processIssueReason("tool_not_linked")?.label,
      "Ferramenta não informada ou não vinculada",
    );
    assert.equal(
      processIssueReason("material_not_linked")?.label,
      "Matéria-prima não vinculada à operação",
    );
    assert.equal(processIssueReason("nope"), null);
  });

  it("identifies auxiliary fields only for tool/material reasons", () => {
    assert.equal(
      processIssueReason("tool_not_linked")?.auxiliaryField,
      "toolCode",
    );
    assert.equal(
      processIssueReason("material_not_linked")?.auxiliaryField,
      "materialCode",
    );
    for (const code of [
      "work_center_incompatible",
      "machine_limitation",
      "process_information_missing",
      "other",
    ]) {
      assert.equal(processIssueReason(code)?.auxiliaryField, null);
    }
  });

  it("reason is the only required field", () => {
    assert.equal(isProcessIssueDraftValid(draft()), true);
    assert.equal(
      isProcessIssueDraftValid(
        draft({ toolCode: null, materialCode: null, note: null }),
      ),
      true,
    );
    assert.equal(isProcessIssueDraftValid(draft({ issueCode: "" })), false);
    assert.equal(
      isProcessIssueDraftValid(draft({ issueCode: "unknown" })),
      false,
    );
    assert.ok(PROCESS_ISSUE_REASON_REQUIRED.length > 0);
  });
});

// --- tentativa / idempotency-key ------------------------------------------------

describe("process issue attempt keys", () => {
  let counter = 0;
  const nextKey = () => `key-${++counter}`;

  it("generates the key when the attempt begins", () => {
    const attempt = beginProcessIssueAttempt(nextKey);
    assert.equal(attempt.key, "key-1");
    assert.equal(attempt.submittedSignature, null);
  });

  it("first submit reuses the opening key", () => {
    const attempt = beginProcessIssueAttempt(nextKey);
    const r = submitKeyForDraft(attempt, draft(), nextKey);
    assert.equal(r.key, attempt.key);
    assert.equal(r.reused, false);
  });

  it("retry with the SAME payload reuses the key", () => {
    let attempt = beginProcessIssueAttempt(nextKey);
    attempt = submitKeyForDraft(attempt, draft(), nextKey).attempt;
    const retry = submitKeyForDraft(attempt, draft(), nextKey);
    assert.equal(retry.key, attempt.key);
    assert.equal(retry.reused, true);
    assert.equal(retry.attempt.key, attempt.key);
  });

  it("payload change after an error generates a NEW key", () => {
    let attempt = beginProcessIssueAttempt(nextKey);
    attempt = submitKeyForDraft(attempt, draft(), nextKey).attempt;
    const retry = submitKeyForDraft(
      attempt,
      draft({ note: "outro detalhe" }),
      nextKey,
    );
    assert.notEqual(retry.key, attempt.key);
    assert.equal(retry.reused, false);
    // e o retry do novo payload estabiliza na nova chave
    const again = submitKeyForDraft(retry.attempt, draft({ note: "outro detalhe" }), nextKey);
    assert.equal(again.key, retry.key);
  });

  it("signature ignores surrounding whitespace and null-vs-empty", () => {
    const a = processIssueDraftSignature(
      draft({ toolCode: "F1", materialCode: null, note: null }),
    );
    const b = processIssueDraftSignature(
      draft({ toolCode: " F1 ", materialCode: "", note: "  " }),
    );
    assert.equal(a, b);
  });

  it("new attempt always produces a new key", () => {
    const first = beginProcessIssueAttempt(nextKey);
    const second = beginProcessIssueAttempt(nextKey);
    assert.notEqual(first.key, second.key);
  });
});

// --- mensagens de erro -------------------------------------------------------------

describe("process issue error messages", () => {
  it("401 asks to identify again", () => {
    assert.equal(
      processIssueSubmitErrorMessage(401),
      "Identifique-se novamente para enviar a solicitação.",
    );
  });

  it("404 reports the operation unavailable", () => {
    assert.equal(
      processIssueSubmitErrorMessage(404),
      "Esta operação não está mais disponível neste posto.",
    );
  });

  it("422 surfaces the safe upstream message", () => {
    assert.equal(
      processIssueSubmitErrorMessage(422, "Motivo de problema desconhecido."),
      "Motivo de problema desconhecido.",
    );
    assert.equal(
      processIssueSubmitErrorMessage(422, null),
      "Não foi possível enviar a solicitação para Processos. Tente novamente.",
    );
  });

  it("503/network fall back to the friendly retry message", () => {
    assert.equal(
      processIssueSubmitErrorMessage(503),
      "Não foi possível enviar a solicitação para Processos. Tente novamente.",
    );
    assert.equal(
      processIssueSubmitErrorMessage(null),
      "Não foi possível enviar a solicitação para Processos. Tente novamente.",
    );
  });
});

describe("process issue confirmation", () => {
  it("uses the request number when present", () => {
    assert.equal(
      processIssueConfirmationMessage("REQ-2026-000123"),
      "Solicitação REQ-2026-000123 enviada para Processos.",
    );
    assert.equal(
      processIssueConfirmationMessage(null),
      "Solicitação enviada para Processos.",
    );
  });
});

// --- contrato da API ------------------------------------------------------------------

function stubFetch(status: number, body: unknown) {
  const calls: { url: string; init?: RequestInit }[] = [];
  const original = globalThis.fetch;
  globalThis.fetch = (async (url: string | URL | Request, init?: RequestInit) => {
    calls.push({ url: String(url), init });
    return new Response(JSON.stringify(body), {
      status,
      headers: { "Content-Type": "application/json" },
    });
  }) as typeof fetch;
  return { calls, restore: () => (globalThis.fetch = original) };
}

describe("createProcessIssue api", () => {
  it("POSTs the public contract with bench session and idempotency key", async () => {
    const { calls, restore } = stubFetch(201, {
      success: true,
      data: {
        requestId: "req-9",
        requestNumber: "REQ-2026-000123",
        status: "submitted",
        message: "Solicitação enviada para Processos.",
      },
    });
    try {
      const result = await createProcessIssue("tok", "sess-1", "idem-1", {
        productionOrder: "24640401002",
        operationCode: "03",
        issueCode: "tool_not_linked",
        toolCode: "F12345",
      });
      assert.equal(result.requestNumber, "REQ-2026-000123");
      assert.equal(result.status, "submitted");

      const call = calls[0];
      assert.equal(
        call.url,
        "/apps/production-control-api/public/machine-load/tok/process-issues",
      );
      const headers = call.init?.headers as Record<string, string>;
      assert.equal(headers["X-Delpi-Bench-Session"], "sess-1");
      assert.equal(headers["Idempotency-Key"], "idem-1");
      assert.equal(call.init?.method, "POST");

      const body = JSON.parse(String(call.init?.body));
      assert.deepEqual(body, {
        productionOrder: "24640401002",
        operationCode: "03",
        issueCode: "tool_not_linked",
        toolCode: "F12345",
        materialCode: null,
        note: null,
        website: "",
      });
      // nenhum campo de identidade/contexto é enviado pelo frontend
      for (const forbidden of [
        "branch",
        "workCenter",
        "operatorCode",
        "operatorName",
        "productCode",
        "paProductCode",
        "toolSnapshot",
        "materials",
      ]) {
        assert.equal(
          forbidden in body,
          false,
          `${forbidden} não pode sair do frontend`,
        );
      }
    } finally {
      restore();
    }
  });

  it("optional fields may be absent from the call", async () => {
    const { calls, restore } = stubFetch(201, {
      success: true,
      data: { requestId: null, requestNumber: "REQ-1", status: "submitted" },
    });
    try {
      await createProcessIssue("tok", "sess-1", "idem-1", {
        productionOrder: "1",
        operationCode: "03",
        issueCode: "other",
      });
      const body = JSON.parse(String(calls[0].init?.body));
      assert.equal(body.toolCode, null);
      assert.equal(body.materialCode, null);
      assert.equal(body.note, null);
    } finally {
      restore();
    }
  });

  it("propagates ApiError with status (401/422/503)", async () => {
    for (const status of [401, 422, 503]) {
      const { restore } = stubFetch(status, {
        success: false,
        message: "falhou",
      });
      try {
        await createProcessIssue("t", "s", "k", {
          productionOrder: "1",
          operationCode: "03",
          issueCode: "other",
        }).then(
          () => assert.fail("deveria lançar"),
          (err: unknown) => {
            assert.ok(err instanceof ApiError);
            assert.equal(err.status, status);
          },
        );
      } finally {
        restore();
      }
    }
  });
});
