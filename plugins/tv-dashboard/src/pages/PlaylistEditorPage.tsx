import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  buildAdminPresentationWsUrl,
  parseComunicadoConfig,
  serializeComunicadoConfig,
  usePresentationRealtime,
} from "@delpi/tv-dashboard-presentation";

import {
  activatePlaylist,
  addSlide,
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
  type TvDashboardUiContent,
} from "../api/tvDashboardApi";
import { getAccessToken } from "../api/httpClient";
import { ComunicadoEditorProvider } from "../components/comunicadoEditorContext";
import { CustomSlideEditorLayout } from "../components/CustomSlideEditorLayout";
import { DeckEditorHeaderActions } from "../components/deck";
import { DeckEditorChrome } from "../components/DeckEditorChrome";
import { DeckWorkspace } from "../components/DeckWorkspace";
import { SlideStagePreview } from "../components/SlideStagePreview";
import {
  DeckEditorHistoryProvider,
  type DeckEditorHistoryContextValue,
} from "../context/deckEditorHistoryContext";
import { useConfirm } from "../context/ConfirmDialogProvider";
import { useDeckEditorHistory } from "../hooks/useDeckEditorHistory";
import { useDeckEditorKeyboard } from "../hooks/useDeckEditorKeyboard";
import type { DeckEditorSnapshot } from "../utils/deckEditorHistory";

