import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  parseComunicadoConfig,
  serializeComunicadoConfig,
  type PresentationPresencePeer,
  type PresentationSelectionUpdateEvent,
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
import { DeckEditorChrome } from "../components/DeckEditorChrome";
import { DeckWorkspace } from "../components/DeckWorkspace";
import { SlideStagePreview } from "../components/SlideStagePreview";
import { enrichComunicadoConfigForEditor } from "../components/slideCardPreview";
import {
  DeckEditorHistoryProvider,
  type DeckEditorHistoryContextValue,
} from "../context/deckEditorHistoryContext";
import { KeyboardShortcutsTipsProvider } from "../context/KeyboardShortcutsTipsProvider";
import { DeckKeyTipsProvider } from "../context/DeckKeyTipsProvider";
import { EditorShortcutsProvider } from "../keyboard";
import { KeyboardShortcutsCatalogModal } from "../components/KeyboardShortcutsCatalogModal";
import { useConfirm } from "../context/ConfirmDialogProvider";
import { useDeckEditorHistory } from "../hooks/useDeckEditorHistory";
import { useDeckEditorKeyboard } from "../hooks/useDeckEditorKeyboard";
import { usePlaylistEditorSync } from "../hooks/usePlaylistEditorSync";
import type { DeckEditorSnapshot } from "../utils/deckEditorHistory";
import {
  pasteTitleFromClipboard,
  slidePayloadForClipboard,
  type SlideClipboardPayload,
} from "../utils/slideDeckClipboard";
import { exportSlideElementToPdf, exportSlideElementToPng, resolveSlideExportTarget } from "../utils/exportSlidePng";
import { exportSlidePptx } from "../utils/exportSlidePptx";
import { readPlaylistShell, writePlaylistShell } from "../utils/editorSessionCache";
import {
  resolveSelectedSlideId,
  writeSelectedSlideId,
} from "../utils/deckSelectedSlidePreferences";
import {
  clearComunicadoSlideDraft,
  mergePlaylistSlidesWithComunicadoDrafts,
  readComunicadoSlideDraft,
  writeComunicadoSlideDraft,
} from "../utils/comunicadoSlideDraftPreferences";
import {
  bumpComunicadoAutosaveVersion,
  resolveNativeConfigAfterAutosave,
  shouldClearComunicadoDraftAfterSave,
  shouldClearComunicadoPendingAfterSave,
} from "../utils/comunicadoSlideAutosave";
import {
  getEditorPresenceClientId,
  resolveEditorDisplayName,
} from "../utils/editorPresence";
import { tvDashboardNotice } from "../utils/tvDashboardNotice";

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
  /** false quando o editor fica montado sob a prévia (atalhos não capturam teclas). */
  editorActive?: boolean;
  onBack: () => void;
  onPreview: () => void;
  onShare: () => void;
};

