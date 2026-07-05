import { API_BASE, httpDelete, httpGet, httpGetBlob, httpPatch, httpPost } from "./httpClient";

type ApiEnvelope<T> = { success: boolean; message?: string; data: T };

async function unwrap<T>(promise: Promise<ApiEnvelope<T>>): Promise<T> {
  const env = await promise;
  if (!env.success) throw new Error(env.message ?? "Erro na API.");
  return env.data;
}

export type Playlist = {
  id: string;
  publicToken: string;
  name: string;
  description?: string | null;
  viewportProfile: string;
  transitionStyle: string;
  defaultDurationSec: number;
  globalRefreshSec: number;
  isActive: boolean;
  viewCount: number;
  lastPresentedAt?: string | null;
  publicUrl?: string;
  slides?: Slide[];
};

export type Slide = {
  id: string;
  playlistId: string;
  sortOrder: number;
  slideType: "native" | "external";
  durationSec?: number | null;
  title: string;
  nativeScreenKey?: string | null;
  nativeConfig?: Record<string, unknown>;
  externalUrl?: string | null;
  externalSandbox?: string | null;
  isActive: boolean;
};

export type NativeScreenCatalogItem = {
  key: string;
  label: string;
  category: string;
  defaultDurationSec: number;
  configSchema: Record<string, unknown>;
};

export type PresentationPayload = {
  playlist: {
    id: string;
    name: string;
    description?: string | null;
    viewportProfile: string;
    transitionStyle: string;
    globalRefreshSec: number;
    defaultDurationSec: number;
    publicUrl?: string;
  };
  slides: Array<{
    id: string;
    sortOrder: number;
    slideType: "native" | "external";
    durationSec: number;
    title: string;
    native?: { screenKey: string; config: Record<string, unknown>; data: Record<string, unknown> };
    external?: { url: string; sandbox?: string | null };
  }>;
};

export async function listPlaylists() {
  const data = await unwrap(httpGet<ApiEnvelope<{ items: Playlist[] }>>(`${API_BASE}/playlists`));
  return data.items;
}

export async function createPlaylist(name: string, description?: string) {
  return unwrap(
    httpPost<ApiEnvelope<Playlist>>(`${API_BASE}/playlists`, { name, description }),
  );
}

export async function getPlaylist(id: string) {
  return unwrap(httpGet<ApiEnvelope<Playlist>>(`${API_BASE}/playlists/${id}`));
}

export async function updatePlaylist(
  id: string,
  body: Partial<{
    name: string;
    description: string;
    viewportProfile: string;
    transitionStyle: string;
    defaultDurationSec: number;
    globalRefreshSec: number;
  }>,
) {
  return unwrap(httpPatch<ApiEnvelope<Playlist>>(`${API_BASE}/playlists/${id}`, body));
}

export async function deletePlaylist(id: string) {
  return unwrap(httpDelete<ApiEnvelope<null>>(`${API_BASE}/playlists/${id}`));
}

export async function deactivatePlaylist(id: string) {
  return unwrap(httpPost<ApiEnvelope<Playlist>>(`${API_BASE}/playlists/${id}/deactivate`, {}));
}

export async function activatePlaylist(id: string) {
  return unwrap(httpPost<ApiEnvelope<Playlist>>(`${API_BASE}/playlists/${id}/activate`, {}));
}

export async function duplicatePlaylist(id: string) {
  return unwrap(
    httpPost<ApiEnvelope<Playlist>>(`${API_BASE}/playlists/${id}/duplicate`, {}),
  );
}

export async function regeneratePlaylistToken(id: string) {
  return unwrap(
    httpPost<ApiEnvelope<Playlist>>(`${API_BASE}/playlists/${id}/regenerate-token`, {}),
  );
}

export async function duplicateSlide(playlistId: string, slideId: string) {
  return unwrap(
    httpPost<ApiEnvelope<Slide>>(
      `${API_BASE}/playlists/${playlistId}/slides/${slideId}/duplicate`,
      {},
    ),
  );
}

export async function getPreviewPayload(id: string) {
  return unwrap(
    httpGet<ApiEnvelope<PresentationPayload>>(`${API_BASE}/playlists/${id}/preview-payload`),
  );
}

export async function listNativeScreens() {
  const data = await unwrap(
    httpGet<ApiEnvelope<{ items: NativeScreenCatalogItem[] }>>(`${API_BASE}/native-screens`),
  );
  return data.items;
}

export async function addSlide(
  playlistId: string,
  body: {
    slideType: "native" | "external";
    title: string;
    durationSec?: number;
    nativeScreenKey?: string;
    nativeConfig?: Record<string, unknown>;
    externalUrl?: string;
  },
) {
  return unwrap(
    httpPost<ApiEnvelope<Slide>>(`${API_BASE}/playlists/${playlistId}/slides`, body),
  );
}

export async function deleteSlide(playlistId: string, slideId: string) {
  return unwrap(
    httpDelete<ApiEnvelope<null>>(`${API_BASE}/playlists/${playlistId}/slides/${slideId}`),
  );
}

export async function reorderSlides(
  playlistId: string,
  items: Array<{ id: string; sortOrder: number }>,
) {
  return unwrap(
    httpPost<ApiEnvelope<{ slides: Slide[] }>>(
      `${API_BASE}/playlists/${playlistId}/slides/reorder`,
      { items },
    ),
  );
}

export async function updateSlide(
  playlistId: string,
  slideId: string,
  body: Partial<{
    title: string;
    durationSec: number;
    nativeConfig: Record<string, unknown>;
    externalUrl: string;
  }>,
) {
  return unwrap(
    httpPatch<ApiEnvelope<Slide>>(`${API_BASE}/playlists/${playlistId}/slides/${slideId}`, body),
  );
}

export function qrDownloadUrl(playlistId: string) {
  return `${API_BASE}/playlists/${playlistId}/qr`;
}

export async function downloadQrPng(playlistId: string) {
  return httpGetBlob(qrDownloadUrl(playlistId));
}
