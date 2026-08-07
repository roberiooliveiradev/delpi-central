import { unwrapEnvelope, type ApiSuccessResponse } from "../types/api";
import type {
  PropostaComercialDetail,
  PropostaComercialListData,
  PropostaComercialPdfExportOverrides,
} from "../types/propostasComerciais";
import { apiDelpiUrl, httpGet, httpGetBlobWithMeta, httpPostBlob } from "./httpClient";

export const PROPOSTAS_COMERCIAIS_API_BASE = apiDelpiUrl("/propostas-comerciais");

export async function listPropostasComerciais(
  limit = 100,
  signal?: AbortSignal,
): Promise<PropostaComercialListData> {
  const query = new URLSearchParams({ limit: String(limit) });
  const response = await httpGet<ApiSuccessResponse<PropostaComercialListData>>(
    `${PROPOSTAS_COMERCIAIS_API_BASE}?${query.toString()}`,
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao listar propostas comerciais.");
}

export async function getPropostaComercial(
  propostaInterna: string,
  signal?: AbortSignal,
): Promise<PropostaComercialDetail> {
  const code = encodeURIComponent(propostaInterna.trim());
  const response = await httpGet<ApiSuccessResponse<PropostaComercialDetail>>(
    `${PROPOSTAS_COMERCIAIS_API_BASE}/${code}`,
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao carregar proposta comercial.");
}

export async function exportPropostaComercialPdf(
  propostaInterna: string,
  overrides?: PropostaComercialPdfExportOverrides,
  signal?: AbortSignal,
): Promise<{ blob: Blob; filename: string | null }> {
  const code = encodeURIComponent(propostaInterna.trim());
  const url = `${PROPOSTAS_COMERCIAIS_API_BASE}/${code}/pdf`;
  const result = overrides
    ? await httpPostBlob(url, overrides, { signal })
    : await httpGetBlobWithMeta(url, { signal });
  return { blob: result.blob, filename: result.filename };
}

export async function openPropostaComercialPdf(
  propostaInterna: string,
  overrides?: PropostaComercialPdfExportOverrides,
  signal?: AbortSignal,
): Promise<void> {
  const code = encodeURIComponent(propostaInterna.trim());
  const { blob, filename } = await exportPropostaComercialPdf(
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
