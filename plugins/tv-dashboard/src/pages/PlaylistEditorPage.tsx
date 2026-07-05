import { useCallback, useEffect, useMemo, useState } from "react";
import {
  buildAdminPresentationWsUrl,
  usePresentationRealtime,
} from "@delpi/tv-dashboard-presentation";
import {
  ArrowDown,
  ArrowLeft,
  ArrowUp,
  Copy,
  Eye,
  EyeOff,
  Link2,
  Plus,
  QrCode,
  RefreshCw,
  Pencil,
  Trash2,
} from "lucide-react";

import {
  activatePlaylist,
  addSlide,
  addSlideFromPreset,
  deactivatePlaylist,
  deletePlaylist,
  deleteSlide,
  duplicateSlide,
  downloadQrPng,
  getBranchScope,
  getPlaylist,
  getPreviewPayload,
  getPresentationStatus,
  getUiContent,
  listNativeScreens,
  listSlidePresets,
  regeneratePlaylistToken,
  reorderSlides,
  updatePlaylist,
  updateSlide,
  type BranchScope,
  type NativeScreenCatalogItem,
  type Playlist,
  type PresentationPayload,
  type PresentationStatus,
  type Slide,
  type SlidePreset,
  type TvDashboardUiContent,
} from "../api/tvDashboardApi";
import { getAccessToken } from "../api/httpClient";
import { AddSlideModal } from "../components/AddSlideModal";
import { EditSlideModal } from "../components/EditSlideModal";
import { SlideCardThumbnail } from "../components/SlideCardThumbnail";

type Props = {
  playlistId: string;
  onBack: () => void;
  onPreview: () => void;
  onShare: () => void;
};

const VIEWPORT_OPTIONS = [
  { value: "1080p", label: "1920×1080 (Full HD)" },
  { value: "1080p_portrait", label: "1080×1920 (Retrato)" },
  { value: "4k", label: "3840×2160 (4K)" },
  { value: "720p", label: "1280×720 (HD)" },
];

const TRANSITION_OPTIONS = [
  { value: "fade", label: "Fade" },
  { value: "slide", label: "Deslizar" },
  { value: "none", label: "Sem transição" },
];

