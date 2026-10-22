/** @vitest-environment jsdom */
import { describe, expect, it } from "vitest";
import { ApiError } from "./api.ts";
import {
  HANDOFF_ERROR_CODES,
  handoffConflictView,
  handoffIntentSignature,
  isUncertainHandoffError,
  newHandoffRequestId,
} from "./runHandoff.ts";

const UUID_V4 =
  /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

describe("newHandoffRequestId", () => {
  it("gera UUID v4 válido para o contrato da E1", () => {
    expect(newHandoffRequestId()).toMatch(UUID_V4);
  });

  it("gera chaves distintas por intenção", () => {
    const seen = new Set<string>();
    for (let index = 0; index < 50; index += 1) {
      seen.add(newHandoffRequestId());
    }
    expect(seen.size).toBe(50);
  });
});

describe("handoffIntentSignature", () => {
  it("mesmo alvo = mesma assinatura (retry reusa requestId)", () => {
    const a = handoffIntentSignature({
      expectedNext: { productionOrder: "OP1", operationCode: "05" },
    });
    const b = handoffIntentSignature({
      expectedNext: { productionOrder: "OP1", operationCode: "05" },
    });
    expect(a).toBe(b);
  });

  it("alvo diferente = nova intenção", () => {
    const a = handoffIntentSignature({
      expectedNext: { productionOrder: "OP1", operationCode: "05" },
    });
    const b = handoffIntentSignature({
      expectedNext: { productionOrder: "OP2", operationCode: "10" },
    });
    expect(a).not.toBe(b);
  });
});

describe("isUncertainHandoffError", () => {
  it("falha de rede (não ApiError) é resultado incerto", () => {
    expect(isUncertainHandoffError(new TypeError("fetch failed"))).toBe(true);
    expect(isUncertainHandoffError(new Error("timeout"))).toBe(true);
  });

  it("502/503 são incertos — a transação pode ter commitado", () => {
    expect(isUncertainHandoffError(new ApiError("x", 502))).toBe(true);
    expect(isUncertainHandoffError(new ApiError("x", 503))).toBe(true);
  });

  it("400/401/404/409/422 são respostas definitivas", () => {
    for (const status of [400, 401, 404, 409, 422]) {
      expect(isUncertainHandoffError(new ApiError("x", status))).toBe(false);
    }
  });
});

describe("handoffConflictView", () => {
  it("todos os códigos da E1 bloqueiam a troca sem encerrar sozinho", () => {
    for (const code of HANDOFF_ERROR_CODES) {
      const view = handoffConflictView(code, null);
      expect(view.blocksNext).toBe(true);
      expect(view.message.length).toBeGreaterThan(0);
    }
  });

  it("count_boundary_stale pede prévia nova + escolha explícita", () => {
    const view = handoffConflictView("count_boundary_stale", null);
    expect(view.action).toBe("refresh_preview");
    expect(view.blocksNext).toBe(true);
  });

  it("queue_changed pede prévia nova + escolha explícita", () => {
    expect(handoffConflictView("queue_changed", null).action).toBe(
      "refresh_preview",
    );
  });

  it("request_conflict pede prévia nova — nunca reusa a chave", () => {
    expect(handoffConflictView("request_conflict", null).action).toBe(
      "refresh_preview",
    );
  });

  it("pulse_unavailable permite nova prévia quando o contador voltar", () => {
    expect(handoffConflictView("pulse_unavailable", null).action).toBe(
      "refresh_preview",
    );
  });

  it("pending_classification aponta o fluxo de motivo existente", () => {
    expect(handoffConflictView("pending_classification", null).action).toBe(
      "classify",
    );
  });

  it("no_next_operation e balance_unknown são finais — só encerrar", () => {
    expect(handoffConflictView("no_next_operation", null).action).toBe("none");
    expect(handoffConflictView("balance_unknown", null).action).toBe("none");
  });

  it("device_mismatch e epoch_conflict bloqueiam sem fallback", () => {
    expect(handoffConflictView("device_mismatch", null).action).toBe("none");
    expect(handoffConflictView("epoch_conflict", null).action).toBe("none");
  });

  it("run_not_active e current_not_in_queue reconciliam o estado", () => {
    expect(handoffConflictView("run_not_active", null).action).toBe("reconcile");
    expect(handoffConflictView("current_not_in_queue", null).action).toBe(
      "reconcile",
    );
  });

  it("mensagem do servidor prevalece quando presente", () => {
    const view = handoffConflictView("queue_changed", "Fila reprogramada às 10h.");
    expect(view.message).toBe("Fila reprogramada às 10h.");
  });

  it("código desconhecido cai no caso conservador (prévia nova)", () => {
    const view = handoffConflictView(undefined, null);
    expect(view.action).toBe("refresh_preview");
    expect(view.blocksNext).toBe(true);
  });
});
