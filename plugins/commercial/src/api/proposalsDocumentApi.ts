import { unwrapEnvelope, type ApiSuccessResponse } from "../types/api";
import type {
  ProposalDocumentDetail,
  ProposalDocumentListData,
  ProposalDocumentPdfExportOverrides,
} from "../types/proposalsDocument";
import { apiDelpiUrl, httpGet, httpGetBlobWithMeta, httpPostBlob } from "./httpClient";

/** Path HTTP legado da api-delpi (não traduzir — rota real é `/propostas-comerciais`). */
export const PROPOSALS_DOCUMENT_API_BASE = apiDelpiUrl("/propostas-comerciais");

export async function listProposalsDocuments(
  limit = 100,
  signal?: AbortSignal,
): Promise<ProposalDocumentListData> {
  const query = new URLSearchParams({ limit: String(limit) });
  const response = await httpGet<ApiSuccessResponse<ProposalDocumentListData>>(
    `${PROPOSALS_DOCUMENT_API_BASE}?${query.toString()}`,
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
    `${PROPOSALS_DOCUMENT_API_BASE}/${code}`,
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
  const url = `${PROPOSALS_DOCUMENT_API_BASE}/${code}/pdf`;
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
