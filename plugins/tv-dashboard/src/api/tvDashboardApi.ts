import { API_BASE, httpDelete, httpGet, httpGetBlob, httpPatch, httpPost, httpPostBlob, httpPostForm } from "./httpClient";
import { resolvePreviewPlaylistId } from "../utils/previewPlaylistId";

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

export type PlaylistSection = {
  id: string;
  playlistId: string;
  name: string;
  sortOrder: number;
  isCollapsed?: boolean;
  isActive?: boolean;
  /** Seção principal do deck; única por playlist; chrome oculto quando é a única. */
  isMain?: boolean;
  defaultDurationSec?: number | null;
  transitionStyle?: string | null;
  masterConfig?: PlaylistMasterConfig;
  createdAt?: string | null;
  updatedAt?: string | null;
};

export type Playlist = {
  id: string;
  /** Revisão otimista do agregado, quando entregue pelo backend. */
  revision?: number;
  currentRevision?: number;
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
  ownerUserId?: string | null;
  createdBy?: string | null;
  /** owner | editor | viewer — preenchido pela API de acesso. */
  accessRole?: "owner" | "editor" | "viewer";
  dataDefaults?: Record<string, unknown>;
  masterConfig?: PlaylistMasterConfig;
  sections?: PlaylistSection[];
  slides?: Slide[];
  /** 1ª tela (preferência: ativa) — capa na lista da home. */
  coverSlide?: Slide | null;
};

export type PlaylistShare = {
  id: string;
  playlistId: string;
  targetUserId: string;
  role: "viewer" | "editor";
  createdBy?: string | null;
  createdAt?: string | null;
  /** Enriquecimento opcional no cliente (diretório). */
  displayName?: string;
  email?: string;
};

export type PlaylistEditInvite = {
  id: string;
  playlistId: string;
  token: string;
  role: "viewer" | "editor";
  redeemPath?: string;
  expiresAt?: string | null;
  createdAt?: string | null;
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
  /** Seção da programação; null = sem seção. */
  sectionId?: string | null;
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
  source?: "json" | "mdd" | string;
};

export type SlidePresetDetail = {
  slideType: "native" | "external";
  title: string;
  durationSec?: number | null;
  nativeScreenKey?: string;
  nativeConfig?: Record<string, unknown>;
  externalUrl?: string;
  source?: string;
};

export type SlideTemplateStatus = "draft" | "published" | "archived";