export function PlaylistEditorPage({ playlistId, onBack, onPreview, onShare }: Props) {
  const [playlist, setPlaylist] = useState<Playlist | null>(null);
  const [catalog, setCatalog] = useState<NativeScreenCatalogItem[]>([]);
  const [presets, setPresets] = useState<SlidePreset[]>([]);
  const [uiContent, setUiContent] = useState<TvDashboardUiContent | null>(null);
  const [branchScope, setBranchScope] = useState<BranchScope | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [editSlide, setEditSlide] = useState<Slide | null>(null);
  const [tvStatus, setTvStatus] = useState<PresentationStatus | null>(null);
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const [previewBySlideId, setPreviewBySlideId] = useState<
    Record<string, PresentationPayload["slides"][number]>
  >({});

  const slides = useMemo(
    () => [...(playlist?.slides ?? [])].sort((a, b) => a.sortOrder - b.sortOrder),
    [playlist?.slides],
  );

  const slidesPreviewKey = useMemo(
    () =>
      slides
        .map(
          (slide) =>
            `${slide.id}:${slide.title}:${slide.slideType}:${slide.nativeScreenKey ?? ""}:${slide.externalUrl ?? ""}:${JSON.stringify(slide.nativeConfig ?? {})}:${slide.isActive}`,
        )
        .join("|"),
    [slides],
  );

  const thumbnailWsUrl = useMemo(() => {
    const token = getAccessToken();
    if (!token) return null;
    return buildAdminPresentationWsUrl(playlistId, token);
  }, [playlistId]);

  const refreshPreviewThumbnails = useCallback(async () => {
    if (!slides.length) {
      setPreviewBySlideId({});
      return;
    }
    try {
      const payload = await getPreviewPayload(playlistId);
      const next: Record<string, PresentationPayload["slides"][number]> = {};
      for (const slide of payload.slides) next[slide.id] = slide;
      setPreviewBySlideId(next);
    } catch {
      setPreviewBySlideId({});
    }
  }, [playlistId, slides.length]);

  useEffect(() => {
    void refreshPreviewThumbnails();
  }, [refreshPreviewThumbnails, slidesPreviewKey]);

  usePresentationRealtime({
    enabled: Boolean(playlistId && slides.length > 0 && thumbnailWsUrl),
    wsUrl: thumbnailWsUrl,
    onPresentationUpdated: () => {
      void refreshPreviewThumbnails();
    },
  });

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [pl, screens, presetItems, ui, scope] = await Promise.all([
        getPlaylist(playlistId),
        listNativeScreens(),
        listSlidePresets(),
        getUiContent(),
        getBranchScope(),
      ]);
      setPlaylist(pl);
      setCatalog(screens);
      setPresets(presetItems);
      setUiContent(ui);
      setBranchScope(scope);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar programação.");
    } finally {
      setLoading(false);
    }
  }, [playlistId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    let cancelled = false;
    async function pollStatus() {
      try {
        const status = await getPresentationStatus(playlistId);
        if (!cancelled) setTvStatus(status);
      } catch {
        if (!cancelled) setTvStatus(null);
      }
    }
    void pollStatus();
    const timer = window.setInterval(() => void pollStatus(), 30_000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [playlistId]);

  async function saveSettings(field: string, value: string | number) {
    if (!playlist) return;
    const updated = await updatePlaylist(playlist.id, { [field]: value });
    setPlaylist({ ...updated, slides: playlist.slides });
  }

  async function handleAddNative(payload: {
    screenKey: string;
    title: string;
    nativeConfig: Record<string, unknown>;
    durationSec: number;
  }) {
    if (!playlist) return;
    const slide = await addSlide(playlist.id, {
      slideType: "native",
      title: payload.title,
      nativeScreenKey: payload.screenKey,
      nativeConfig: payload.nativeConfig,
      durationSec: payload.durationSec,
    });
    setPlaylist({ ...playlist, slides: [...(playlist.slides ?? []), slide] });
  }

  async function handleImportPreset(payload: { presetKey: string; branch?: string }) {
    if (!playlist) return;
    const slide = await addSlideFromPreset(playlist.id, payload);
    setPlaylist({ ...playlist, slides: [...(playlist.slides ?? []), slide] });
  }

  async function handleAddExternal(payload: {
    title: string;
    externalUrl: string;
    durationSec: number;
  }) {
    if (!playlist) return;
    const slide = await addSlide(playlist.id, {
      slideType: "external",
      title: payload.title,
      externalUrl: payload.externalUrl,
      durationSec: payload.durationSec,
    });
    setPlaylist({ ...playlist, slides: [...(playlist.slides ?? []), slide] });
  }

  async function handleRemoveSlide(slide: Slide) {
    if (!playlist) return;
    if (!window.confirm(`Remover a tela «${slide.title}»?`)) return;
    await deleteSlide(playlist.id, slide.id);
    setPlaylist({
      ...playlist,
      slides: (playlist.slides ?? []).filter((item) => item.id !== slide.id),
    });
  }

  async function moveSlide(slide: Slide, direction: -1 | 1) {
    if (!playlist) return;
    const slides = [...(playlist.slides ?? [])].sort((a, b) => a.sortOrder - b.sortOrder);
    const index = slides.findIndex((item) => item.id === slide.id);
    const target = index + direction;
    if (index < 0 || target < 0 || target >= slides.length) return;
    const reordered = [...slides];
    [reordered[index], reordered[target]] = [reordered[target], reordered[index]];
    const items = reordered.map((item, sortOrder) => ({ id: item.id, sortOrder }));
    const result = await reorderSlides(playlist.id, items);
    setPlaylist({ ...playlist, slides: result.slides });
  }

  async function handleToggleActive() {
    if (!playlist) return;
    const updated = playlist.isActive
      ? await deactivatePlaylist(playlist.id)
      : await activatePlaylist(playlist.id);
    setPlaylist({ ...updated, slides: playlist.slides });
  }

  async function handleDelete() {
    if (!playlist) return;
    if (!window.confirm("Excluir esta programação permanentemente?")) return;
    await deletePlaylist(playlist.id);
    onBack();
  }

  async function handleRegenerateToken() {
    if (!playlist) return;
    if (
      !window.confirm(
        "Gerar novo link? TVs com o link atual deixarão de funcionar até usar o novo endereço.",
      )
    ) {
      return;
    }
    const updated = await regeneratePlaylistToken(playlist.id);
    setPlaylist({ ...updated, slides: playlist.slides });
    window.alert("Novo link gerado.");
  }

  async function handleSaveSlide(
    slide: Slide,
    payload: {
      title: string;
      durationSec: number;
      nativeConfig?: Record<string, unknown>;
      externalUrl?: string;
    },
  ) {
    if (!playlist) return;
    const updated = await updateSlide(playlist.id, slide.id, payload);
    setPlaylist({
      ...playlist,
      slides: (playlist.slides ?? []).map((item) => (item.id === slide.id ? updated : item)),
    });
  }

  async function handleDuplicateSlide(slide: Slide) {
    if (!playlist) return;
    const copy = await duplicateSlide(playlist.id, slide.id);
    setPlaylist({ ...playlist, slides: [...(playlist.slides ?? []), copy] });
  }

  async function handleToggleSlideActive(slide: Slide) {
    if (!playlist) return;
    const updated = await updateSlide(playlist.id, slide.id, { isActive: !slide.isActive });
    setPlaylist({
      ...playlist,
      slides: (playlist.slides ?? []).map((item) => (item.id === slide.id ? updated : item)),
    });
  }

  function tvStatusLabel() {
    const admin = uiContent?.admin;
    if (!tvStatus) return null;
    if (tvStatus.status === "online") return admin?.tvStatusOnline ?? "TV online";
    if (tvStatus.status === "offline") return admin?.tvStatusOffline ?? "TV offline";
    return admin?.tvStatusNever ?? "Nunca exibida";
  }

  function tvStatusClass() {
    if (!tvStatus) return "td-badge";
    if (tvStatus.status === "online") return "td-badge td-badge--online";
    if (tvStatus.status === "offline") return "td-badge td-badge--offline";
    return "td-badge td-badge--inactive";
  }

  async function handleDropSlide(targetIndex: number) {
    if (!playlist || dragIndex === null || dragIndex === targetIndex) return;
    const reordered = [...slides];
    const [moved] = reordered.splice(dragIndex, 1);
    reordered.splice(targetIndex, 0, moved);
    const items = reordered.map((item, sortOrder) => ({ id: item.id, sortOrder }));
    const result = await reorderSlides(playlist.id, items);
    setPlaylist({ ...playlist, slides: result.slides });
    setDragIndex(null);
  }

  function copyLink() {
    if (!playlist?.publicUrl) return;
    void navigator.clipboard.writeText(playlist.publicUrl);
    window.alert("Link copiado.");
  }

  function openQr() {
    void downloadQrPng(playlistId).then((blob) => {
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank", "noopener,noreferrer");
      window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
    }).catch((err) => {
      window.alert(err instanceof Error ? err.message : "Erro ao gerar QR.");
    });
  }

  if (loading) return <div className="td-state">Carregando programação…</div>;
  if (error || !playlist) return <div className="td-state">{error ?? "Programação não encontrada."}</div>;

  return (
    <>
      <div className="td-toolbar">
        <button type="button" className="td-btn" onClick={onBack}>
          <ArrowLeft size={16} />
          Voltar
        </button>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button type="button" className="td-btn" onClick={onPreview}>
            <Eye size={16} />
            Pré-visualizar
          </button>
          <button type="button" className="td-btn" onClick={onShare}>
            <Link2 size={16} />
            Compartilhar
          </button>
          <button type="button" className="td-btn" onClick={copyLink}>
            <Copy size={16} />
            Copiar link
          </button>
          <button type="button" className="td-btn" onClick={openQr}>
            <QrCode size={16} />
            QR code
          </button>
          <button type="button" className="td-btn" onClick={() => void handleRegenerateToken()}>
            <RefreshCw size={16} />
            Novo link
          </button>
          <button type="button" className="td-btn" onClick={() => void handleToggleActive()}>
            <Link2 size={16} />
            {playlist.isActive ? "Desativar link" : "Reativar link"}
          </button>
          <button type="button" className="td-btn td-btn--danger" onClick={() => void handleDelete()}>
            <Trash2 size={16} />
            Excluir
          </button>
        </div>
      </div>

      <div className="td-grid-2">
        <div className="td-card">
          <h2 style={{ marginTop: 0, display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
            {playlist.name}
            {tvStatusLabel() ? (
              <span className={tvStatusClass()}>{tvStatusLabel()}</span>
            ) : null}
          </h2>
          <p className="td-subtitle" style={{ marginTop: 0 }}>
            {playlist.viewCount ?? 0} visualizações
            {playlist.lastPresentedAt
              ? ` · última exibição ${new Date(playlist.lastPresentedAt).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" })}`
              : ""}
            {playlist.isActive ? "" : " · link inativo"}
          </p>
          <div className="td-field">
            <label htmlFor="td-viewport">Resolução alvo</label>
            <select
              id="td-viewport"
              value={playlist.viewportProfile}
              onChange={(e) => void saveSettings("viewportProfile", e.target.value)}
            >
              {VIEWPORT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <div className="td-field">
            <label htmlFor="td-transition">Transição</label>
            <select
              id="td-transition"
              value={playlist.transitionStyle}
              onChange={(e) => void saveSettings("transitionStyle", e.target.value)}
            >
              {TRANSITION_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <div className="td-field">
            <label htmlFor="td-duration">Duração padrão (s)</label>
            <input
              id="td-duration"
              type="number"
              min={5}
              max={600}
              value={playlist.defaultDurationSec}
              onChange={(e) => void saveSettings("defaultDurationSec", Number(e.target.value))}
            />
          </div>
          <div className="td-field">
            <label htmlFor="td-refresh">Atualizar dados a cada (s)</label>
            <input
              id="td-refresh"
              type="number"
              min={30}
              max={3600}
              value={playlist.globalRefreshSec}
              onChange={(e) => void saveSettings("globalRefreshSec", Number(e.target.value))}
            />
          </div>
          <div className="td-link-box">
            <input readOnly value={playlist.publicUrl ?? ""} aria-label="Link público" />
          </div>
        </div>

        <div className="td-card">
          <div className="td-toolbar" style={{ marginBottom: 0 }}>
            <h3 style={{ margin: 0 }}>Telas ({slides.length})</h3>
            <button type="button" className="td-btn td-btn--primary" onClick={() => setAddModalOpen(true)}>
              <Plus size={16} />
              Adicionar tela
            </button>
          </div>
          <div className="td-slide-list">
            {slides.length === 0 ? (
              <p className="td-subtitle">Adicione telas nativas DELPI ou links externos (Power BI, sites).</p>
            ) : (
              slides.map((slide, idx) => (
                <div
                  key={slide.id}
                  className={`td-slide-item${slide.isActive ? "" : " td-slide-item--inactive"}${dragIndex === idx ? " td-slide-item--dragging" : ""}`}
                  draggable
                  onDragStart={() => setDragIndex(idx)}
                  onDragOver={(event) => event.preventDefault()}
                  onDrop={() => void handleDropSlide(idx)}
                  onDragEnd={() => setDragIndex(null)}
                >
                  <strong>{idx + 1}</strong>
                  <SlideCardThumbnail
                    slide={slide}
                    playlistId={playlistId}
                    previewSlide={previewBySlideId[slide.id]}
                  />
                  <div>
                    <div>{slide.title}</div>
                    <div className="td-slide-meta">
                      {!slide.isActive ? `${uiContent?.admin?.slideInactive ?? "Tela pausada"} · ` : ""}
                      {slide.slideType === "native"
                        ? `Nativa · ${slide.nativeScreenKey}`
                        : `Externa · ${slide.externalUrl}`}
                      {" · "}
                      {slide.durationSec ?? playlist.defaultDurationSec}s
                    </div>
                  </div>
                  <div className="td-slide-actions">
                    <button type="button" className="td-btn td-btn--icon" disabled={idx === 0} onClick={() => void moveSlide(slide, -1)} aria-label="Mover para cima">
                      <ArrowUp size={14} />
                    </button>
                    <button type="button" className="td-btn td-btn--icon" disabled={idx === slides.length - 1} onClick={() => void moveSlide(slide, 1)} aria-label="Mover para baixo">
                      <ArrowDown size={14} />
                    </button>
                    <button type="button" className="td-btn td-btn--icon" onClick={() => void handleToggleSlideActive(slide)} aria-label={slide.isActive ? "Pausar tela" : "Reativar tela"}>
                      {slide.isActive ? <Eye size={14} /> : <EyeOff size={14} />}
                    </button>
                    <button type="button" className="td-btn td-btn--icon" onClick={() => setEditSlide(slide)} aria-label="Editar tela">
                      <Pencil size={14} />
                    </button>
                    <button type="button" className="td-btn td-btn--icon" onClick={() => void handleDuplicateSlide(slide)} aria-label="Duplicar tela">
                      <Copy size={14} />
                    </button>
                    <button type="button" className="td-btn td-btn--danger td-btn--icon" onClick={() => void handleRemoveSlide(slide)} aria-label="Remover">
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <AddSlideModal
        open={addModalOpen}
        playlistId={playlistId}
        catalog={catalog}
        presets={presets}
        branchScope={branchScope}
        ui={uiContent}
        onClose={() => setAddModalOpen(false)}
        onAddNative={(payload) => void handleAddNative(payload)}
        onAddExternal={(payload) => void handleAddExternal(payload)}
        onImportPreset={(payload) => void handleImportPreset(payload)}
      />

      <EditSlideModal
        open={editSlide !== null}
        playlistId={playlistId}
        slide={editSlide}
        catalog={catalog}
        branchScope={branchScope}
        defaultDurationSec={playlist.defaultDurationSec}
        onClose={() => setEditSlide(null)}
        onSave={(payload) => {
          if (editSlide) void handleSaveSlide(editSlide, payload);
        }}
      />

    </>
  );
}
