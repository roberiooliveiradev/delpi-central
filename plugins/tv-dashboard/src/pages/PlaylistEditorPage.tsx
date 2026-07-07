import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  buildAdminPresentationWsUrl,
  parseComunicadoConfig,
  serializeComunicadoConfig,
  usePresentationRealtime,
} from "@delpi/tv-dashboard-presentation";

import {
  ArrowLeft,
  Copy,
  Eye,
  Link2,
  QrCode,
  RefreshCw,
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
import { ComunicadoComposerCanvas } from "../components/ComunicadoComposer";
import { ComunicadoEditorProvider, useComunicadoEditor } from "../components/comunicadoEditorContext";
import { ComunicadoEditorRibbon } from "../components/ComunicadoEditorRibbon";
import {
  DeckElementSidePanel,
} from "../components/deck";
import { DeckEditorChrome } from "../components/DeckEditorChrome";
import { DeckWorkspace } from "../components/DeckWorkspace";
import { SlideStagePreview } from "../components/SlideStagePreview";

type DeckSettingsProps = {
  onSaveSlide: (
    slide: Slide,
    payload: {
      title: string;
      durationSec: number;
      nativeConfig?: Record<string, unknown>;
      externalUrl?: string;
    },
  ) => void;
};

type Props = {
  playlistId: string;
  onBack: () => void;
  onPreview: () => void;
  onShare: () => void;
};

export function PlaylistEditorPage({ playlistId, onBack, onPreview, onShare }: Props) {
  const [playlist, setPlaylist] = useState<Playlist | null>(null);
  const [catalog, setCatalog] = useState<NativeScreenCatalogItem[]>([]);
  const [presets, setPresets] = useState<SlidePreset[]>([]);
  const [uiContent, setUiContent] = useState<TvDashboardUiContent | null>(null);
  const [branchScope, setBranchScope] = useState<BranchScope | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [selectedSlideId, setSelectedSlideId] = useState<string | null>(null);
  const [tvStatus, setTvStatus] = useState<PresentationStatus | null>(null);
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const [previewBySlideId, setPreviewBySlideId] = useState<
    Record<string, PresentationPayload["slides"][number]>
  >({});
  const saveComunicadoTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const slides = useMemo(
    () => [...(playlist?.slides ?? [])].sort((a, b) => a.sortOrder - b.sortOrder),
    [playlist?.slides],
  );

  const selectedSlide = useMemo(
    () => slides.find((slide) => slide.id === selectedSlideId) ?? slides[0] ?? null,
    [slides, selectedSlideId],
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

  const reloadPlaylistFromServer = useCallback(async () => {
    try {
      const pl = await getPlaylist(playlistId);
      setPlaylist((current) => (current ? { ...pl, slides: pl.slides ?? current.slides } : pl));
      await refreshPreviewThumbnails();
    } catch {
      // mantém estado local se a sincronização falhar
    }
  }, [playlistId, refreshPreviewThumbnails]);

  useEffect(() => {
    void refreshPreviewThumbnails();
  }, [refreshPreviewThumbnails, slidesPreviewKey]);

  useEffect(() => {
    if (!slides.length) {
      setSelectedSlideId(null);
      return;
    }
    if (!selectedSlideId || !slides.some((slide) => slide.id === selectedSlideId)) {
      setSelectedSlideId(slides[0].id);
    }
  }, [slides, selectedSlideId]);

  usePresentationRealtime({
    enabled: Boolean(playlistId && slides.length > 0 && thumbnailWsUrl),
    wsUrl: thumbnailWsUrl,
    onPresentationUpdated: () => {
      void reloadPlaylistFromServer();
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

  useEffect(() => {
    return () => {
      if (saveComunicadoTimerRef.current) window.clearTimeout(saveComunicadoTimerRef.current);
    };
  }, []);

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
    setSelectedSlideId(slide.id);
  }

  async function handleImportPreset(payload: { presetKey: string; branch?: string }) {
    if (!playlist) return;
    const slide = await addSlideFromPreset(playlist.id, payload);
    setPlaylist({ ...playlist, slides: [...(playlist.slides ?? []), slide] });
    setSelectedSlideId(slide.id);
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
    setSelectedSlideId(slide.id);
  }

  async function handleRemoveSlide(slide: Slide) {
    if (!playlist) return;
    if (!window.confirm(`Remover a tela «${slide.title}»?`)) return;
    await deleteSlide(playlist.id, slide.id);
    const remaining = (playlist.slides ?? []).filter((item) => item.id !== slide.id);
    setPlaylist({ ...playlist, slides: remaining });
    if (selectedSlideId === slide.id) {
      setSelectedSlideId(remaining[0]?.id ?? null);
    }
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

  function scheduleCustomSlideSave(slide: Slide, nativeConfig: Record<string, unknown>) {
    if (saveComunicadoTimerRef.current) window.clearTimeout(saveComunicadoTimerRef.current);
    saveComunicadoTimerRef.current = window.setTimeout(() => {
      void handleSaveSlide(slide, {
        title: slide.title,
        durationSec: slide.durationSec ?? playlist?.defaultDurationSec ?? 30,
        nativeConfig,
      });
    }, 700);
  }

  async function handleDuplicateSlide(slide: Slide) {
    if (!playlist) return;
    const copy = await duplicateSlide(playlist.id, slide.id);
    setPlaylist({ ...playlist, slides: [...(playlist.slides ?? []), copy] });
    setSelectedSlideId(copy.id);
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
    void downloadQrPng(playlistId)
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        window.open(url, "_blank", "noopener,noreferrer");
        window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
      })
      .catch((err) => {
        window.alert(err instanceof Error ? err.message : "Erro ao gerar QR.");
      });
  }

  if (loading) return <div className="td-state">Carregando programação…</div>;
  if (error || !playlist) return <div className="td-state">{error ?? "Programação não encontrada."}</div>;

  const admin = uiContent?.admin ?? {};
  const isCustomSlide = selectedSlide?.nativeScreenKey === "custom_message";

  const slideDeckProps = {
    slides,
    selectedSlide,
    onAdd: () => setAddModalOpen(true),
    onSelect: setSelectedSlideId,
    onDuplicate: (slide: Slide) => void handleDuplicateSlide(slide),
    onToggleActive: (slide: Slide) => void handleToggleSlideActive(slide),
    onRemove: (slide: Slide) => void handleRemoveSlide(slide),
  };

  const chromeProps = {
    playlist,
    slide: selectedSlide,
    catalog,
    branchScope,
    isCustomSlide,
    adminLabels: admin,
    slideDeck: slideDeckProps,
    onSavePlaylistSettings: (field: string, value: string | number) => void saveSettings(field, value),
    onSaveSlide: (slide: Slide, payload: Parameters<DeckSettingsProps["onSaveSlide"]>[1]) =>
      void handleSaveSlide(slide, payload),
  };

  const workspaceProps = {
    slides,
    playlistId,
    selectedSlideId: selectedSlide?.id ?? null,
    previewBySlideId,
    dragIndex,
    inactiveLabel: admin.slideInactive ?? "Pausada",
    onSelect: setSelectedSlideId,
    onDragStart: setDragIndex,
    onDrop: (index: number) => void handleDropSlide(index),
    onDragEnd: () => setDragIndex(null),
  };

  return (
    <div className="td-deck">
      <div className="td-toolbar td-deck__toolbar">
        <button type="button" className="td-btn" onClick={onBack}>
          <ArrowLeft size={16} />
          Voltar
        </button>
        <div className="td-deck__toolbar-actions">
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

      <header className="td-deck__header">
        <div>
          <h2 className="td-deck__title">
            {playlist.name}
            {tvStatusLabel() ? <span className={tvStatusClass()}>{tvStatusLabel()}</span> : null}
          </h2>
          <p className="td-subtitle td-deck__meta">
            {playlist.viewCount ?? 0} visualizações
            {playlist.lastPresentedAt
              ? ` · última exibição ${new Date(playlist.lastPresentedAt).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" })}`
              : ""}
            {playlist.isActive ? "" : " · link inativo"}
            {selectedSlide ? ` · tela ${slides.findIndex((item) => item.id === selectedSlide.id) + 1} de ${slides.length}` : ""}
          </p>
        </div>
      </header>

      {isCustomSlide && selectedSlide ? (
        <ComunicadoEditorProvider
          playlistId={playlistId}
          value={serializeComunicadoConfig(parseComunicadoConfig(selectedSlide.nativeConfig ?? {}))}
          onChange={(config) => scheduleCustomSlideSave(selectedSlide, config)}
        >
          <DeckEditorChrome {...chromeProps} />
          <DeckWorkspace
            {...workspaceProps}
            selectedSlideId={selectedSlide.id}
            rightPanel={<DeckElementSidePanel labels={admin} />}
            stage={
              <div className="td-deck-stage__editor">
                <ComunicadoComposerCanvas />
              </div>
            }
          />
        </ComunicadoEditorProvider>
      ) : (
        <>
          <DeckEditorChrome {...chromeProps} />
          <DeckWorkspace
            {...workspaceProps}
            stage={
              !selectedSlide ? (
                <div className="td-deck-stage__empty">
                  <p className="td-subtitle">Adicione uma tela ou selecione um slide na coluna à esquerda.</p>
                </div>
              ) : (
                <div className="td-deck-stage__canvas" data-viewport={playlist.viewportProfile}>
                  <SlideStagePreview
                    slide={selectedSlide}
                    playlistId={playlistId}
                    previewSlide={previewBySlideId[selectedSlide.id]}
                  />
                </div>
              )
            }
          />
        </>
      )}

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
    </div>
  );
}
