import { ApiRequestError } from "../../../api/httpClient";
import {
  decideEnrichmentBulk,
  decideEnrichmentField,
  prepareEnrichmentUpdate,
  type EnrichmentBulkDecisionRequest,
  type EnrichmentDecisionRequest,
} from "./api";
import type { EnrichmentDecisionPayload } from "./types";

/**
 * Operação de decisão capturada no momento da intenção do usuário.
 *
 * Invariante RETRY = SAME OPERATION: endpoint, review_id, payload e
 * idempotency_key ficam congelados aqui — o retry nunca reconstrói a
 * requisição a partir do estado React mutável (revisão ativa, seleção).
 */
export type SingleDecisionOperation = {
  kind: "single";
  code: string;
  store: string;
  reviewId: string;
  payload: EnrichmentDecisionRequest;
};

export type BulkDecisionOperation = {
  kind: "bulk";
  code: string;
  store: string;
  reviewId: string;
  payload: EnrichmentBulkDecisionRequest;
};

export type PrepareOperation = {
  kind: "prepare";
  code: string;
  store: string;
  reviewId: string;
  expectedRevision: number;
};

export type DecisionOperation = SingleDecisionOperation | BulkDecisionOperation;

export type RetryableOperation = DecisionOperation | PrepareOperation;

export function captureSingleDecision(
  code: string,
  store: string,
  reviewId: string,
  fieldKey: string,
  decision: "ACCEPT" | "REJECT",
  expectedRevision: number,
  idempotencyKey: string,
  reasonCode?: string,
): SingleDecisionOperation {
  return {
    kind: "single",
    code,
    store,
    reviewId,
    payload: {
      field_key: fieldKey,
      decision,
      expected_revision: expectedRevision,
      idempotency_key: idempotencyKey,
      ...(reasonCode ? { reason_code: reasonCode } : {}),
    },
  };
}

export function captureBulkDecision(
  code: string,
  store: string,
  reviewId: string,
  fieldKeys: readonly string[],
  decision: "ACCEPT" | "REJECT",
  expectedRevision: number,
  idempotencyKey: string,
  reasonCode?: string,
): BulkDecisionOperation {
  return {
    kind: "bulk",
    code,
    store,
    reviewId,
    payload: {
      field_keys: [...fieldKeys],
      decision,
      expected_revision: expectedRevision,
      idempotency_key: idempotencyKey,
      ...(reasonCode ? { reason_code: reasonCode } : {}),
    },
  };
}

/** prepare-update não aceita idempotency_key — só expected_revision (contrato S2). */
export function capturePrepareOperation(
  code: string,
  store: string,
  reviewId: string,
  expectedRevision: number,
): PrepareOperation {
  return { kind: "prepare", code, store, reviewId, expectedRevision };
}

/** Envia exatamente a requisição capturada — mesmo método, endpoint e corpo. */
export function executeDecisionOperation(
  op: DecisionOperation,
): Promise<EnrichmentDecisionPayload> {
  return op.kind === "single"
    ? decideEnrichmentField(op.code, op.store, op.reviewId, op.payload)
    : decideEnrichmentBulk(op.code, op.store, op.reviewId, op.payload);
}

export function executePrepareOperation(op: PrepareOperation) {
  return prepareEnrichmentUpdate(
    op.code,
    op.store,
    op.reviewId,
    op.expectedRevision,
  );
}

/**
 * Só falhas sem confirmação de estado merecem retry da mesma operação:
 * erro de rede (não-ApiRequestError), 5xx e 429 (respeitar Retry-After).
 * Conflitos 4xx (revisão, idempotência, já decidido) e validações nunca
 * disparam retry — exigem nova intenção do usuário.
 */
export function isRecoverableForRetry(err: unknown): boolean {
  if (!(err instanceof ApiRequestError)) return true;
  return err.status >= 500 || err.status === 429;
}
