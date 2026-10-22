import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiRequestError } from "../../../api/httpClient";
import {
  captureBulkDecision,
  capturePrepareOperation,
  captureSingleDecision,
  executeDecisionOperation,
  executePrepareOperation,
  isRecoverableForRetry,
} from "./decisionOperations";
import { decideEnrichmentBulk, decideEnrichmentField, prepareEnrichmentUpdate } from "./api";
import { newIdempotencyKey } from "./stateMachine";

vi.mock("./api", () => ({
  decideEnrichmentField: vi.fn().mockResolvedValue({ idempotent_replay: false }),
  decideEnrichmentBulk: vi.fn().mockResolvedValue({ idempotent_replay: false }),
  prepareEnrichmentUpdate: vi.fn().mockResolvedValue({ draft_fields: [] }),
}));

beforeEach(() => {
  vi.mocked(decideEnrichmentField).mockClear();
  vi.mocked(decideEnrichmentBulk).mockClear();
  vi.mocked(prepareEnrichmentUpdate).mockClear();
});

describe("T1 — retry de decisão individual é a mesma operação", () => {
  it("executa o payload capturado, mesmo após o estado evoluir", async () => {
    const op = captureSingleDecision(
      "002469", "01", "rev-1", "supplier_name", "ACCEPT", 5, "key-A",
    );
    // Simula a ficha evoluindo para revision 6 entre falha e retry: a operação
    // continua carregando a revisão 5 original.
    await executeDecisionOperation(op);
    await executeDecisionOperation(op);
    const calls = vi.mocked(decideEnrichmentField).mock.calls;
    expect(calls).toHaveLength(2);
    expect(calls[0]).toEqual(calls[1]);
    expect(calls[0].slice(0, 3)).toEqual(["002469", "01", "rev-1"]);
    expect(calls[0][3]).toEqual({
      field_key: "supplier_name",
      decision: "ACCEPT",
      expected_revision: 5,
      idempotency_key: "key-A",
    });
  });
});

describe("T2 — bulk preserva a seleção original", () => {
  it("copia field_keys na captura; mutar a seleção não altera o retry", async () => {
    const selection = ["supplier_name", "district"];
    const op = captureBulkDecision(
      "002469", "01", "rev-1", selection, "REJECT", 5, "key-B",
    );
    // Usuário muda a seleção para {district, city} antes do retry.
    selection.splice(0, 2, "district", "city");
    await executeDecisionOperation(op);
    const body = vi.mocked(decideEnrichmentBulk).mock.calls[0][3];
    expect(body.field_keys).toEqual(["supplier_name", "district"]);
    expect(body.field_keys).not.toContain("city");
    expect(body.idempotency_key).toBe("key-B");
  });
});

describe("T4 — nova intenção gera nova operação e nova chave", () => {
  it("duas capturas têm chaves distintas e payloads independentes", () => {
    const a = captureSingleDecision("c", "s", "r", "f", "ACCEPT", 1, newIdempotencyKey());
    const b = captureSingleDecision("c", "s", "r", "f", "ACCEPT", 1, newIdempotencyKey());
    expect(a.kind === "single" && b.kind === "single").toBe(true);
    if (a.kind === "single" && b.kind === "single") {
      expect(a.payload.idempotency_key).not.toBe(b.payload.idempotency_key);
      expect(a.payload).not.toBe(b.payload);
    }
  });
});

describe("T6 — conflitos nunca são recuperáveis para retry", () => {
  it.each([
    "ENRICHMENT_REVISION_CONFLICT",
    "ENRICHMENT_IDEMPOTENCY_CONFLICT",
    "ENRICHMENT_PROPOSAL_ALREADY_DECIDED",
    "ENRICHMENT_REVIEW_EXPIRED",
    "ENRICHMENT_PROPOSAL_NOT_ELIGIBLE",
  ])("%s → sem retry", (code) => {
    const err = new ApiRequestError("conflict", { status: 409, code });
    expect(isRecoverableForRetry(err)).toBe(false);
    const gone = new ApiRequestError("expired", { status: 410, code });
    expect(isRecoverableForRetry(gone)).toBe(false);
  });

  it("422 de validação → sem retry", () => {
    expect(
      isRecoverableForRetry(new ApiRequestError("bad", { status: 422 })),
    ).toBe(false);
  });

  it("403 não revela recurso e não dispara retry", () => {
    expect(
      isRecoverableForRetry(
        new ApiRequestError("denied", { status: 403, code: "forbidden" }),
      ),
    ).toBe(false);
  });
});

describe("T7 — rate limit e falhas sem confirmação são recuperáveis", () => {
  it("429 preserva a operação (retry manual respeitando Retry-After)", () => {
    const err = new ApiRequestError("limited", { status: 429, retryAfter: 30 });
    expect(err.retryAfter).toBe(30);
    expect(isRecoverableForRetry(err)).toBe(true);
  });

  it("erro de rede sem resposta → recuperável", () => {
    expect(isRecoverableForRetry(new TypeError("fetch failed"))).toBe(true);
  });

  it("5xx → recuperável", () => {
    expect(
      isRecoverableForRetry(new ApiRequestError("boom", { status: 503 })),
    ).toBe(true);
  });
});

describe("T8 — prepare-update sem idempotência fictícia", () => {
  it("operação captura só expected_revision e envia corpo real do contrato", async () => {
    const op = capturePrepareOperation("002469", "01", "rev-1", 7);
    expect(op).toEqual({
      kind: "prepare",
      code: "002469",
      store: "01",
      reviewId: "rev-1",
      expectedRevision: 7,
    });
    await executePrepareOperation(op);
    expect(prepareEnrichmentUpdate).toHaveBeenCalledWith(
      "002469", "01", "rev-1", 7,
    );
    // retry é a mesma chamada — sem chave inventada
    await executePrepareOperation(op);
    expect(vi.mocked(prepareEnrichmentUpdate).mock.calls[0]).toEqual(
      vi.mocked(prepareEnrichmentUpdate).mock.calls[1],
    );
  });
});

describe("reason_code opcional do contrato", () => {
  it("omite quando ausente e envia quando presente", () => {
    const without = captureSingleDecision("c", "s", "r", "f", "REJECT", 1, "k");
    const with_ = captureSingleDecision("c", "s", "r", "f", "REJECT", 1, "k", "OUTDATED");
    if (without.kind === "single" && with_.kind === "single") {
      expect("reason_code" in without.payload).toBe(false);
      expect(with_.payload.reason_code).toBe("OUTDATED");
    }
  });
});
