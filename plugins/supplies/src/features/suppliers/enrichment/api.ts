import { httpGet, httpPost, suppliesApiUrl } from "../../../api/httpClient";
import type {
  EnrichmentDecisionListEnvelope,
  EnrichmentDecisionPayload,
  EnrichmentPrepareUpdateResult,
  EnrichmentReviewListEnvelope,
  EnrichmentReviewPayload,
} from "./types";

function reviewsPath(code: string, store: string): string {
  return `/suppliers/${encodeURIComponent(code)}/${encodeURIComponent(store)}/enrichment-reviews`;
}

export function createEnrichmentReview(
  code: string,
  store: string,
  signal?: AbortSignal,
): Promise<EnrichmentReviewPayload> {
  return httpPost<EnrichmentReviewPayload>(suppliesApiUrl(reviewsPath(code, store)), {}, { signal });
}

export function listEnrichmentReviews(
  code: string,
  store: string,
  page: number,
  pageSize: number,
  signal?: AbortSignal,
): Promise<EnrichmentReviewListEnvelope> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  return httpGet<EnrichmentReviewListEnvelope>(
    suppliesApiUrl(`${reviewsPath(code, store)}?${params.toString()}`),
    { signal },
  );
}

export function getEnrichmentReview(
  code: string,
  store: string,
  reviewId: string,
  signal?: AbortSignal,
): Promise<EnrichmentReviewPayload> {
  return httpGet<EnrichmentReviewPayload>(
    suppliesApiUrl(`${reviewsPath(code, store)}/${encodeURIComponent(reviewId)}`),
    { signal },
  );
}

export function listEnrichmentDecisions(
  code: string,
  store: string,
  reviewId: string,
  signal?: AbortSignal,
): Promise<EnrichmentDecisionListEnvelope> {
  return httpGet<EnrichmentDecisionListEnvelope>(
    suppliesApiUrl(
      `${reviewsPath(code, store)}/${encodeURIComponent(reviewId)}/decisions`,
    ),
    { signal },
  );
}

export type EnrichmentDecisionRequest = {
  field_key: string;
  decision: "ACCEPT" | "REJECT";
  expected_revision: number;
  idempotency_key: string;
};

export function decideEnrichmentField(
  code: string,
  store: string,
  reviewId: string,
  body: EnrichmentDecisionRequest,
  signal?: AbortSignal,
): Promise<EnrichmentDecisionPayload> {
  return httpPost<EnrichmentDecisionPayload>(
    suppliesApiUrl(
      `${reviewsPath(code, store)}/${encodeURIComponent(reviewId)}/decisions`,
    ),
    body as unknown as Record<string, unknown>,
    { signal },
  );
}

export type EnrichmentBulkDecisionRequest = {
  field_keys: string[];
  decision: "ACCEPT" | "REJECT";
  expected_revision: number;
  idempotency_key: string;
};

export function decideEnrichmentBulk(
  code: string,
  store: string,
  reviewId: string,
  body: EnrichmentBulkDecisionRequest,
  signal?: AbortSignal,
): Promise<EnrichmentDecisionPayload> {
  return httpPost<EnrichmentDecisionPayload>(
    suppliesApiUrl(
      `${reviewsPath(code, store)}/${encodeURIComponent(reviewId)}/bulk-decisions`,
    ),
    body as unknown as Record<string, unknown>,
    { signal },
  );
}

export function prepareEnrichmentUpdate(
  code: string,
  store: string,
  reviewId: string,
  expectedRevision: number,
  signal?: AbortSignal,
): Promise<EnrichmentPrepareUpdateResult> {
  return httpPost<EnrichmentPrepareUpdateResult>(
    suppliesApiUrl(
      `${reviewsPath(code, store)}/${encodeURIComponent(reviewId)}/prepare-update`,
    ),
    { expected_revision: expectedRevision },
    { signal },
  );
}
