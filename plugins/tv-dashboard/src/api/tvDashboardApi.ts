import { API_BASE, httpDelete, httpGet, httpGetBlob, httpPatch, httpPost, httpPostForm } from "./httpClient";

type ApiEnvelope<T> = { success: boolean; message?: string; data: T };

async function unwrap<T>(promise: Promise<ApiEnvelope<T>>): Promise<T> {
  const env = await promise;
  if (!env.success) throw new Error(env.message ?? "Erro na API.");
  return env.data;
}

export type PlaylistMasterConfig = {
  enabled?: boolean;
  background?: {
    type: "color" | "image" | "gradient";
    value?: string;
    assetId?: string;
    url?: string;
    from?: string;
    to?: string;
    angle?: number;
  };
  logo?: {
    assetId?: string;
    url?: string;
    frame?: { x?: number; y?: number; w?: number; h?: number };
    opacity?: number;
  };
};

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
  dataDefaults?: Record<string, unknown>;
  masterConfig?: PlaylistMasterConfig;
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
  /** Override da transição da playlist; omitido = herdar. */
  transitionStyle?: string | null;
};

export type NativeScreenCatalogItem = {
  key: string;
  label: string;
  category: string;
  defaultDurationSec: number;
  configSchema: Record<string, unknown>;
};

export type SlidePreset = {
  key: string;
  label: string;
  description?: string | null;
  slideType?: "native" | "external";
  durationSec?: number | null;
};

export type SlidePresetDetail = {
  slideType: "native" | "external";
  title: string;
  durationSec?: number | null;
  nativeScreenKey?: string;
  nativeConfig?: Record<string, unknown>;
  externalUrl?: string;
};

export type TvDashboardUiContent = {
  messages?: Record<string, string>;
  presentation?: Record<string, string | number>;
  admin?: Record<string, string>;
};

export type BranchScope = {
  mode: "unrestricted" | "scoped";
  allowConsolidated: boolean;
  branches: string[];
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
  presentationMeta?: {
    nativeErrorAdvanceSec: number;
    heartbeatIntervalSec: number;
  };
  slides: Array<{
    id: string;
    sortOrder: number;
    slideType: "native" | "external";
    durationSec: number;
    title: string;
    transitionStyle?: string | null;
    native?: { screenKey: string; config: Record<string, unknown>; data: Record<string, unknown> };
    external?: { url: string; sandbox?: string | null };
  }>;
};

export type PresentationStatus = {
  status: "online" | "offline" | "never";
  online: boolean;
  lastPresentedAt?: string | null;
  viewCount: number;
  heartbeatIntervalSec: number;
  staleAfterSec: number;
  secondsSinceLastPresentation?: number | null;
  isActive: boolean;
};

export type MediaAsset = {
  id: string;
  playlistId: string;
  storedName: string;
  originalName?: string | null;
  mimeType: string;
  mediaKind: "image" | "video" | "font";
  fileSizeBytes: number;
};

export function adminMediaUrl(playlistId: string, assetId: string) {
  return `${API_BASE}/playlists/${playlistId}/media/${assetId}`;
}

export async function uploadPlaylistMedia(playlistId: string, file: File) {
  const form = new FormData();
  form.append("file", file);
  return unwrap(
    httpPostForm<ApiEnvelope<MediaAsset>>(`${API_BASE}/playlists/${playlistId}/media`, form),
  );
}

export async function listPlaylistMedia(playlistId: string, mediaKind?: "image" | "video" | "font") {
  const query = mediaKind ? `?media_kind=${encodeURIComponent(mediaKind)}` : "";
  const data = await unwrap(
    httpGet<ApiEnvelope<{ items: MediaAsset[] }>>(
      `${API_BASE}/playlists/${playlistId}/media${query}`,
    ),
  );
  return data.items;
}

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

export async function getPresentationStatus(id: string) {
  return unwrap(
    httpGet<ApiEnvelope<PresentationStatus>>(`${API_BASE}/playlists/${id}/presentation-status`),
  );
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
    dataDefaults: Record<string, unknown>;
    masterConfig: PlaylistMasterConfig;
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

export type TvDataRouteCatalogItem = {
  operationId: string;
  label: string;
  category: string;
  description?: string;
  path?: string;
  allowedDisplayModes?: string[];
  suggestedDisplayModes?: string[];
  valueFields?: string[];
  defaultParams?: Record<string, unknown>;
  paramSchema?: Record<string, unknown>;
  fixedQueryParams?: Record<string, unknown>;
  tvConstraints?: Record<string, unknown>;
  metaShape?: string;
};

export async function listDataRoutes() {
  const data = await unwrap(
    httpGet<ApiEnvelope<{ items: TvDataRouteCatalogItem[] }>>(`${API_BASE}/data/routes`),
  );
  return data.items;
}

export async function previewDataBlockV2(body: {
  block: Record<string, unknown>;
  nativeConfig: Record<string, unknown>;
  playlistId?: string;
}) {
  return unwrap(
    httpPost<ApiEnvelope<{ block: Record<string, unknown> }>>(
      `${API_BASE}/data/preview-block`,
      body,
    ),
  );
}

/** @deprecated Prefer previewDataBlockV2 — não exige slide persistido. */
export async function previewDataBlock(
  playlistId: string,
  slideId: string,
  blockId: string,
  nativeConfig: Record<string, unknown>,
) {
  return unwrap(
    httpPost<ApiEnvelope<{ block: Record<string, unknown> }>>(
      `${API_BASE}/playlists/${playlistId}/slides/${slideId}/preview-data-block`,
      { blockId, nativeConfig },
    ),
  );
}

export async function listNativeScreens() {
  const data = await unwrap(
    httpGet<ApiEnvelope<{ items: NativeScreenCatalogItem[] }>>(`${API_BASE}/native-screens`),
  );
  return data.items;
}

export async function listSlidePresets() {
  const data = await unwrap(
    httpGet<ApiEnvelope<{ items: SlidePreset[] }>>(`${API_BASE}/slide-presets`),
  );
  return data.items;
}

export async function getSlidePreset(presetKey: string) {
  return unwrap(httpGet<ApiEnvelope<SlidePresetDetail>>(`${API_BASE}/slide-presets/${presetKey}`));
}

export async function getUiContent() {
  return unwrap(httpGet<ApiEnvelope<TvDashboardUiContent>>(`${API_BASE}/content/ui`));
}

export async function getBranchScope() {
  return unwrap(httpGet<ApiEnvelope<BranchScope>>(`${API_BASE}/content/branch-scope`));
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
    transitionStyle?: string | null;
  },
) {
  return unwrap(
    httpPost<ApiEnvelope<Slide>>(`${API_BASE}/playlists/${playlistId}/slides`, body),
  );
}

export async function addSlideFromPreset(
  playlistId: string,
  body: { presetKey: string; branch?: string },
) {
  return unwrap(
    httpPost<ApiEnvelope<Slide>>(
      `${API_BASE}/playlists/${playlistId}/slides/from-preset`,
      body,
    ),
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
    isActive: boolean;
    transitionStyle: string | null;
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
