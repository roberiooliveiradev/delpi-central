import { unwrapEnvelope, type ApiSuccessResponse } from "../types/api";
import type {
  ProposalDocumentDetail,
  ProposalDocumentListData,
  ProposalDocumentPdfExportOverrides,
} from "../types/proposalsDocument";
import { commercialApiUrl, httpGet, httpGetBlobWithMeta, httpPostBlob } from "./httpClient";

/** BFF commercial-api → api-delpi commercial-proposals (ADY). */
export const COMMERCIAL_PROPOSALS_API_BASE = commercialApiUrl("/proposal-documents");

export async function listProposalsDocuments(
  limit = 100,
  signal?: AbortSignal,
): Promise<ProposalDocumentListData> {
  const query = new URLSearchParams({ limit: String(limit) });
  const response = await httpGet<ApiSuccessResponse<ProposalDocumentListData>>(
    `${COMMERCIAL_PROPOSALS_API_BASE}/?${query.toString()}`,
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao listar propostas comerciais.");
}

export async function getProposalDocument(
  propostaInterna: string,
  signal?: AbortSignal,
): Promise<ProposalDocumentDetail> {
  const code = encodeURIComponent(propostaInterna.trim());
  const response = await httpGet<ApiSuccessResponse<ProposalDocumentDetail>>(
    `${COMMERCIAL_PROPOSALS_API_BASE}/${code}`,
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao carregar proposta comercial.");
}

export async function exportProposalDocumentPdf(
  propostaInterna: string,
  overrides?: ProposalDocumentPdfExportOverrides,
  signal?: AbortSignal,
): Promise<{ blob: Blob; filename: string | null }> {
  const code = encodeURIComponent(propostaInterna.trim());
  const url = `${COMMERCIAL_PROPOSALS_API_BASE}/${code}/pdf`;
  const result = overrides
    ? await httpPostBlob(url, overrides, { signal })
    : await httpGetBlobWithMeta(url, { signal });
  return { blob: result.blob, filename: result.filename };
}

export async function openProposalDocumentPdf(
  propostaInterna: string,
  overrides?: ProposalDocumentPdfExportOverrides,
  signal?: AbortSignal,
): Promise<void> {
  const code = encodeURIComponent(propostaInterna.trim());
  const { blob, filename } = await exportProposalDocumentPdf(
    propostaInterna,
    overrides,
    signal,
  );
  const objectUrl = window.URL.createObjectURL(blob);
  const opened = window.open(objectUrl, "_blank", "noopener,noreferrer");
  if (!opened) {
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = filename ?? `proposta-${code}.pdf`;
    link.rel = "noopener";
    document.body.appendChild(link);
    link.click();
    link.remove();
  }
  window.setTimeout(() => window.URL.revokeObjectURL(objectUrl), 60_000);
}
