import type { ProcessoArquivo, ProcessoArquivoList, ProcessoArquivoType } from "../../types/processoArquivo";
import { TRANSFORMOMETRO_API_BASE, buildAuthHeaders } from "./transformometroApiBase";

type ApiEnvelope<T> = {
  success: boolean;
  message: string;
  data: T;
};

async function parseEnvelope<T>(response: Response): Promise<T> {
  const body = (await response.json()) as ApiEnvelope<T>;
  if (!response.ok || !body.success) {
    throw new Error(body.message || `Erro HTTP ${response.status}`);
  }
  return body.data;
}

export async function fetchProcessoArquivos(
  processoId: string,
  getAccessToken?: () => string | undefined
): Promise<ProcessoArquivo[]> {
  const response = await fetch(`${TRANSFORMOMETRO_API_BASE}/processos/${processoId}/arquivos`, {
    headers: buildAuthHeaders(getAccessToken),
  });
  const data = await parseEnvelope<ProcessoArquivoList>(response);
  return data.items ?? [];
}

export async function uploadProcessoArquivo(
  processoId: string,
  params: {
    tipo: ProcessoArquivoType;
    file?: File;
    descricao?: string;
    urlExterna?: string;
  },
  getAccessToken?: () => string | undefined
): Promise<ProcessoArquivo> {
  const form = new FormData();
  form.set("tipo", params.tipo);
  if (params.descricao) form.set("descricao", params.descricao);
  if (params.urlExterna) form.set("url_externa", params.urlExterna);
  if (params.file) form.append("file", params.file);

  const response = await fetch(`${TRANSFORMOMETRO_API_BASE}/processos/${processoId}/arquivos`, {
    method: "POST",
    headers: buildAuthHeaders(getAccessToken),
    body: form,
  });
  return parseEnvelope<ProcessoArquivo>(response);
}

export async function deleteProcessoArquivo(
  processoId: string,
  arquivoId: string,
  getAccessToken?: () => string | undefined
): Promise<void> {
  const response = await fetch(
    `${TRANSFORMOMETRO_API_BASE}/processos/${processoId}/arquivos/${arquivoId}`,
    {
      method: "DELETE",
      headers: buildAuthHeaders(getAccessToken),
    }
  );
  await parseEnvelope(response);
}

export function processoArquivoFileUrl(processoId: string, arquivoId: string): string {
  return `${TRANSFORMOMETRO_API_BASE}/processos/${processoId}/arquivos/${arquivoId}/arquivo`;
}

export async function fetchProcessoArquivoObjectUrl(
  processoId: string,
  arquivoId: string,
  getAccessToken?: () => string | undefined
): Promise<string> {
  const response = await fetch(processoArquivoFileUrl(processoId, arquivoId), {
    headers: buildAuthHeaders(getAccessToken),
  });
  if (!response.ok) {
    throw new Error(`Erro HTTP ${response.status}`);
  }
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}

export {
  createPendingUploadId,
  formatEvidenceFileSize,
  inferEvidenceTypeFromFile as inferProcessoArquivoTypeFromFile,
} from "./transformometroEvidenceApi";

export function canPreviewProcessoArquivo(arquivo: ProcessoArquivo): boolean {
  if (arquivo.tipo === "link") return false;
  const mime = (arquivo.tipo_mime ?? "").toLowerCase();
  return mime.startsWith("image/") || mime === "application/pdf";
}