export type SlideTemplate = {
  id: string;
  key: string;
  label: string;
  description?: string | null;
  nativeScreenKey: string;
  nativeConfig: Record<string, unknown>;
  durationSec?: number | null;
  status: SlideTemplateStatus;
  isSystem: boolean;
  version: number;
  thumbnailJson?: Record<string, unknown> | null;
  ownerUserId?: string | null;
  createdAt?: string | null;
  updatedAt?: string | null;
  updatedBy?: string | null;
  slideType?: "native";
  title?: string;
  source?: string;
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
    masterConfig?: PlaylistMasterConfig;
  };
  presentationMeta?: {
    nativeErrorAdvanceSec: number;
    heartbeatIntervalSec: number;
  };
  sections?: Array<{
    id: string;
    name: string;
    sortOrder: number;
    isActive?: boolean;
    defaultDurationSec?: number | null;
    transitionStyle?: string | null;
    masterConfig?: PlaylistMasterConfig;
  }>;
  slides: Array<{
    id: string;
    sortOrder: number;
    slideType: "native" | "external";
    durationSec: number;
    title: string;
    sectionId?: string | null;
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
  contentRevision?: string;
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

export type PlaylistHistoryPreview = {
  playlistName?: string;
  slideCount?: number;
  slideTitles?: string[];
  selectedSlideId?: string | null;
};

export type PlaylistHistorySlideChange =
  | string
  | {
      id?: string | null;
      title?: string | null;
      fields?: string[];
    };

export type PlaylistHistoryChangeTotals = {
  playlistFields?: number;
  added?: number;
  removed?: number;
  updated?: number;
  reordered?: number;
  /** Aliases explícitos aceitos durante a evolução do contrato. */
  playlistFieldsChanged?: number;
  slidesAdded?: number;
  slidesRemoved?: number;
  slidesUpdated?: number;
  slidesReordered?: number;
  total?: number;
};

export type PlaylistHistoryChange = {
  available: boolean;
  comparedToRevision?: number | null;
  playlistFields?: string[];
  slides?: {
    added?: PlaylistHistorySlideChange[];
    removed?: PlaylistHistorySlideChange[];
    updated?: PlaylistHistorySlideChange[];
    reordered?: PlaylistHistorySlideChange[] | boolean;
  };
  totals?: PlaylistHistoryChangeTotals;
};

export type PlaylistHistoryEntry = {
  snapshotId: string;
  revision: number;
  createdAt: string;
  authorId?: string | null;
  authorName?: string | null;
  authorEmail?: string | null;
  reason?: string | null;
  preview?: PlaylistHistoryPreview | null;
  change?: PlaylistHistoryChange | null;
};

export type PlaylistHistoryPage = {
  items: PlaylistHistoryEntry[];
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
  hasNext: boolean;
  currentRevision: number | null;
};

export type PlaylistHistorySnapshot = PlaylistHistoryEntry & {
  snapshot: {
    playlist: Partial<Playlist>;
    slides: Slide[];
  };
};

export function adminMediaUrl(playlistId: string, assetId: string) {
  return `${API_BASE}/playlists/${playlistId}/media/${assetId}`;
}

/** Mídia do link público — `<img>`/CSS no filmstrip e na prévia sem JWT. */
export function publicPresentMediaUrl(publicToken: string, assetId: string) {
  return `${API_BASE}/public/present/${encodeURIComponent(publicToken)}/media/${assetId}`;
}

export async function uploadPlaylistMedia(
  playlistId: string,
  file: File,
  options?: { signal?: AbortSignal; onProgress?: (ratio: number) => void },
) {
  const form = new FormData();
  form.append("file", file);
  return unwrap(
    httpPostForm<ApiEnvelope<MediaAsset>>(
      `${API_BASE}/playlists/${playlistId}/media`,
      form,
      options,
    ),
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

export async function deletePlaylistMedia(playlistId: string, assetId: string) {
  return unwrap(
    httpDelete<ApiEnvelope<{ id: string; deleted: boolean }>>(
      `${API_BASE}/playlists/${playlistId}/media/${assetId}`,
    ),
  );
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

export async function listPlaylistHistory(
  playlistId: string,
  options: { page?: number; pageSize?: number } = {},
) {
  const page = Math.max(1, options.page ?? 1);
  const pageSize = Math.min(100, Math.max(1, options.pageSize ?? 10));
  const params = new URLSearchParams({
    page: String(page),
    pageSize: String(pageSize),
  });
  const data = await unwrap(
    httpGet<
      ApiEnvelope<{
        items: PlaylistHistoryEntry[];
        page: number;
        pageSize: number;
        total: number;
        totalPages: number;
        currentRevision: number | null;
      }>
    >(
      `${API_BASE}/playlists/${playlistId}/history?${params.toString()}`,
    ),
  );
  return {
    ...data,
    hasNext: data.page < data.totalPages,
    currentRevision: data.currentRevision,
  } satisfies PlaylistHistoryPage;
}

export async function getPlaylistHistorySnapshot(playlistId: string, snapshotId: string) {
  const data = await unwrap(
    httpGet<
      ApiEnvelope<{
        snapshotId: string;
        revision: number;
        authorId?: string | null;
        authorName?: string | null;
        authorEmail?: string | null;
        reason?: string | null;
        createdAt: string;
        preview?: PlaylistHistoryPreview | null;
        change?: PlaylistHistoryChange | null;
        playlist: Playlist;
      }>
    >(
      `${API_BASE}/playlists/${playlistId}/history/${encodeURIComponent(snapshotId)}`,
    ),
  );
  const { slides = [], ...playlist } = data.playlist;
  return {
    snapshotId: data.snapshotId,
    revision: data.revision,
    createdAt: data.createdAt,
    authorId: data.authorId,
    authorName: data.authorName,
    authorEmail: data.authorEmail,
    reason: data.reason,
    preview: data.preview,
    change: data.change,
    snapshot: { playlist, slides },
  } satisfies PlaylistHistorySnapshot;
}

export async function restorePlaylistHistorySnapshot(
  playlistId: string,
  snapshotId: string,
  expectedRevision: number,
) {
  const data = await unwrap(
    httpPost<ApiEnvelope<{ playlist: Playlist }>>(
      `${API_BASE}/playlists/${playlistId}/history/${encodeURIComponent(snapshotId)}/restore`,
      { expectedRevision },
    ),
  );
  return data.playlist;
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

export type DeckImportBindingReport = {
  operationId: string;
  slideSourceId?: string | null;
  blockId?: string | null;
  blockType?: string | null;
  status: "ok" | "warning" | "error";
  message: string;
};

export type DeckImportPreview = {
  valid: boolean;
  errors: string[];
  warnings?: string[];
  format?: string;
  schemaVersion?: string;
  importToken?: string;
  playlistName?: string;
  source?: {
    playlistId?: string;
    playlistName?: string;
    exportedBy?: string | null;
    exportedAt?: string;
  };
  stats?: {
    slideCount?: number;
    sectionCount?: number;
    mediaCount?: number;
    bindingCount?: number;
  };
  slides?: Array<{
    sourceId?: string;
    title?: string;
    slideType?: string;
    sortOrder?: number;
  }>;
  sections?: Array<{
    sourceId?: string;
    name?: string;
    isMain?: boolean;
    sortOrder?: number;
  }>;
  bindings?: DeckImportBindingReport[];
};

export async function exportPlaylistDeck(id: string): Promise<Blob> {
  return httpGetBlob(`${API_BASE}/playlists/${id}/export`);
}

export async function previewPlaylistDeckImport(file: File): Promise<DeckImportPreview> {
  const form = new FormData();
  form.append("file", file);
  return unwrap(
    httpPostForm<ApiEnvelope<DeckImportPreview>>(`${API_BASE}/playlists/import/preview`, form),
  );
}

export async function applyPlaylistDeckImport(body: {
  importToken: string;
  nameOverride?: string;
  activateAfterImport?: boolean;
  bindingPolicy?: "lenient" | "strict";
}): Promise<Playlist> {
  return unwrap(
    httpPost<ApiEnvelope<Playlist>>(`${API_BASE}/playlists/import/apply`, body),
  );
}

export async function regeneratePlaylistToken(id: string) {
  return unwrap(
    httpPost<ApiEnvelope<Playlist>>(`${API_BASE}/playlists/${id}/regenerate-token`, {}),
  );
}

export async function listPlaylistShares(playlistId: string) {
  const data = await unwrap(
    httpGet<ApiEnvelope<{ items: PlaylistShare[] }>>(
      `${API_BASE}/playlists/${playlistId}/shares`,
    ),
  );
  return data.items;
}

export async function upsertPlaylistShare(
  playlistId: string,
  body: { targetUserId: string; role: "viewer" | "editor" },
) {
  return unwrap(
    httpPost<ApiEnvelope<PlaylistShare>>(`${API_BASE}/playlists/${playlistId}/shares`, body),
  );
}

export async function revokePlaylistShare(playlistId: string, targetUserId: string) {
  return unwrap(
    httpDelete<ApiEnvelope<null>>(
      `${API_BASE}/playlists/${playlistId}/shares/${encodeURIComponent(targetUserId)}`,
    ),
  );
}

export async function createPlaylistEditInvite(
  playlistId: string,
  role: "viewer" | "editor" = "editor",
) {
  return unwrap(
    httpPost<ApiEnvelope<PlaylistEditInvite>>(
      `${API_BASE}/playlists/${playlistId}/edit-invites`,
      { role },
    ),
  );
}

export async function revokePlaylistEditInvites(playlistId: string) {
  return unwrap(
    httpPost<ApiEnvelope<{ revoked: number }>>(
      `${API_BASE}/playlists/${playlistId}/edit-invites/revoke`,
      {},
    ),
  );
}

export async function acceptPlaylistEditInvite(token: string) {
  return unwrap(
    httpPost<ApiEnvelope<{ playlistId: string; role: string; share: PlaylistShare }>>(
      `${API_BASE}/playlists/edit-invites/accept`,
      { token },
    ),
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

export type PreviewFilterOverrides = {
  slide?: Record<string, string | number | boolean | null>;
  bySourceId?: Record<string, Record<string, string | number | boolean | null>>;
};

export async function getPreviewPayload(id: string, filters?: PreviewFilterOverrides | null) {
  const params = new URLSearchParams();
  if (filters) {
    const slide = filters.slide ?? {};
    const bySourceId = filters.bySourceId ?? {};
    if (Object.keys(slide).length > 0 || Object.keys(bySourceId).length > 0) {
      params.set("filters", JSON.stringify({ slide, bySourceId }));
    }
  }
  const qs = params.toString();
  return unwrap(
    httpGet<ApiEnvelope<PresentationPayload>>(
      `${API_BASE}/playlists/${id}/preview-payload${qs ? `?${qs}` : ""}`,
    ),
  );
}

export type TvDataRouteFieldType = "number" | "string" | "date";

export type TvDataRouteCatalogItem = {
  operationId: string;
  label: string;
  category: string;
  description?: string;
  /** Texto de audiência curado (overlay) — prioridade sobre description no catálogo. */
  whenToUse?: string;
  path?: string;
  allowedDisplayModes?: string[];
  suggestedDisplayModes?: string[];
  valueFields?: string[];
  valueFieldLabels?: Record<string, string>;
  /** Tipos curados (overlay) — sugerem eixo X vs Y. */
  valueFieldTypes?: Record<string, TvDataRouteFieldType>;
  defaultParams?: Record<string, unknown>;
  paramSchema?: Record<string, unknown>;
  fixedQueryParams?: Record<string, unknown>;
  tvConstraints?: Record<string, unknown>;
  /** Sem datas na query → API devolve histórico completo (não força últimos N dias). */
  openEndedDateRange?: boolean;
  metaShape?: string;
  /** Nomes antigos do catálogo — hydrate limpa snapshots. */
  labelAliases?: string[];
  /** Preset de steps Power Query sugeridos pelo overlay da rota. */
  suggestedTransformSteps?: Array<Record<string, unknown>>;
};

export async function listDataRoutes() {
  const data = await unwrap(
    httpGet<ApiEnvelope<{ items: TvDataRouteCatalogItem[] }>>(`${API_BASE}/data/routes`),
  );
  return data.items;
}

export type TvDataRouteSuggestion = TvDataRouteCatalogItem & {
  reason?: string;
  score?: number | null;
};

export async function suggestDataRoutes(query: string, limit = 5) {
  return unwrap(
    httpPost<
      ApiEnvelope<{
        query: string;
        suggestions: TvDataRouteSuggestion[];
        total: number;
        degraded?: boolean;
      }>
    >(`${API_BASE}/data/routes/suggest`, { query, limit }),
  );
}

export async function previewDataBlockV2(body: {
  block: Record<string, unknown>;
  nativeConfig: Record<string, unknown>;
  playlistId?: string;
  /** Bypass TTL cache no servidor (Atualizar visual). */
  forceRefresh?: boolean;
  targetStepName?: string;
  previewOptions?: {
    maxRows?: number;
    includeColumnProfile?: boolean;
  };
  signal?: AbortSignal;
}) {
  const { signal, playlistId, ...rest } = body;
  const previewPlaylistId = resolvePreviewPlaylistId(playlistId);
  const payload = {
    ...rest,
    ...(previewPlaylistId ? { playlistId: previewPlaylistId } : {}),
  };
  return unwrap(
    httpPost<ApiEnvelope<{
      block: Record<string, unknown>;
      query?: Record<string, unknown>;
      preview?: Record<string, unknown>;
    }>>(
      `${API_BASE}/data/preview-block`,
      payload,
      { signal },
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

export async function exportSlidePresetMdd(presetKey: string): Promise<Blob> {
  return httpGetBlob(`${API_BASE}/slide-presets/${encodeURIComponent(presetKey)}/export`);
}

export async function exportSlideAsTemplateMdd(body: {
  key: string;
  label: string;
  description?: string;
  title?: string;
  durationSec?: number;
  nativeScreenKey?: string;
  nativeConfig: Record<string, unknown>;
}): Promise<Blob> {
  return httpPostBlob(`${API_BASE}/slide-templates/export`, body);
}

export async function importSlideTemplateMdd(file: File): Promise<SlidePresetDetail & { key: string; label: string }> {
  const form = new FormData();
  form.append("file", file);
  return unwrap(
    httpPostForm<ApiEnvelope<SlidePresetDetail & { key: string; label: string }>>(
      `${API_BASE}/slide-templates/import`,
      form,
    ),
  );
}

export async function listPublishedSlideTemplates() {
  const data = await unwrap(
    httpGet<ApiEnvelope<{ items: SlideTemplate[] }>>(
      `${API_BASE}/slide-templates?status=published`,
    ),
  );
  return data.items;
}

export async function listLibrarySlideTemplates(params?: {
  status?: SlideTemplateStatus | "";
  q?: string;
  isSystem?: boolean;
}) {
  const search = new URLSearchParams();
  if (params?.status) search.set("status", params.status);
  if (params?.q?.trim()) search.set("q", params.q.trim());
  if (typeof params?.isSystem === "boolean") search.set("isSystem", String(params.isSystem));
  const qs = search.toString();
  const data = await unwrap(
    httpGet<ApiEnvelope<{ items: SlideTemplate[] }>>(
      `${API_BASE}/slide-templates${qs ? `?${qs}` : ""}`,
    ),
  );
  return data.items;
}

export async function getSlideTemplate(id: string) {
  return unwrap(httpGet<ApiEnvelope<SlideTemplate>>(`${API_BASE}/slide-templates/${id}`));
}

export async function createSlideTemplate(body: {
  label: string;
  description?: string;
  nativeConfig: Record<string, unknown>;
  nativeScreenKey?: string;
  durationSec?: number;
  key?: string;
  publishNow?: boolean;
}) {
  return unwrap(
    httpPost<ApiEnvelope<SlideTemplate>>(`${API_BASE}/slide-templates`, body),
  );
}

export async function createSlideTemplateFromSlide(body: {
  label: string;
  description?: string;
  nativeConfig: Record<string, unknown>;
  nativeScreenKey?: string;
  durationSec?: number;
}) {
  return unwrap(
    httpPost<ApiEnvelope<SlideTemplate>>(`${API_BASE}/slide-templates/from-slide`, body),
  );
}

export async function updateSlideTemplate(
  id: string,
  body: {
    version: number;
    label?: string;
    description?: string;
    nativeConfig?: Record<string, unknown>;
    nativeScreenKey?: string;
    durationSec?: number;
  },
) {
  return unwrap(
    httpPatch<ApiEnvelope<SlideTemplate>>(`${API_BASE}/slide-templates/${id}`, body),
  );
}

export async function deleteSlideTemplate(id: string) {
  return unwrap(httpDelete<ApiEnvelope<SlideTemplate>>(`${API_BASE}/slide-templates/${id}`));
}

export async function publishSlideTemplate(id: string) {
  return unwrap(
    httpPost<ApiEnvelope<SlideTemplate>>(`${API_BASE}/slide-templates/${id}/publish`, {}),
  );
}

export async function unpublishSlideTemplate(id: string) {
  return unwrap(
    httpPost<ApiEnvelope<SlideTemplate>>(`${API_BASE}/slide-templates/${id}/unpublish`, {}),
  );
}

export async function archiveSlideTemplate(id: string) {
  return unwrap(
    httpPost<ApiEnvelope<SlideTemplate>>(`${API_BASE}/slide-templates/${id}/archive`, {}),
  );
}

export async function cloneSlideTemplate(id: string) {
  return unwrap(
    httpPost<ApiEnvelope<SlideTemplate>>(`${API_BASE}/slide-templates/${id}/clone`, {}),
  );
}

export async function exportLibrarySlideTemplateMdd(id: string): Promise<Blob> {
  return httpGetBlob(`${API_BASE}/slide-templates/${encodeURIComponent(id)}/export`);
}

export async function previewImportSlideTemplateMdd(
  file: File,
): Promise<SlidePresetDetail & { key: string; label: string; description?: string | null }> {
  const form = new FormData();
  form.append("file", file);
  return unwrap(
    httpPostForm<
      ApiEnvelope<SlidePresetDetail & { key: string; label: string; description?: string | null }>
    >(`${API_BASE}/slide-templates/import/preview`, form),
  );
}

export async function applyImportSlideTemplateMdd(file: File, publishNow = false) {
  const form = new FormData();
  form.append("file", file);
  const qs = publishNow ? "?publishNow=true" : "";
  return unwrap(
    httpPostForm<ApiEnvelope<SlideTemplate>>(
      `${API_BASE}/slide-templates/import/apply${qs}`,
      form,
    ),
  );
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
    sectionId?: string | null;
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
    durationSec: number | null;
    nativeConfig: Record<string, unknown>;
    externalUrl: string;
    isActive: boolean;
    transitionStyle: string | null;
    sectionId: string | null;
  }>,
  options?: { keepalive?: boolean },
) {
  return unwrap(
    httpPatch<ApiEnvelope<Slide>>(
      `${API_BASE}/playlists/${playlistId}/slides/${slideId}`,
      body,
      { keepalive: options?.keepalive },
    ),
  );
}

export async function listPlaylistSections(playlistId: string) {
  const data = await unwrap(
    httpGet<ApiEnvelope<{ items: PlaylistSection[] }>>(
      `${API_BASE}/playlists/${playlistId}/sections`,
    ),
  );
  return data.items;
}

/** Garante a seção Principal (isMain); idempotente. */
export async function ensurePlaylistMainSection(playlistId: string) {
  return unwrap(
    httpPost<ApiEnvelope<PlaylistSection>>(
      `${API_BASE}/playlists/${playlistId}/sections/ensure-main`,
      {},
    ),
  );
}

export async function createPlaylistSection(
  playlistId: string,
  body: {
    name: string;
    sortOrder?: number;
    isCollapsed?: boolean;
    isActive?: boolean;
    isMain?: boolean;
    defaultDurationSec?: number | null;
    transitionStyle?: string | null;
    masterConfig?: PlaylistMasterConfig;
  },
) {
  return unwrap(
    httpPost<ApiEnvelope<PlaylistSection>>(
      `${API_BASE}/playlists/${playlistId}/sections`,
      body,
    ),
  );
}

export async function updatePlaylistSection(
  playlistId: string,
  sectionId: string,
  body: Partial<{
    name: string;
    sortOrder: number;
    isCollapsed: boolean;
    isActive: boolean;
    defaultDurationSec: number | null;
    transitionStyle: string | null;
    masterConfig: PlaylistMasterConfig;
  }>,
) {
  return unwrap(
    httpPatch<ApiEnvelope<PlaylistSection>>(
      `${API_BASE}/playlists/${playlistId}/sections/${sectionId}`,
      body,
    ),
  );
}

export async function deletePlaylistSection(
  playlistId: string,
  sectionId: string,
  options?: { deleteSlides?: boolean },
) {
  const qs = options?.deleteSlides ? "?deleteSlides=true" : "";
  return unwrap(
    httpDelete<ApiEnvelope<{ deleted: boolean }>>(
      `${API_BASE}/playlists/${playlistId}/sections/${sectionId}${qs}`,
    ),
  );
}

export async function reorderPlaylistSections(
  playlistId: string,
  items: Array<{ id: string; sortOrder: number }>,
) {
  return unwrap(
    httpPost<ApiEnvelope<{ items: PlaylistSection[] }>>(
      `${API_BASE}/playlists/${playlistId}/sections/reorder`,
      { items },
    ),
  );
}

export function qrDownloadUrl(playlistId: string) {
  return `${API_BASE}/playlists/${playlistId}/qr`;
}

export async function downloadQrPng(playlistId: string) {
  return httpGetBlob(qrDownloadUrl(playlistId));
}