export function PlaylistEditorPage({
  playlistId,
  editorActive = true,
  onBack,
  onPreview,
  onShare,
}: Props) {
  const confirm = useConfirm();
  const [playlist, setPlaylist] = useState<Playlist | null>(() => readPlaylistShell(playlistId));
  const [catalog, setCatalog] = useState<NativeScreenCatalogItem[]>([]);
  const [uiContent, setUiContent] = useState<TvDashboardUiContent | null>(null);
  const [branchScope, setBranchScope] = useState<BranchScope | null>(null);
  const [loading, setLoading] = useState(() => !readPlaylistShell(playlistId));
  const [error, setError] = useState<string | null>(null);
  const [selectedSlideId, setSelectedSlideId] = useState<string | null>(null);
  const [tvStatus, setTvStatus] = useState<PresentationStatus | null>(null);
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const [previewBySlideId, setPreviewBySlideId] = useState<
    Record<string, PresentationPayload["slides"][number]>
  >({});
  const saveComunicadoTimerRef = useRef<number | null>(null);
  const wsDraftTimerRef = useRef<number | null>(null);
  const pendingComunicadoSaveRef = useRef<{
    slide: Slide;
    nativeConfig: Record<string, unknown>;
    version: number;
  } | null>(null);
  const comunicadoAutosaveVersionRef = useRef<Map<string, number>>(new Map());
  const slideClipboardRef = useRef<SlideClipboardPayload | null>(null);
  const [slideClipboardRevision, setSlideClipboardRevision] = useState(0);
  const [exportBusy, setExportBusy] = useState(false);
  const [presencePeers, setPresencePeers] = useState<PresentationPresencePeer[]>([]);
  const [remoteSelectionsByClientId, setRemoteSelectionsByClientId] = useState<
    Record<string, PresentationSelectionUpdateEvent>
  >({});
  /** Bump a cada mudança vinda de outro editor (WS) — o editor aceita o novo value. */
  const [remoteConfigRevision, setRemoteConfigRevision] = useState(0);
  const playlistRef = useRef<Playlist | null>(null);
  const selectedSlideIdRef = useRef<string | null>(null);
  const liveComunicadoConfigRef = useRef<Record<string, unknown> | null>(null);
  const flushPendingComunicadoSaveRef = useRef<(() => Promise<void>) | null>(null);

  playlistRef.current = playlist;
  selectedSlideIdRef.current = selectedSlideId;

  useEffect(() => {
    if (playlist) writePlaylistShell(playlist);
  }, [playlist]);

  /** Troca de slide: flush autosave do slide anterior e alinha ref live ao alvo. */
  const selectSlide = useCallback(
    (slideId: string, slideHint?: Slide | null) => {
      const pending = pendingComunicadoSaveRef.current;
      if (pending && pending.slide.id !== slideId) {
        void flushPendingComunicadoSaveRef.current?.();
      }
      setSelectedSlideId(slideId);
      writeSelectedSlideId(playlistId, slideId);
      const slide =
        slideHint ?? playlistRef.current?.slides?.find((item) => item.id === slideId) ?? null;
      if (slide?.nativeScreenKey === "custom_message") {
        liveComunicadoConfigRef.current = slide.nativeConfig ?? {};
      } else {
        liveComunicadoConfigRef.current = null;
      }
    },
    [playlistId],
  );

  const applyDeckSnapshot = useCallback(
    (snapshot: DeckEditorSnapshot) => {
      setPlaylist(snapshot.playlist);
      setSelectedSlideId(snapshot.selectedSlideId);
      writeSelectedSlideId(playlistId, snapshot.selectedSlideId);
      const slide = snapshot.selectedSlideId
        ? snapshot.playlist.slides?.find((item) => item.id === snapshot.selectedSlideId)
        : null;
      if (slide?.nativeScreenKey === "custom_message") {
        liveComunicadoConfigRef.current = slide.nativeConfig ?? {};
      }
    },
    [playlistId],
  );

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
      playlistId,
      recordBeforeChange: deckHistory.recordBeforeChange,
      confirmChange: deckHistory.confirmChange,
      cancelChange: deckHistory.cancelChange,
      undo: deckHistory.undo,
      redo: deckHistory.redo,
      canUndo: deckHistory.canUndo,
      canRedo: deckHistory.canRedo,
      historyEpoch: deckHistory.historyEpoch,
      historyPage: deckHistory.historyPage,
      loading: deckHistory.loading,
      restoring: deckHistory.restoring,
      error: deckHistory.error,
      loadHistory: deckHistory.loadHistory,
      restoreRevision: deckHistory.restoreRevision,
      setLiveComunicadoConfig: (config) => {
        liveComunicadoConfigRef.current = config;
      },
    }),
    [
      deckHistory.canRedo,
      deckHistory.canUndo,
      deckHistory.cancelChange,
      deckHistory.confirmChange,
      deckHistory.error,
      deckHistory.historyPage,
      deckHistory.historyEpoch,
      deckHistory.loadHistory,
      deckHistory.loading,
      deckHistory.recordBeforeChange,
      deckHistory.redo,
      deckHistory.restoreRevision,
      deckHistory.restoring,
      deckHistory.undo,
      playlistId,
    ],
  );

  useDeckEditorKeyboard({
    undo: deckHistory.undo,
    redo: deckHistory.redo,
    canUndo: deckHistory.canUndo && !deckHistory.restoring,
    canRedo: deckHistory.canRedo && !deckHistory.restoring,
  });

  const slides = useMemo(
    () => [...(playlist?.slides ?? [])].sort((a, b) => a.sortOrder - b.sortOrder),
    [playlist?.slides],
  );

  const selectedSlide = useMemo(
    () => slides.find((slide) => slide.id === selectedSlideId) ?? slides[0] ?? null,
    [slides, selectedSlideId],
  );

  const editorComunicadoValue = useMemo(() => {
    if (!selectedSlide || selectedSlide.nativeScreenKey !== "custom_message") {
      return null;
    }
    return serializeComunicadoConfig(parseComunicadoConfig(selectedSlide.nativeConfig ?? {}));
  }, [selectedSlide]);

  /** Estrutura do filmstrip (sem nativeConfig) — evita re-enrich operacional a cada autosave. */
  const slidesStructureKey = useMemo(
    () =>
      slides
        .map(
          (slide) =>
            `${slide.id}:${slide.title}:${slide.slideType}:${slide.nativeScreenKey ?? ""}:${slide.externalUrl ?? ""}:${slide.isActive}`,
        )
        .join("|"),
    [slides],
  );

  const accessToken = getAccessToken();
  const editorPresence = useMemo(
    () =>
      accessToken
        ? {
            clientId: getEditorPresenceClientId(),
            displayName: resolveEditorDisplayName(accessToken),
            role: "editor" as const,
          }
        : undefined,
    [accessToken],
  );

  const otherEditors = useMemo(
    () =>
      presencePeers.filter(
        (peer) => peer.role === "editor" && peer.clientId !== editorPresence?.clientId,
      ),
    [presencePeers, editorPresence?.clientId],
  );

  const currentRemoteSelections = useMemo(
    () =>
      Object.values(remoteSelectionsByClientId).filter(
        (selection) => selection.slideId === selectedSlideId,
      ),
    [remoteSelectionsByClientId, selectedSlideId],
  );

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
      // Mantém miniaturas anteriores — limpar no erro apaga o filmstrip e causa flash.
    }
  }, [playlistId, slides.length]);

  const reloadPlaylistFromServer = useCallback(async () => {
    try {
      const pl = await getPlaylist(playlistId);
      setPlaylist((current) => {
        const remoteSlides = pl.slides ?? current?.slides ?? [];
        const pending = pendingComunicadoSaveRef.current;
        const activeId = selectedSlideIdRef.current;
        const slides = remoteSlides.map((slide) => {
          if (
            pending &&
            activeId &&
            slide.id === activeId &&
            slide.id === pending.slide.id &&
            slide.nativeScreenKey === "custom_message"
          ) {
            return { ...slide, nativeConfig: pending.nativeConfig };
          }
          return slide;
        });
        return current ? { ...pl, slides } : { ...pl, slides };
      });
      setRemoteConfigRevision((revision) => revision + 1);
      await refreshPreviewThumbnails();
    } catch {
      // mantém estado local se a sincronização falhar
    }
  }, [playlistId, refreshPreviewThumbnails]);

  const applyRemoteSlideDraft = useCallback(
    (slideId: string, nativeConfig: Record<string, unknown>, clientId: string) => {
      if (clientId === editorPresence?.clientId) return;
      const pending = pendingComunicadoSaveRef.current;
      if (pending?.slide.id === slideId) return;

      setPlaylist((current) => {
        if (!current) return current;
        return {
          ...current,
          slides: (current.slides ?? []).map((slide) =>
            slide.id === slideId && slide.nativeScreenKey === "custom_message"
              ? { ...slide, nativeConfig }
              : slide,
          ),
        };
      });

      if (selectedSlideIdRef.current === slideId) {
        liveComunicadoConfigRef.current = nativeConfig;
      }
      setRemoteConfigRevision((revision) => revision + 1);
    },
    [editorPresence?.clientId],
  );

  useEffect(() => {
    void refreshPreviewThumbnails();
  }, [refreshPreviewThumbnails, playlistId, slidesStructureKey]);

  useEffect(() => {
    setSelectedSlideId(null);
    liveComunicadoConfigRef.current = null;
  }, [playlistId]);

  useEffect(() => {
    if (!slides.length) {
      setSelectedSlideId(null);
      writeSelectedSlideId(playlistId, null);
      return;
    }
    if (selectedSlideId && slides.some((slide) => slide.id === selectedSlideId)) {
      return;
    }
    const nextId = resolveSelectedSlideId(
      playlistId,
      slides.map((slide) => slide.id),
    );
    if (nextId) {
      const slide = slides.find((item) => item.id === nextId) ?? null;
      selectSlide(nextId, slide);
      return;
    }
    setSelectedSlideId(null);
    writeSelectedSlideId(playlistId, null);
  }, [slides, selectedSlideId, playlistId, selectSlide]);

  const handlePresenceUpdate = useCallback((peers: PresentationPresencePeer[]) => {
    setPresencePeers(peers);
    const activeClientIds = new Set(peers.map((peer) => peer.clientId));
    setRemoteSelectionsByClientId((current) =>
      Object.fromEntries(
        Object.entries(current).filter(([clientId]) => activeClientIds.has(clientId)),
      ),
    );
  }, []);

  const handleRemoteSelection = useCallback(
    (event: PresentationSelectionUpdateEvent) => {
      if (event.clientId === editorPresence?.clientId) return;
      setRemoteSelectionsByClientId((current) => {
        if (event.selectedIds.length === 0) {
          const next = { ...current };
          delete next[event.clientId];
          return next;
        }
        return { ...current, [event.clientId]: event };
      });
    },
    [editorPresence?.clientId],
  );

  const { sendRealtime: wsSendRef } = usePlaylistEditorSync({
    playlistId,
    accessToken,
    presence: editorPresence,
    onPresenceUpdate: handlePresenceUpdate,
    onSync: () => {
      void reloadPlaylistFromServer().then(() => deckHistory.handleRemoteUpdate());
    },
    onSlideDraft: (event) => {
      applyRemoteSlideDraft(event.slideId, event.nativeConfig, event.clientId);
    },
    onSelectionUpdate: handleRemoteSelection,
  });

  const sendSelectionUpdate = useCallback(
    (slideId: string, selectedIds: string[]) => {
      const clientId = editorPresence?.clientId;
      if (!clientId) return;
      wsSendRef.current?.({
        type: "selection_update",
        slideId,
        clientId,
        selectedIds,
      });
    },
    [editorPresence?.clientId, wsSendRef],
  );

  const load = useCallback(async () => {
    const cached = readPlaylistShell(playlistId);
    // Soft-load: com shell em sessão, não blanka a página no F5 enquanto a API responde.
    if (cached) {
      setPlaylist(mergePlaylistSlidesWithComunicadoDrafts(playlistId, cached));
      setLoading(false);
    } else {
      setLoading(true);
    }
    setError(null);
    try {
      const [pl, screens, ui, scope] = await Promise.all([
        getPlaylist(playlistId),
        listNativeScreens(),
        getUiContent(),
        getBranchScope(),
      ]);
      const merged = mergePlaylistSlidesWithComunicadoDrafts(playlistId, pl);
      setPlaylist(merged);
      writePlaylistShell(merged);
      // Reenvia à API drafts locais ainda não confirmados (ex.: F5 no meio do debounce).
      for (const slide of merged.slides ?? []) {
        if (slide.nativeScreenKey !== "custom_message") continue;
        const draft = readComunicadoSlideDraft(playlistId, slide.id);
        if (!draft) continue;
        void updateSlide(playlistId, slide.id, {
          title: slide.title,
          durationSec: slide.durationSec ?? merged.defaultDurationSec ?? 30,
          nativeConfig: draft.nativeConfig,
        })
          .then(() => clearComunicadoSlideDraft(playlistId, slide.id))
          .catch(() => {
            /* draft permanece */
          });
      }
      setCatalog(screens);
      setUiContent(ui);
      setBranchScope(scope);
    } catch (err) {
      if (!cached) {
        setError(err instanceof Error ? err.message : "Erro ao carregar programação.");
      } else {
        tvDashboardNotice(err instanceof Error ? err.message : "Erro ao atualizar programação.");
      }
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

  async function saveSettings(field: string, value: string | number | Record<string, unknown>) {
    if (!playlist) return;
    deckHistory.recordBeforeChange();
    try {
      const updated = await updatePlaylist(playlist.id, { [field]: value } as Parameters<typeof updatePlaylist>[1]);
      setPlaylist({ ...updated, slides: playlist.slides });
      await deckHistory.confirmChange();
    } catch (caught) {
      deckHistory.cancelChange();
      throw caught;
    }
  }

  async function handleExportPng() {
    if (!selectedSlide) return;
    const target = resolveSlideExportTarget(document.querySelector(".td-deck-stage__main"));
    if (!target) {
      tvDashboardNotice("Não foi possível localizar o palco para exportar.");
      return;
    }
    setExportBusy(true);
    try {
      const safeTitle = selectedSlide.title.replace(/[^\w\-]+/g, "_").slice(0, 40) || "slide";
      await exportSlideElementToPng(target, { fileName: `${safeTitle}.png` });
    } catch (err) {
      tvDashboardNotice(err instanceof Error ? err.message : "Falha ao exportar PNG.");
    } finally {
      setExportBusy(false);
    }
  }

  async function handleExportPdf() {
    if (!selectedSlide) return;
    const target = resolveSlideExportTarget(document.querySelector(".td-deck-stage__main"));
    if (!target) {
      tvDashboardNotice("Não foi possível localizar o palco para exportar.");
      return;
    }
    setExportBusy(true);
    try {
      const safeTitle = selectedSlide.title.replace(/[^\w\-]+/g, "_").slice(0, 40) || "slide";
      await exportSlideElementToPdf(target, { fileName: `${safeTitle}.pdf` });
    } catch (err) {
      tvDashboardNotice(err instanceof Error ? err.message : "Falha ao exportar PDF.");
    } finally {
      setExportBusy(false);
    }
  }

  async function handleExportPptx() {
    if (!selectedSlide) return;
    if (selectedSlide.nativeScreenKey !== "custom_message") {
      tvDashboardNotice("A exportação PPTX MVP está disponível para telas personalizadas.");
      return;
    }
    setExportBusy(true);
    try {
      const safeTitle = selectedSlide.title.replace(/[^\w\-]+/g, "_").slice(0, 40) || "slide";
      const rawConfig = liveComunicadoConfigRef.current ?? selectedSlide.nativeConfig ?? {};
      await exportSlidePptx(
        enrichComunicadoConfigForEditor(rawConfig, playlistId),
        `${safeTitle}.pptx`,
      );
    } catch (err) {
      tvDashboardNotice(err instanceof Error ? err.message : "Falha ao exportar PPTX.");
    } finally {
      setExportBusy(false);
    }
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
    try {
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
      selectSlide(slide.id, slide);
      await deckHistory.confirmChange();
    } catch (caught) {
      deckHistory.cancelChange();
      throw caught;
    }
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
    try {
      await deleteSlide(playlist.id, slide.id);
      const remaining = (playlist.slides ?? []).filter((item) => item.id !== slide.id);
      setPlaylist({ ...playlist, slides: remaining });
      if (selectedSlideId === slide.id) {
        const nextId = remaining[0]?.id ?? null;
        if (nextId) selectSlide(nextId);
        else {
          setSelectedSlideId(null);
          liveComunicadoConfigRef.current = null;
          writeSelectedSlideId(playlistId, null);
        }
      }
      await deckHistory.confirmChange();
    } catch (caught) {
      deckHistory.cancelChange();
      throw caught;
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
    tvDashboardNotice("Novo link gerado.");
  }

  async function handleSaveSlide(
    slide: Slide,
    payload: {
      title: string;
      durationSec: number;
      nativeConfig?: Record<string, unknown>;
      externalUrl?: string | null;
      transitionStyle?: string | null;
    },
    options?: { recordHistory?: boolean; autosaveVersion?: number },
  ) {
    if (!playlist) return;
    if (options?.recordHistory) deckHistory.recordBeforeChange();
    try {
      const updated = await updateSlide(playlist.id, slide.id, payload);
      const latestVersion = comunicadoAutosaveVersionRef.current.get(slide.id) ?? 0;
      const completedVersion = options?.autosaveVersion;

      if (payload.nativeConfig) {
        if (
          shouldClearComunicadoDraftAfterSave({
            completedVersion,
            latestVersion,
          })
        ) {
          clearComunicadoSlideDraft(playlist.id, slide.id);
        }
        if (
          shouldClearComunicadoPendingAfterSave({
            pending: pendingComunicadoSaveRef.current
              ? {
                  slideId: pendingComunicadoSaveRef.current.slide.id,
                  nativeConfig: pendingComunicadoSaveRef.current.nativeConfig,
                  version: pendingComunicadoSaveRef.current.version,
                }
              : null,
            slideId: slide.id,
            completedVersion,
          })
        ) {
          pendingComunicadoSaveRef.current = null;
        }
      }

      setPlaylist((current) => {
        if (!current) return current;
        const resolvedNative = payload.nativeConfig
          ? resolveNativeConfigAfterAutosave({
              slideId: slide.id,
              serverNativeConfig: updated.nativeConfig,
              completedVersion,
              latestVersion,
              pending: pendingComunicadoSaveRef.current
                ? {
                    slideId: pendingComunicadoSaveRef.current.slide.id,
                    nativeConfig: pendingComunicadoSaveRef.current.nativeConfig,
                    version: pendingComunicadoSaveRef.current.version,
                  }
                : null,
              liveConfig: liveComunicadoConfigRef.current,
              selectedSlideId: selectedSlideIdRef.current,
            })
          : updated.nativeConfig;
        return {
          ...current,
          slides: (current.slides ?? []).map((item) =>
            item.id === slide.id
              ? {
                  ...updated,
                  nativeConfig: resolvedNative ?? updated.nativeConfig,
                }
              : item,
          ),
        };
      });
      await deckHistory.confirmChange();
    } catch (caught) {
      if (options?.recordHistory) deckHistory.cancelChange();
      throw caught;
    }
  }

  const persistComunicadoPending = useCallback(
    async (captured: {
      slide: Slide;
      nativeConfig: Record<string, unknown>;
      version: number;
    }) => {
      const pl = playlistRef.current;
      if (!pl) return;
      try {
        const updated = await updateSlide(pl.id, captured.slide.id, {
          title: captured.slide.title,
          durationSec: captured.slide.durationSec ?? pl.defaultDurationSec ?? 30,
          nativeConfig: captured.nativeConfig,
        });
        const latestVersion = comunicadoAutosaveVersionRef.current.get(captured.slide.id) ?? 0;
        if (
          shouldClearComunicadoDraftAfterSave({
            completedVersion: captured.version,
            latestVersion,
          })
        ) {
          clearComunicadoSlideDraft(pl.id, captured.slide.id);
        }
        setPlaylist((current) => {
          if (!current) return current;
          const resolvedNative = resolveNativeConfigAfterAutosave({
            slideId: captured.slide.id,
            serverNativeConfig: updated.nativeConfig,
            completedVersion: captured.version,
            latestVersion,
            pending: pendingComunicadoSaveRef.current
              ? {
                  slideId: pendingComunicadoSaveRef.current.slide.id,
                  nativeConfig: pendingComunicadoSaveRef.current.nativeConfig,
                  version: pendingComunicadoSaveRef.current.version,
                }
              : null,
            liveConfig: liveComunicadoConfigRef.current,
            selectedSlideId: selectedSlideIdRef.current,
          });
          return {
            ...current,
            slides: (current.slides ?? []).map((item) =>
              item.id === captured.slide.id
                ? { ...updated, nativeConfig: resolvedNative ?? updated.nativeConfig }
                : item,
            ),
          };
        });
        await deckHistory.confirmChange();
      } catch {
        // Draft permanece no localStorage. Reenfileira só se não houver pending mais novo.
        const currentPending = pendingComunicadoSaveRef.current;
        if (
          !currentPending ||
          (currentPending.slide.id === captured.slide.id &&
            currentPending.version < captured.version)
        ) {
          pendingComunicadoSaveRef.current = captured;
        }
        deckHistory.cancelChange();
      }
    },
    [deckHistory.cancelChange, deckHistory.confirmChange],
  );

  const flushPendingComunicadoSave = useCallback(async () => {
    const pending = pendingComunicadoSaveRef.current;
    if (!pending) return;
    if (saveComunicadoTimerRef.current) {
      window.clearTimeout(saveComunicadoTimerRef.current);
      saveComunicadoTimerRef.current = null;
    }
    pendingComunicadoSaveRef.current = null;
    await persistComunicadoPending(pending);
  }, [persistComunicadoPending]);

  flushPendingComunicadoSaveRef.current = flushPendingComunicadoSave;

  function scheduleCustomSlideSave(slide: Slide, nativeConfig: Record<string, unknown>) {
    const previous = pendingComunicadoSaveRef.current;
    if (previous && previous.slide.id !== slide.id) {
      if (saveComunicadoTimerRef.current) {
        window.clearTimeout(saveComunicadoTimerRef.current);
        saveComunicadoTimerRef.current = null;
      }
      pendingComunicadoSaveRef.current = null;
      void persistComunicadoPending(previous);
    }

    liveComunicadoConfigRef.current = nativeConfig;
    writeComunicadoSlideDraft(playlistId, slide.id, nativeConfig);
    const version = bumpComunicadoAutosaveVersion(comunicadoAutosaveVersionRef.current, slide.id);
    pendingComunicadoSaveRef.current = { slide, nativeConfig, version };
    // Otimista: atualiza nativeConfig no estado já — o save API continua debounced.
    // Sem isso, re-renders (WS/thumbnails) reaplicam o config antigo no editor mid-drag.
    setPlaylist((current) => {
      if (!current) return current;
      return {
        ...current,
        slides: (current.slides ?? []).map((item) =>
          item.id === slide.id ? { ...item, nativeConfig } : item,
        ),
      };
    });
    if (saveComunicadoTimerRef.current) window.clearTimeout(saveComunicadoTimerRef.current);
    saveComunicadoTimerRef.current = window.setTimeout(() => {
      void handleSaveSlide(
        slide,
        {
          title: slide.title,
          durationSec: slide.durationSec ?? playlistRef.current?.defaultDurationSec ?? 30,
          nativeConfig,
        },
        { autosaveVersion: version },
      );
    }, 700);

    if (wsDraftTimerRef.current) window.clearTimeout(wsDraftTimerRef.current);
    wsDraftTimerRef.current = window.setTimeout(() => {
      const clientId = editorPresence?.clientId;
      if (!clientId) return;
      wsSendRef.current?.({
        type: "slide_draft",
        slideId: slide.id,
        clientId,
        nativeConfig,
      });
    }, 120);
  }

  useEffect(() => {
    const onLeave = () => {
      void flushPendingComunicadoSave();
    };
    window.addEventListener("pagehide", onLeave);
    window.addEventListener("beforeunload", onLeave);
    return () => {
      window.removeEventListener("pagehide", onLeave);
      window.removeEventListener("beforeunload", onLeave);
      void flushPendingComunicadoSave();
    };
  }, [flushPendingComunicadoSave]);

  async function handleDuplicateSlide(slide: Slide) {
    if (!playlist) return;
    deckHistory.recordBeforeChange();
    try {
      const copy = await duplicateSlide(playlist.id, slide.id);
      setPlaylist({ ...playlist, slides: [...(playlist.slides ?? []), copy] });
      selectSlide(copy.id, copy);
      await deckHistory.confirmChange();
    } catch (caught) {
      deckHistory.cancelChange();
      throw caught;
    }
  }

  function handleCopySlide(slide: Slide) {
    slideClipboardRef.current = slidePayloadForClipboard(slide);
    setSlideClipboardRevision((value) => value + 1);
  }

  async function handlePasteSlide() {
    if (!playlist || !slideClipboardRef.current) return;
    const payload = slideClipboardRef.current;
    deckHistory.recordBeforeChange();
    try {
      const slide = await addSlide(playlist.id, {
        ...payload,
        title: pasteTitleFromClipboard(payload),
        nativeScreenKey: payload.nativeScreenKey ?? undefined,
        nativeConfig: payload.nativeConfig ?? undefined,
        externalUrl: payload.externalUrl ?? undefined,
      });
      setPlaylist({ ...playlist, slides: [...(playlist.slides ?? []), slide] });
      selectSlide(slide.id, slide);
      await deckHistory.confirmChange();
    } catch (caught) {
      deckHistory.cancelChange();
      throw caught;
    }
  }

  const canPasteSlide = slideClipboardRef.current != null;
  void slideClipboardRevision;

  async function handleToggleSlideActive(slide: Slide) {
    if (!playlist) return;
    deckHistory.recordBeforeChange();
    try {
      const updated = await updateSlide(playlist.id, slide.id, { isActive: !slide.isActive });
      setPlaylist({
        ...playlist,
        slides: (playlist.slides ?? []).map((item) => (item.id === slide.id ? updated : item)),
      });
      await deckHistory.confirmChange();
    } catch (caught) {
      deckHistory.cancelChange();
      throw caught;
    }
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
    try {
      const result = await reorderSlides(playlist.id, items);
      setPlaylist({ ...playlist, slides: result.slides });
      setDragIndex(null);
      await deckHistory.confirmChange();
    } catch (caught) {
      deckHistory.cancelChange();
      throw caught;
    }
  }

  function copyLink() {
    if (!playlist?.publicUrl) return;
    void navigator.clipboard.writeText(playlist.publicUrl);
    tvDashboardNotice("Link copiado.");
  }

  function openQr() {
    void downloadQrPng(playlistId)
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        window.open(url, "_blank", "noopener,noreferrer");
        window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
      })
      .catch((err) => {
        tvDashboardNotice(err instanceof Error ? err.message : "Erro ao gerar QR.");
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
    onSelect: selectSlide,
    onDuplicate: (slide: Slide) => void handleDuplicateSlide(slide),
    onToggleActive: (slide: Slide) => void handleToggleSlideActive(slide),
    onRemove: (slide: Slide) => void handleRemoveSlide(slide),
    onExportPng: () => void handleExportPng(),
    onExportPdf: () => void handleExportPdf(),
    onExportPptx: isCustomSlide ? () => void handleExportPptx() : undefined,
    exportBusy,
    playlistChrome: {
      playlistName: playlist.name,
      tvStatusLabel: tvStatusLabel(),
      tvStatusClass: tvStatusClass(),
      linkActive: playlist.isActive,
      onBack,
      onPreview,
      onRefreshVisual: () => {
        void refreshPreviewThumbnails();
      },
      onShare,
      onCopyLink: copyLink,
      onQr: openQr,
      onRegenerateToken: () => void handleRegenerateToken(),
      onToggleLink: () => void handleToggleActive(),
      onDelete: () => void handleDelete(),
    },
  };

  const chromeProps = {
    playlist,
    slide: selectedSlide,
    catalog,
    branchScope,
    isCustomSlide,
    adminLabels: admin,
    slideDeck: slideDeckProps,
    onSavePlaylistSettings: (field: string, value: string | number | Record<string, unknown>) =>
      void saveSettings(field, value),
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
    canPasteSlide,
    viewportProfile: playlist.viewportProfile,
    masterConfig: playlist.masterConfig,
    onSelect: selectSlide,
    onDragStart: setDragIndex,
    onDrop: (index: number) => void handleDropSlide(index),
    onDragEnd: () => setDragIndex(null),
    onAdd: () => void handleAddCustomSlide(),
    onCopySlide: handleCopySlide,
    onPasteSlide: () => void handlePasteSlide(),
    onDuplicateSlide: (slide: Slide) => void handleDuplicateSlide(slide),
    onToggleSlideActive: (slide: Slide) => void handleToggleSlideActive(slide),
    onRemoveSlide: (slide: Slide) => void handleRemoveSlide(slide),
  };

  return (
    <EditorShortcutsProvider active={editorActive}>
    <DeckEditorHistoryProvider value={deckHistoryValue}>
      <KeyboardShortcutsTipsProvider>
      <DeckKeyTipsProvider>
      <div className="td-deck td-deck--editor">
      {otherEditors.length > 0 ? (
        <div className="td-editor-presence" role="status" aria-live="polite">
          Também editando: {otherEditors.map((peer) => peer.displayName).join(", ")}
        </div>
      ) : null}
      {isCustomSlide && selectedSlide && editorComunicadoValue ? (
        <ComunicadoEditorProvider
          playlistId={playlistId}
          globalRefreshSec={playlist.globalRefreshSec}
          slideId={selectedSlide.id}
          viewportProfile={playlist.viewportProfile}
          masterConfig={playlist.masterConfig}
          value={editorComunicadoValue}
          remoteRevision={remoteConfigRevision}
          remoteSelections={currentRemoteSelections}
          onSelectionChange={sendSelectionUpdate}
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
                    viewportProfile={playlist.viewportProfile}
                    masterConfig={playlist.masterConfig}
                  />
                </div>
              )
            }
          />
        </>
      )}

      </div>
      <KeyboardShortcutsCatalogModal />
      </DeckKeyTipsProvider>
      </KeyboardShortcutsTipsProvider>
    </DeckEditorHistoryProvider>
    </EditorShortcutsProvider>
  );
}
