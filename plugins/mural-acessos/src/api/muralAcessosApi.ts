import {
  httpDelete,
  httpGet,
  httpGetBlob,
  httpPost,
  httpPostForm,
  httpPut,
  unwrapApiDelpiEnvelope,
} from "./httpClient";

const API_BASE = "/apps/api-delpi/mural-acessos";

export type MuralHub = {
  id: string;
  title: string;
  subtitle: string;
  publicToken: string;
  publicPath: string;
  publicUrl: string;
  qrUrl: string;
  linkCount?: number;
};

export type MuralHubPayload = {
  title: string;
  subtitle: string;
  publicToken: string;
};

export type MuralLink = {
  id: string;
  hubId: string;
  title: string;
  url: string;
  description: string;
  orderIndex: number;
  active: boolean;
  hasImage: boolean;
  imageUrl: string | null;
};

export type MuralLinkPayload = {
  title: string;
  url: string;
  description: string;
  active: boolean;
};

type RequestOptions = { signal?: AbortSignal };

export async function fetchHubs(options: RequestOptions = {}): Promise<MuralHub[]> {
  const response = await httpGet<unknown>(`${API_BASE}/hubs`, options);
  return unwrapApiDelpiEnvelope<MuralHub[]>(response as never, "Erro ao carregar os murais.");
}

export async function createHub(
  payload: MuralHubPayload,
  options: RequestOptions = {},
): Promise<MuralHub> {
  const response = await httpPost<unknown>(`${API_BASE}/hubs`, payload, options);
  return unwrapApiDelpiEnvelope<MuralHub>(response as never, "Erro ao cadastrar o mural.");
}

export async function fetchHub(hubId: string, options: RequestOptions = {}): Promise<MuralHub> {
  const response = await httpGet<unknown>(
    `${API_BASE}/hubs/${encodeURIComponent(hubId)}`,
    options,
  );
  return unwrapApiDelpiEnvelope<MuralHub>(response as never, "Erro ao carregar o mural.");
}

export async function updateHub(
  hubId: string,
  payload: MuralHubPayload,
  options: RequestOptions = {},
): Promise<MuralHub> {
  const response = await httpPut<unknown>(
    `${API_BASE}/hubs/${encodeURIComponent(hubId)}`,
    payload,
    options,
  );
  return unwrapApiDelpiEnvelope<MuralHub>(response as never, "Erro ao salvar o mural.");
}

export async function deleteHub(hubId: string, options: RequestOptions = {}): Promise<void> {
  const response = await httpDelete<unknown>(
    `${API_BASE}/hubs/${encodeURIComponent(hubId)}`,
    options,
  );
  unwrapApiDelpiEnvelope(response as never, "Erro ao remover o mural.");
}

export async function fetchLinks(hubId: string, options: RequestOptions = {}): Promise<MuralLink[]> {
  const response = await httpGet<unknown>(
    `${API_BASE}/hubs/${encodeURIComponent(hubId)}/links`,
    options,
  );
  return unwrapApiDelpiEnvelope<MuralLink[]>(response as never, "Erro ao carregar os acessos.");
}

export async function createLink(
  hubId: string,
  payload: MuralLinkPayload,
  options: RequestOptions = {},
): Promise<MuralLink> {
  const response = await httpPost<unknown>(
    `${API_BASE}/hubs/${encodeURIComponent(hubId)}/links`,
    payload,
    options,
  );
  return unwrapApiDelpiEnvelope<MuralLink>(response as never, "Erro ao cadastrar o acesso.");
}

export async function updateLink(
  linkId: string,
  payload: MuralLinkPayload,
  options: RequestOptions = {},
): Promise<MuralLink> {
  const response = await httpPut<unknown>(
    `${API_BASE}/links/${encodeURIComponent(linkId)}`,
    payload,
    options,
  );
  return unwrapApiDelpiEnvelope<MuralLink>(response as never, "Erro ao atualizar o acesso.");
}

export async function deleteLink(linkId: string, options: RequestOptions = {}): Promise<void> {
  const response = await httpDelete<unknown>(
    `${API_BASE}/links/${encodeURIComponent(linkId)}`,
    options,
  );
  unwrapApiDelpiEnvelope(response as never, "Erro ao remover o acesso.");
}

export async function reorderLinks(
  hubId: string,
  orderedIds: string[],
  options: RequestOptions = {},
): Promise<MuralLink[]> {
  const response = await httpPut<unknown>(
    `${API_BASE}/hubs/${encodeURIComponent(hubId)}/links/reorder`,
    { ordered_ids: orderedIds },
    options,
  );
  return unwrapApiDelpiEnvelope<MuralLink[]>(response as never, "Erro ao reordenar.");
}

export async function uploadLinkImage(
  linkId: string,
  file: File,
  options: RequestOptions = {},
): Promise<MuralLink> {
  const form = new FormData();
  form.append("file", file);
  const response = await httpPostForm<unknown>(
    `${API_BASE}/links/${encodeURIComponent(linkId)}/image`,
    form,
    options,
  );
  return unwrapApiDelpiEnvelope<MuralLink>(response as never, "Erro ao enviar a imagem.");
}

export async function deleteLinkImage(
  linkId: string,
  options: RequestOptions = {},
): Promise<MuralLink> {
  const response = await httpDelete<unknown>(
    `${API_BASE}/links/${encodeURIComponent(linkId)}/image`,
    options,
  );
  return unwrapApiDelpiEnvelope<MuralLink>(response as never, "Erro ao remover a imagem.");
}

export async function fetchAuthenticatedImage(
  imageUrl: string,
  options: RequestOptions = {},
): Promise<string> {
  const blob = await httpGetBlob(imageUrl, options);
  return URL.createObjectURL(blob);
}

export async function fetchHubQrPng(hubId: string, options: RequestOptions = {}): Promise<string> {
  const blob = await httpGetBlob(
    `${API_BASE}/hubs/${encodeURIComponent(hubId)}/qr.png`,
    options,
  );
  return URL.createObjectURL(blob);
}

export function resolvePublicMenuUrl(hub: MuralHub): string {
  if (hub.publicUrl.startsWith("http://") || hub.publicUrl.startsWith("https://")) {
    return hub.publicUrl;
  }
  return `${window.location.origin}${hub.publicPath}`;
}

export function suggestPublicToken(title: string): string {
  return title
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 40);
}