type DeckSettingsProps = {
  onSaveSlide: (
    slide: Slide,
    payload: {
      title: string;
      durationSec: number;
      nativeConfig?: Record<string, unknown>;
      externalUrl?: string;
      transitionStyle?: string | null;
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
  const confirm = useConfirm();
  const [playlist, setPlaylist] = useState<Playlist | null>(null);
  const [catalog, setCatalog] = useState<NativeScreenCatalogItem[]>([]);
  const [uiContent, setUiContent] = useState<TvDashboardUiContent | null>(null);
  const [branchScope, setBranchScope] = useState<BranchScope | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSlideId, setSelectedSlideId] = useState<string | null>(null);
  const [tvStatus, setTvStatus] = useState<PresentationStatus | null>(null);
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const [previewBySlideId, setPreviewBySlideId] = useState<
    Record<string, PresentationPayload["slides"][number]>
  >({});
  const saveComunicadoTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const playlistRef = useRef<Playlist | null>(null);
  const selectedSlideIdRef = useRef<string | null>(null);
  const liveComunicadoConfigRef = useRef<Record<string, unknown> | null>(null);

  playlistRef.current = playlist;
  selectedSlideIdRef.current = selectedSlideId;

  const applyDeckSnapshot = useCallback((snapshot: DeckEditorSnapshot) => {
    setPlaylist(snapshot.playlist);
    setSelectedSlideId(snapshot.selectedSlideId);
    const slide = snapshot.selectedSlideId
      ? snapshot.playlist.slides?.find((item) => item.id === snapshot.selectedSlideId)
      : null;
    if (slide?.nativeScreenKey === "custom_message") {
      liveComunicadoConfigRef.current = slide.nativeConfig ?? {};
    }
  }, []);

  const deckHistory = useDeckEditorHistory({
    playlistId,
    getPlaylist: () => playlistRef.current,
    getSelectedSlideId: () => selectedSlideIdRef.current,
    getLiveComunicadoConfig: () => liveComunicadoConfigRef.current,
    getComunicadoSlideId: () =>
      selectedSlideIdRef.current &&
      playlistRef.current?.slides?.some(
        (slide) =>
          slide.id === selectedSlideIdRef.current && slide.nativeScreenKey === "custom_message",
      )
        ? selectedSlideIdRef.current
        : null,
    applySnapshot: applyDeckSnapshot,
  });

  const deckHistoryValue = useMemo<DeckEditorHistoryContextValue>(
    () => ({
      recordBeforeChange: deckHistory.recordBeforeChange,
      undo: deckHistory.undo,
      redo: deckHistory.redo,
      canUndo: deckHistory.canUndo,
      canRedo: deckHistory.canRedo,
      setLiveComunicadoConfig: (config) => {
        liveComunicadoConfigRef.current = config;
      },
    }),
    [
      deckHistory.canRedo,
      deckHistory.canUndo,
      deckHistory.recordBeforeChange,
      deckHistory.redo,
      deckHistory.undo,
    ],
  );

  useDeckEditorKeyboard({
    undo: deckHistory.undo,
    redo: deckHistory.redo,
    canUndo: deckHistory.canUndo,
    canRedo: deckHistory.canRedo,
  });

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
      const [pl, screens, ui, scope] = await Promise.all([
        getPlaylist(playlistId),
        listNativeScreens(),
        getUiContent(),
        getBranchScope(),
      ]);
      setPlaylist(pl);
      setCatalog(screens);
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
    deckHistory.recordBeforeChange();
    const updated = await updatePlaylist(playlist.id, { [field]: value });
    setPlaylist({ ...updated, slides: playlist.slides });
  }

  async function handleAddCustomSlide() {
    if (!playlist) return;
    deckHistory.recordBeforeChange();
    const customCatalogItem = catalog.find((item) => item.key === "custom_message");
    const customCount = (playlist.slides ?? []).filter(
      (slide) => slide.nativeScreenKey === "custom_message",
    ).length;
    const baseTitle = customCatalogItem?.label ?? "Personalizado";
    const title = customCount === 0 ? baseTitle : `${baseTitle} ${customCount + 1}`;
    const slide = await addSlide(playlist.id, {
      slideType: "native",
      title,
      nativeScreenKey: "custom_message",
      nativeConfig: serializeComunicadoConfig(
        parseComunicadoConfig({ headline: "", blocks: [] }),
      ),
      durationSec: customCatalogItem?.defaultDurationSec ?? 30,
    });
    setPlaylist({ ...playlist, slides: [...(playlist.slides ?? []), slide] });
    setSelectedSlideId(slide.id);
  }

  async function handleRemoveSlide(slide: Slide) {
    if (!playlist) return;
    const confirmed = await confirm({
      title: "Remover tela",
      message: `Remover a tela «${slide.title}»?`,
      confirmLabel: "Remover",
      variant: "danger",
    });
    if (!confirmed) return;
    deckHistory.recordBeforeChange();
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
    const confirmed = await confirm({
      title: "Excluir programação",
      message: "Excluir esta programação permanentemente?",
      confirmLabel: "Excluir",
      variant: "danger",
    });
    if (!confirmed) return;
    await deletePlaylist(playlist.id);
    onBack();
  }

  async function handleRegenerateToken() {
    if (!playlist) return;
    const confirmed = await confirm({
      title: "Gerar novo link",
      message:
        "Gerar novo link? TVs com o link atual deixarão de funcionar até usar o novo endereço.",
      confirmLabel: "Gerar novo link",
      variant: "danger",
    });
    if (!confirmed) {
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
      transitionStyle?: string | null;
    },
    options?: { recordHistory?: boolean },
  ) {
    if (!playlist) return;
    if (options?.recordHistory) deckHistory.recordBeforeChange();
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
    deckHistory.recordBeforeChange();
    const copy = await duplicateSlide(playlist.id, slide.id);
    setPlaylist({ ...playlist, slides: [...(playlist.slides ?? []), copy] });
    setSelectedSlideId(copy.id);
  }

  async function handleToggleSlideActive(slide: Slide) {
    if (!playlist) return;
    deckHistory.recordBeforeChange();
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
    deckHistory.recordBeforeChange();
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
    onAdd: () => void handleAddCustomSlide(),
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
    headerActions: (
      <DeckEditorHeaderActions
        playlistName={playlist.name}
        tvStatusLabel={tvStatusLabel()}
        tvStatusClass={tvStatusClass()}
        linkActive={playlist.isActive}
        onBack={onBack}
        onPreview={onPreview}
        onShare={onShare}
        onCopyLink={copyLink}
        onQr={openQr}
        onRegenerateToken={() => void handleRegenerateToken()}
        onToggleLink={() => void handleToggleActive()}
        onDelete={() => void handleDelete()}
      />
    ),
    onSavePlaylistSettings: (field: string, value: string | number) => void saveSettings(field, value),
    onSaveSlide: (slide: Slide, payload: Parameters<DeckSettingsProps["onSaveSlide"]>[1]) =>
      void handleSaveSlide(slide, payload, { recordHistory: true }),
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
    <DeckEditorHistoryProvider value={deckHistoryValue}>
      <div className="td-deck td-deck--editor">
      {isCustomSlide && selectedSlide ? (
        <ComunicadoEditorProvider
          playlistId={playlistId}
          slideId={selectedSlide.id}
          value={serializeComunicadoConfig(parseComunicadoConfig(selectedSlide.nativeConfig ?? {}))}
          onChange={(config) => scheduleCustomSlideSave(selectedSlide, config)}
        >
          <CustomSlideEditorLayout
            selectedSlide={selectedSlide}
            workspaceProps={workspaceProps}
            chromeProps={chromeProps}
            adminLabels={admin}
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

      </div>
    </DeckEditorHistoryProvider>
  );
}
