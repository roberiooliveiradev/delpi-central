import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  parseComunicadoConfig,
  serializeComunicadoConfig,
  type PresentationPresencePeer,
  type PresentationSelectionUpdateEvent,
} from "@delpi/tv-dashboard-presentation";

import { rewriteAdminMediaUrlsForBrowser } from "../api/browserSafeMediaUrl";
import {
  activatePlaylist,
  addSlide,
  createPlaylistSection,
  deactivatePlaylist,
  deletePlaylist,
  deletePlaylistSection,
  deleteSlide,
  duplicateSlide,
  downloadQrPng,
  ensurePlaylistMainSection,
  getBranchScope,
  getPlaylist,
  getPreviewPayload,
  getPresentationStatus,
  getUiContent,
  listNativeScreens,
  listPlaylistSections,
  regeneratePlaylistToken,
  reorderPlaylistSections,
  reorderSlides,
  updatePlaylist,
  updatePlaylistSection,
  updateSlide,
  type BranchScope,
  type NativeScreenCatalogItem,
  type Playlist,
  type PlaylistSection,
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
import { SectionPropertiesPanel } from "../components/SectionPropertiesPanel";
import { SlideStagePreview } from "../components/SlideStagePreview";
import { enrichComunicadoConfigForEditor, mergeMasterConfigs } from "../components/slideCardPreview";
import { insertSlideAfterAnchor } from "../utils/insertSlideAfterAnchor";
import { assignSlideToSectionOrder } from "../utils/assignSlideToSectionOrder";
import { relocateFilmstripSlides } from "../utils/relocateFilmstripSlides";
import { claimSlidesForNewSection } from "../utils/claimSlidesForNewSection";
import {
  DeckEditorHistoryProvider,
  type DeckEditorHistoryContextValue,
} from "../context/deckEditorHistoryContext";
import { KeyboardShortcutsTipsProvider } from "../context/KeyboardShortcutsTipsProvider";
import { DeckKeyTipsProvider } from "../context/DeckKeyTipsProvider";
import { TvCopilotDockProvider } from "../context/tvCopilotDockContext";
import { EditorShortcutsProvider } from "../keyboard";
import { KeyboardShortcutsCatalogModal } from "../components/KeyboardShortcutsCatalogModal";
import { PlaylistRenameDialog } from "../components/PlaylistRenameDialog";
import { TvCopilotDockSlot } from "../components/TvCopilotDock";
import { TvDashboardScreenLoading } from "../components/TvDashboardScreenLoading";
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
import { ExportPdfDialog } from "../components/ExportPdfDialog";
import {
  exportActivePlaylistSlidesToPdf,
  resolvePlaylistDesignSize,
} from "../utils/exportPlaylistPdf";
import { exportSlideElementToPng, exportSlideElementToPdf, resolveSlideExportTarget } from "../utils/exportSlidePng";
import { exportSlidePptx } from "../utils/exportSlidePptx";
import { readPlaylistShell, writePlaylistShell } from "../utils/editorSessionCache";
import { registerPreviewHandoff } from "../utils/previewHandoff";
import { clearPreviewPayloadCache } from "../utils/previewPayloadCache";
import {
  resolveSelectedSlideId,
  writeSelectedSlideId,
} from "../utils/deckSelectedSlidePreferences";
import {
  ensureFilmstripSlideInSelection,
  resolveFilmstripSlideSelection,
  type FilmstripSelectionModifiers,
  type FilmstripSlideSelection,
} from "../utils/filmstripSlideSelection";
import {
  applyServerPlaylistPreservingLocalEdits,
  clearComunicadoSlideDraftIfCoveredBySave,
  hasLocalComunicadoEdits,
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
      durationSec: number | null;
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
  const [selectedSlideIds, setSelectedSlideIds] = useState<string[]>([]);
  const [filmstripRangeAnchorId, setFilmstripRangeAnchorId] = useState<string | null>(null);
  const [filmstripMultiMode, setFilmstripMultiMode] = useState(false);
  const [tvStatus, setTvStatus] = useState<PresentationStatus | null>(null);
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const [dragSlideIds, setDragSlideIds] = useState<string[]>([]);
  const [sectionPropertiesId, setSectionPropertiesId] = useState<string | null>(null);
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
  const [exportPdfOpen, setExportPdfOpen] = useState(false);
  const [exportPdfProgress, setExportPdfProgress] = useState<string | null>(null);
  const [renameOpen, setRenameOpen] = useState(false);
  const [renameBusy, setRenameBusy] = useState(false);
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

  /** Foco no slide primário (editor/autosave) sem limpar multi-seleção do filmstrip. */
  const focusPrimarySlide = useCallback(
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

  /** Troca de slide com seleção única (histórico, atalhos, add/paste). */
  const selectSlide = useCallback(
    (slideId: string, slideHint?: Slide | null) => {
      focusPrimarySlide(slideId, slideHint);
      setSelectedSlideIds([slideId]);
      setFilmstripRangeAnchorId(slideId);
      setFilmstripMultiMode(false);
    },
    [focusPrimarySlide],
  );

  const applyFilmstripSelection = useCallback(
    (next: FilmstripSlideSelection) => {
      setSelectedSlideIds(next.selectedIds);
      setFilmstripRangeAnchorId(next.rangeAnchorId);
      if (next.selectedIds.length <= 1) {
        setFilmstripMultiMode(false);
      }
      if (next.primaryId) {
        focusPrimarySlide(next.primaryId);
      }
    },
    [focusPrimarySlide],
  );

  const handleFilmstripSelect = useCallback(
    (slideId: string, modifiers: FilmstripSelectionModifiers = {}) => {
      const orderedIds = (playlistRef.current?.slides ?? []).map((slide) => slide.id);
      const previous: FilmstripSlideSelection = {
        selectedIds:
          selectedSlideIds.length > 0
            ? selectedSlideIds
            : selectedSlideId
              ? [selectedSlideId]
              : [],
        primaryId: selectedSlideId,
        rangeAnchorId: filmstripRangeAnchorId,
      };
      applyFilmstripSelection(
        resolveFilmstripSlideSelection({
          orderedIds,
          previous,
          targetId: slideId,
          modifiers,
        }),
      );
    },
    [applyFilmstripSelection, filmstripRangeAnchorId, selectedSlideId, selectedSlideIds],
  );

  const handleFilmstripLongPress = useCallback(
    (slideId: string) => {
      const orderedIds = (playlistRef.current?.slides ?? []).map((slide) => slide.id);
      const previous: FilmstripSlideSelection = {
        selectedIds:
          selectedSlideIds.length > 0
            ? selectedSlideIds
            : selectedSlideId
              ? [selectedSlideId]
              : [],
        primaryId: selectedSlideId,
        rangeAnchorId: filmstripRangeAnchorId,
      };
      setFilmstripMultiMode(true);
      applyFilmstripSelection(
        ensureFilmstripSlideInSelection({ orderedIds, previous, targetId: slideId }),
      );
    },
    [
      applyFilmstripSelection,
      filmstripRangeAnchorId,
      selectedSlideId,
      selectedSlideIds,
    ],
  );

  const clearFilmstripMultiSelection = useCallback(() => {
    if (selectedSlideId) {
      setSelectedSlideIds([selectedSlideId]);
      setFilmstripRangeAnchorId(selectedSlideId);
    } else {
      setSelectedSlideIds([]);
      setFilmstripRangeAnchorId(null);
    }
    setFilmstripMultiMode(false);
  }, [selectedSlideId]);

  const applyDeckSnapshot = useCallback(
    (snapshot: DeckEditorSnapshot) => {
      setPlaylist(snapshot.playlist);
      setSelectedSlideId(snapshot.selectedSlideId);
      writeSelectedSlideId(playlistId, snapshot.selectedSlideId);
      setSelectedSlideIds(snapshot.selectedSlideId ? [snapshot.selectedSlideId] : []);
      setFilmstripRangeAnchorId(snapshot.selectedSlideId);
      setFilmstripMultiMode(false);
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

  const sections = useMemo(
    () => [...(playlist?.sections ?? [])].sort((a, b) => a.sortOrder - b.sortOrder),
    [playlist?.sections],
  );

  const selectedSlide = useMemo(
    () => slides.find((slide) => slide.id === selectedSlideId) ?? slides[0] ?? null,
    [slides, selectedSlideId],
  );

  const sectionPropertiesTarget = useMemo(
    () => sections.find((section) => section.id === sectionPropertiesId) ?? null,
    [sections, sectionPropertiesId],
  );

  const selectedSlideMaster = useMemo(() => {
    if (!selectedSlide) return playlist?.masterConfig;
    const sectionMaster = selectedSlide.sectionId
      ? sections.find((section) => section.id === selectedSlide.sectionId)?.masterConfig
      : undefined;
    return mergeMasterConfigs(playlist?.masterConfig, sectionMaster);
  }, [playlist?.masterConfig, sections, selectedSlide]);

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
            `${slide.id}:${slide.title}:${slide.slideType}:${slide.nativeScreenKey ?? ""}:${slide.externalUrl ?? ""}:${slide.isActive}:${slide.sectionId ?? ""}`,
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
      const payload = rewriteAdminMediaUrlsForBrowser(await getPreviewPayload(playlistId));
      const next: Record<string, PresentationPayload["slides"][number]> = {};
      for (const slide of payload.slides) next[slide.id] = slide;
      setPreviewBySlideId(next);
    } catch {
      // Mantém miniaturas anteriores — limpar no erro apaga o filmstrip e causa flash.
    }
  }, [playlistId, slides.length]);

  const reloadPlaylistFromServer = useCallback(async (opts?: { focusSlideId?: string | null }) => {
    try {
      const pl = await getPlaylist(playlistId);
      const pending = pendingComunicadoSaveRef.current;
      const activeId = selectedSlideIdRef.current;
      // liveComunicadoConfigRef espelha o slide aberto — só sobrepõe o remoto
      // quando há save pendente de verdade (senão o WS do copiloto nunca entra).
      const live =
        pending && activeId && liveComunicadoConfigRef.current
          ? { slideId: activeId, nativeConfig: liveComunicadoConfigRef.current }
          : null;
      const merged = applyServerPlaylistPreservingLocalEdits({
        playlistId,
        remote: pl,
        pending: pending
          ? { slideId: pending.slide.id, nativeConfig: pending.nativeConfig }
          : null,
        live,
      });
      setPlaylist((current) => (current ? { ...merged } : merged));
      const dirty = hasLocalComunicadoEdits({
        playlistId,
        slideId: activeId,
        pendingSlideId: pending?.slide.id ?? null,
      });
      if (!dirty) {
        setRemoteConfigRevision((revision) => revision + 1);
        if (activeId && liveComunicadoConfigRef.current) {
          const remoteSlide = (merged.slides ?? []).find((s) => s.id === activeId);
          if (remoteSlide?.nativeScreenKey === "custom_message" && remoteSlide.nativeConfig) {
            liveComunicadoConfigRef.current = remoteSlide.nativeConfig;
          }
        }
      }
      const focusId = opts?.focusSlideId?.trim();
      if (focusId) {
        const created = (merged.slides ?? []).find((s) => s.id === focusId);
        if (created) {
          selectSlide(created.id, created);
        }
      }
      await refreshPreviewThumbnails();
    } catch {
      // mantém estado local se a sincronização falhar
    }
  }, [playlistId, refreshPreviewThumbnails, selectSlide]);

  const applyRemoteSlideDraft = useCallback(
    (slideId: string, nativeConfig: Record<string, unknown>, clientId: string) => {
      if (clientId === editorPresence?.clientId) return;
      const pending = pendingComunicadoSaveRef.current;
      if (pending?.slide.id === slideId) return;
      if (
        hasLocalComunicadoEdits({
          playlistId,
          slideId,
          pendingSlideId: pending?.slide.id ?? null,
        })
      ) {
        return;
      }

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
    [editorPresence?.clientId, playlistId],
  );

  useEffect(() => {
    void refreshPreviewThumbnails();
  }, [refreshPreviewThumbnails, playlistId, slidesStructureKey]);

  useEffect(() => {
    setSelectedSlideId(null);
    setSelectedSlideIds([]);
    setFilmstripRangeAnchorId(null);
    setFilmstripMultiMode(false);
    liveComunicadoConfigRef.current = null;
  }, [playlistId]);

  useEffect(() => {
    if (!slides.length) {
      setSelectedSlideId(null);
      setSelectedSlideIds([]);
      setFilmstripRangeAnchorId(null);
      setFilmstripMultiMode(false);
      writeSelectedSlideId(playlistId, null);
      return;
    }
    if (selectedSlideId && slides.some((slide) => slide.id === selectedSlideId)) {
      setSelectedSlideIds((prev) => {
        const pruned = prev.filter((id) => slides.some((slide) => slide.id === id));
        if (pruned.length === prev.length) return prev;
        if (pruned.length === 0 && selectedSlideId) return [selectedSlideId];
        return pruned;
      });
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
    setSelectedSlideIds([]);
    setFilmstripRangeAnchorId(null);
    setFilmstripMultiMode(false);
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
    enabled: editorActive,
    onPresenceUpdate: handlePresenceUpdate,
    onSync: (event) => {
      // Sync canônico (WS presentation_updated) — inclui mutações do copiloto via CRUD.
      void reloadPlaylistFromServer({ focusSlideId: event?.slideId ?? null }).then(() =>
        deckHistory.handleRemoteUpdate(),
      );
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
      // Nunca limpar draft sem guarda de versão — save antigo não pode apagar edição nova.
      for (const slide of merged.slides ?? []) {
        if (slide.nativeScreenKey !== "custom_message") continue;
        const draft = readComunicadoSlideDraft(playlistId, slide.id);
        if (!draft) continue;
        const draftVersion = draft.version;
        void updateSlide(playlistId, slide.id, {
          title: slide.title,
          durationSec: slide.durationSec ?? null,
          nativeConfig: draft.nativeConfig,
        })
          .then(() => {
            clearComunicadoSlideDraftIfCoveredBySave(playlistId, slide.id, draftVersion);
          })
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
    const previousPlaylist = playlist;
    // dataDefaults: otimista para fingerprint/preview atualizarem sem esperar o PATCH.
    if (field === "dataDefaults" && value && typeof value === "object") {
      setPlaylist({ ...playlist, dataDefaults: value as Record<string, unknown> });
    }
    if (field === "viewport" && value && typeof value === "object") {
      const patch = value as {
        viewportProfile?: string;
        viewportWidth?: number | null;
        viewportHeight?: number | null;
      };
      setPlaylist({
        ...playlist,
        viewportProfile: patch.viewportProfile ?? playlist.viewportProfile,
        viewportWidth: patch.viewportWidth ?? null,
        viewportHeight: patch.viewportHeight ?? null,
      });
    }
    try {
      const body =
        field === "viewport" && value && typeof value === "object"
          ? (value as Parameters<typeof updatePlaylist>[1])
          : ({ [field]: value } as Parameters<typeof updatePlaylist>[1]);
      const updated = await updatePlaylist(playlist.id, body);
      setPlaylist({ ...updated, slides: previousPlaylist.slides });
      await deckHistory.confirmChange();
    } catch (caught) {
      if (field === "dataDefaults" || field === "viewport") {
        setPlaylist(previousPlaylist);
      }
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

  function handleExportPdf() {
    if (!selectedSlide && slides.every((slide) => slide.isActive === false)) {
      tvDashboardNotice("Não há telas para exportar.");
      return;
    }
    setExportPdfProgress(null);
    setExportPdfOpen(true);
  }

  async function handleGenerateExportPdf(options: {
    scope: "playlist" | "current";
    pixelRatio: 1 | 2;
  }) {
    if (!playlist) return;
    const designSize = resolvePlaylistDesignSize(playlist);
    const safePlaylist = playlist.name.replace(/[^\w\-]+/g, "_").slice(0, 40) || "programacao";
    setExportBusy(true);
    setExportPdfProgress(options.scope === "playlist" ? "Preparando…" : "Capturando slide…");
    try {
      if (options.scope === "current") {
        if (!selectedSlide) {
          tvDashboardNotice("Selecione um slide para exportar.");
          return;
        }
        const target = resolveSlideExportTarget(document.querySelector(".td-deck-stage__main"));
        if (!target) {
          tvDashboardNotice("Não foi possível localizar o palco para exportar.");
          return;
        }
        const safeTitle =
          selectedSlide.title.replace(/[^\w\-]+/g, "_").slice(0, 40) || "slide";
        await exportSlideElementToPdf(target, {
          fileName: `${safeTitle}.pdf`,
          pixelRatio: options.pixelRatio,
          designSize,
        });
      } else {
        const result = await exportActivePlaylistSlidesToPdf({
          playlistId: playlist.id,
          slides,
          designSize,
          previewBySlideId,
          masterConfig: playlist.masterConfig,
          publicToken: playlist.publicToken,
          pixelRatio: options.pixelRatio,
          fileName: `${safePlaylist}.pdf`,
          onProgress: ({ current, total, slideTitle }) => {
            setExportPdfProgress(
              `Capturando ${current}/${total}${slideTitle ? ` · ${slideTitle}` : ""}`,
            );
          },
        });
        if (result.skipped > 0) {
          tvDashboardNotice(
            `PDF gerado com ${result.pageCount} página(s); ${result.skipped} tela(s) ignorada(s).`,
          );
        }
      }
      setExportPdfOpen(false);
      setExportPdfProgress(null);
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      tvDashboardNotice(err instanceof Error ? err.message : "Falha ao exportar PDF.");
    } finally {
      setExportBusy(false);
      setExportPdfProgress(null);
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

  /** Coloca o slide recém-criado abaixo da âncora (tela ativa) e persiste a ordem. */
  async function placeSlideAfterActive(newSlide: Slide, anchorId?: string | null) {
    if (!playlist) return newSlide;
    const prev = playlist.slides ?? [];
    const activeId = anchorId ?? selectedSlideId ?? selectedSlide?.id ?? null;
    const ordered = insertSlideAfterAnchor([...prev, newSlide], newSlide, activeId);
    const onlyAppended =
      ordered.length === prev.length + 1 &&
      ordered[ordered.length - 1]?.id === newSlide.id &&
      prev.every((slide, index) => ordered[index]?.id === slide.id);
    if (onlyAppended) {
      setPlaylist({ ...playlist, slides: ordered });
      return newSlide;
    }
    const items = ordered.map((item, sortOrder) => ({ id: item.id, sortOrder }));
    const result = await reorderSlides(playlist.id, items);
    setPlaylist({ ...playlist, slides: result.slides });
    return result.slides.find((item) => item.id === newSlide.id) ?? newSlide;
  }

  async function handleAddCustomSlide(explicitSectionId?: string | null) {
    if (!playlist) return;
    deckHistory.recordBeforeChange();
    const customCatalogItem = catalog.find((item) => item.key === "custom_message");
    const customCount = (playlist.slides ?? []).filter(
      (slide) => slide.nativeScreenKey === "custom_message",
    ).length;
    const baseTitle = customCatalogItem?.label ?? "Personalizado";
    const title = customCount === 0 ? baseTitle : `${baseTitle} ${customCount + 1}`;
    const anchorId = selectedSlideId ?? selectedSlide?.id ?? null;
    const anchorSectionId =
      explicitSectionId !== undefined
        ? explicitSectionId
        : (slides.find((slide) => slide.id === anchorId)?.sectionId ??
          selectedSlide?.sectionId ??
          null);
    try {
      if (explicitSectionId) {
        const target = sections.find((section) => section.id === explicitSectionId);
        if (target?.isCollapsed) {
          await updatePlaylistSection(playlist.id, explicitSectionId, { isCollapsed: false });
        }
      }
      const slide = await addSlide(playlist.id, {
        slideType: "native",
        title,
        nativeScreenKey: "custom_message",
        nativeConfig: serializeComunicadoConfig(
          parseComunicadoConfig({ headline: "", blocks: [] }),
        ),
        durationSec: null,
        transitionStyle: null,
        sectionId: anchorSectionId,
      });
      let placed = slide;
      if (explicitSectionId) {
        const ordered = assignSlideToSectionOrder(
          [...(playlist.slides ?? []), slide],
          slide.id,
          explicitSectionId,
        );
        const items = ordered.map((item, sortOrder) => ({ id: item.id, sortOrder }));
        const result = await reorderSlides(playlist.id, items);
        const nextSections =
          sections.find((section) => section.id === explicitSectionId)?.isCollapsed
            ? (playlist.sections ?? []).map((section) =>
                section.id === explicitSectionId ? { ...section, isCollapsed: false } : section,
              )
            : playlist.sections;
        setPlaylist({
          ...playlist,
          sections: nextSections,
          slides: result.slides.map((item) =>
            item.id === slide.id ? { ...item, sectionId: explicitSectionId } : item,
          ),
        });
        placed = result.slides.find((item) => item.id === slide.id) ?? {
          ...slide,
          sectionId: explicitSectionId,
        };
      } else {
        placed = await placeSlideAfterActive(slide, anchorId);
      }
      selectSlide(placed.id, placed);
      await deckHistory.confirmChange();
    } catch (caught) {
      deckHistory.cancelChange();
      throw caught;
    }
  }

  async function handleAddSection(explicitAnchorId?: string | null) {
    if (!playlist) return;
    deckHistory.recordBeforeChange();
    try {
      const main = await ensurePlaylistMainSection(playlist.id);
      let workingSections = await listPlaylistSections(playlist.id);
      if (!workingSections.some((section) => section.id === main.id)) {
        workingSections = [main, ...workingSections.filter((s) => !s.isMain)];
      }
      workingSections = [...workingSections].sort((a, b) => a.sortOrder - b.sortOrder);
      let localSlides = (playlist.slides ?? []).map((slide) =>
        slide.sectionId ? slide : { ...slide, sectionId: main.id },
      );

      const anchorId =
        explicitAnchorId !== undefined && explicitAnchorId !== null
          ? explicitAnchorId
          : (selectedSlideId ?? selectedSlide?.id ?? null);
      const anchor = anchorId
        ? localSlides.find((slide) => slide.id === anchorId) ?? null
        : null;

      const userCount = workingSections.filter((section) => !section.isMain).length;
      const maxOrder = workingSections.reduce(
        (max, section) => Math.max(max, section.sortOrder),
        -1,
      );

      if (!anchor) {
        const section = await createPlaylistSection(playlist.id, {
          name: `Seção ${userCount + 1}`,
          sortOrder: maxOrder + 1,
          isCollapsed: false,
        });
        setPlaylist({
          ...playlist,
          sections: [...workingSections.filter((s) => s.id !== section.id), section],
          slides: localSlides,
        });
        await deckHistory.confirmChange();
        return;
      }

      const claim = claimSlidesForNewSection(localSlides, workingSections, anchor.id);
      const afterSectionId = claim.anchorSectionId ?? main.id;
      const section = await createPlaylistSection(playlist.id, {
        name: `Seção ${userCount + 1}`,
        sortOrder: maxOrder + 1,
        isCollapsed: false,
      });

      const baseOrder = workingSections.filter((s) => s.id !== section.id);
      const afterIdx = baseOrder.findIndex((s) => s.id === afterSectionId);
      const insertAt = afterIdx >= 0 ? afterIdx + 1 : 1;
      const orderedSections = [...baseOrder];
      orderedSections.splice(insertAt, 0, section);
      const reorderItems = orderedSections.map((item, sortOrder) => ({
        id: item.id,
        sortOrder,
      }));
      workingSections = await reorderPlaylistSections(playlist.id, reorderItems);

      const claimSet = new Set(claim.claimIds);
      const beforeSet = new Set(claim.beforeIds);
      const sectionUpdates: Array<{ id: string; sectionId: string }> = [];
      localSlides = localSlides.map((slide) => {
        let nextSectionId = slide.sectionId ?? main.id;
        if (claimSet.has(slide.id)) nextSectionId = section.id;
        else if (beforeSet.has(slide.id) && !slide.sectionId) nextSectionId = main.id;
        else if (!slide.sectionId) nextSectionId = main.id;
        if (nextSectionId !== (slide.sectionId ?? null)) {
          sectionUpdates.push({ id: slide.id, sectionId: nextSectionId });
        }
        return { ...slide, sectionId: nextSectionId };
      });

      for (const update of sectionUpdates) {
        await updateSlide(playlist.id, update.id, { sectionId: update.sectionId });
      }

      const items = localSlides
        .slice()
        .sort((a, b) => a.sortOrder - b.sortOrder)
        .map((item, sortOrder) => ({ id: item.id, sortOrder }));
      const result = await reorderSlides(playlist.id, items);
      const nextSlides = result.slides.map((item) => {
        const local = localSlides.find((slide) => slide.id === item.id);
        return local ? { ...item, sectionId: local.sectionId } : item;
      });

      const expandIds = new Set(
        [section.id, afterSectionId].filter(Boolean) as string[],
      );
      for (const sectionId of expandIds) {
        const target = workingSections.find((s) => s.id === sectionId);
        if (target?.isCollapsed) {
          await updatePlaylistSection(playlist.id, sectionId, { isCollapsed: false });
        }
      }
      workingSections = workingSections.map((s) =>
        expandIds.has(s.id) ? { ...s, isCollapsed: false } : s,
      );

      setPlaylist({
        ...playlist,
        sections: workingSections,
        slides: nextSlides,
      });
      await deckHistory.confirmChange();
    } catch (caught) {
      deckHistory.cancelChange();
      throw caught;
    }
  }

  function resolveFilmstripDragIds(index: number): string[] {
    const slide = slides[index];
    if (!slide) return [];
    const multi =
      selectedSlideIds.includes(slide.id) && selectedSlideIds.length > 1
        ? slides.filter((item) => selectedSlideIds.includes(item.id)).map((item) => item.id)
        : [slide.id];
    return multi;
  }

  function beginFilmstripDrag(index: number) {
    setDragIndex(index);
    setDragSlideIds(resolveFilmstripDragIds(index));
  }

  function endFilmstripDrag() {
    setDragIndex(null);
    setDragSlideIds([]);
  }

  async function persistFilmstripRelocation(
    nextSlides: Slide[],
    options?: { expandSectionId?: string | null },
  ) {
    if (!playlist) return;
    const byId = new Map(slides.map((slide) => [slide.id, slide]));
    const sectionUpdates: Array<{ id: string; sectionId: string | null }> = [];
    for (const slide of nextSlides) {
      const prev = byId.get(slide.id);
      if (!prev) continue;
      if ((prev.sectionId ?? null) !== (slide.sectionId ?? null)) {
        sectionUpdates.push({ id: slide.id, sectionId: slide.sectionId ?? null });
      }
    }
    for (const update of sectionUpdates) {
      await updateSlide(playlist.id, update.id, { sectionId: update.sectionId });
    }
    const items = nextSlides.map((item, sortOrder) => ({ id: item.id, sortOrder }));
    const result = await reorderSlides(playlist.id, items);
    const sectionById = new Map(nextSlides.map((slide) => [slide.id, slide.sectionId ?? null]));
    const expandId = options?.expandSectionId ?? null;
    setPlaylist({
      ...playlist,
      sections: expandId
        ? (playlist.sections ?? []).map((section) =>
            section.id === expandId ? { ...section, isCollapsed: false } : section,
          )
        : playlist.sections,
      slides: result.slides.map((item) =>
        sectionById.has(item.id)
          ? { ...item, sectionId: sectionById.get(item.id) ?? null }
          : item,
      ),
    });
  }

  async function moveSlideToSection(sectionId: string | null) {
    if (!playlist) return;
    const movingIds =
      dragSlideIds.length > 0
        ? dragSlideIds
        : dragIndex != null && slides[dragIndex]
          ? [slides[dragIndex]!.id]
          : [];
    if (movingIds.length === 0) return;
    let targetSectionId = sectionId;
    if (targetSectionId == null) {
      const main =
        sections.find((section) => section.isMain) ??
        (await ensurePlaylistMainSection(playlist.id));
      targetSectionId = main.id;
      if (!sections.some((section) => section.id === main.id)) {
        setPlaylist((prev) =>
          prev
            ? {
                ...prev,
                sections: [main, ...(prev.sections ?? []).filter((s) => s.id !== main.id)],
              }
            : prev,
        );
      }
    }
    const ordered = relocateFilmstripSlides(slides, movingIds, {
      kind: "section",
      sectionId: targetSectionId,
    });
    const unchanged =
      ordered.length === slides.length &&
      ordered.every((slide, index) => {
        const prev = slides[index];
        return (
          prev != null &&
          prev.id === slide.id &&
          (prev.sectionId ?? null) === (slide.sectionId ?? null)
        );
      });
    if (unchanged) {
      endFilmstripDrag();
      return;
    }
    deckHistory.recordBeforeChange();
    try {
      const target = sections.find((section) => section.id === targetSectionId);
      if (target?.isCollapsed) {
        await updatePlaylistSection(playlist.id, targetSectionId, { isCollapsed: false });
      }
      await persistFilmstripRelocation(ordered, { expandSectionId: targetSectionId });
      endFilmstripDrag();
      await deckHistory.confirmChange();
    } catch (caught) {
      deckHistory.cancelChange();
      throw caught;
    }
  }

  async function patchSection(sectionId: string, patch: Partial<PlaylistSection>) {
    if (!playlist) return;
    deckHistory.recordBeforeChange();
    try {
      const updated = await updatePlaylistSection(playlist.id, sectionId, {
        name: patch.name,
        sortOrder: patch.sortOrder,
        isCollapsed: patch.isCollapsed,
        isActive: patch.isActive,
        defaultDurationSec: patch.defaultDurationSec,
        transitionStyle: patch.transitionStyle,
        masterConfig: patch.masterConfig,
      });
      setPlaylist({
        ...playlist,
        sections: (playlist.sections ?? []).map((item) =>
          item.id === sectionId ? updated : item,
        ),
      });
      await deckHistory.confirmChange();
    } catch (caught) {
      deckHistory.cancelChange();
      throw caught;
    }
  }

  async function handleDeleteSection(sectionId: string, deleteSlides: boolean) {
    if (!playlist) return;
    const section = sections.find((item) => item.id === sectionId);
    if (section?.isMain) {
      tvDashboardNotice("A seção principal não pode ser excluída.");
      return;
    }
    const main = sections.find((item) => item.isMain);
    const confirmed = await confirm({
      title: deleteSlides ? "Excluir seção e slides" : "Excluir seção",
      message: deleteSlides
        ? `Excluir a seção «${section?.name ?? ""}» e todos os slides nela?`
        : `Excluir a seção «${section?.name ?? ""}»? Os slides voltam para a seção Principal.`,
      confirmLabel: "Excluir",
      variant: "danger",
    });
    if (!confirmed) return;
    deckHistory.recordBeforeChange();
    try {
      await deletePlaylistSection(playlist.id, sectionId, { deleteSlides });
      const nextSections = (playlist.sections ?? []).filter((item) => item.id !== sectionId);
      const nextSlides = deleteSlides
        ? (playlist.slides ?? []).filter((slide) => slide.sectionId !== sectionId)
        : (playlist.slides ?? []).map((slide) =>
            slide.sectionId === sectionId
              ? { ...slide, sectionId: main?.id ?? null }
              : slide,
          );
      setPlaylist({ ...playlist, sections: nextSections, slides: nextSlides });
      if (sectionPropertiesId === sectionId) setSectionPropertiesId(null);
      if (selectedSlideId && !nextSlides.some((slide) => slide.id === selectedSlideId)) {
        const nextId = nextSlides[0]?.id ?? null;
        if (nextId) selectSlide(nextId);
        else {
          setSelectedSlideId(null);
          writeSelectedSlideId(playlistId, null);
        }
      }
      await deckHistory.confirmChange();
    } catch (caught) {
      deckHistory.cancelChange();
      throw caught;
    }
  }

  async function handleRenameSlide(slide: Slide, nextTitle: string) {
    if (!playlist) return;
    const title = nextTitle.trim();
    if (!title || title === slide.title) return;
    deckHistory.recordBeforeChange();
    try {
      const updated = await updateSlide(playlist.id, slide.id, { title });
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

  async function handleRemoveSlide(slide: Slide) {
    await handleRemoveSlides([slide]);
  }

  async function handleRemoveSlides(targets: Slide[]) {
    if (!playlist || targets.length === 0) return;
    const unique = targets.filter(
      (slide, index, list) => list.findIndex((item) => item.id === slide.id) === index,
    );
    const confirmed = await confirm({
      title: unique.length > 1 ? "Remover telas" : "Remover tela",
      message:
        unique.length > 1
          ? `Remover ${unique.length} telas? Esta ação não pode ser desfeita.`
          : `Remover a tela «${unique[0]?.title ?? ""}»? Esta ação não pode ser desfeita.`,
      confirmLabel: "Remover",
      variant: "danger",
    });
    if (!confirmed) return;
    deckHistory.recordBeforeChange();
    try {
      const removeIds = new Set(unique.map((slide) => slide.id));
      for (const slide of unique) {
        await deleteSlide(playlist.id, slide.id);
      }
      const remaining = (playlist.slides ?? []).filter((item) => !removeIds.has(item.id));
      setPlaylist({ ...playlist, slides: remaining });
      if (selectedSlideId && removeIds.has(selectedSlideId)) {
        const nextId = remaining[0]?.id ?? null;
        if (nextId) selectSlide(nextId);
        else {
          setSelectedSlideId(null);
          setSelectedSlideIds([]);
          setFilmstripRangeAnchorId(null);
          setFilmstripMultiMode(false);
          liveComunicadoConfigRef.current = null;
          writeSelectedSlideId(playlistId, null);
        }
      } else {
        setSelectedSlideIds((prev) => prev.filter((id) => !removeIds.has(id)));
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

  async function handleRenamePlaylist(name: string) {
    if (!playlist) return;
    setRenameBusy(true);
    try {
      await saveSettings("name", name);
      setRenameOpen(false);
      tvDashboardNotice("Programação renomeada.");
    } catch (err) {
      tvDashboardNotice(err instanceof Error ? err.message : "Erro ao renomear programação.");
    } finally {
      setRenameBusy(false);
    }
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
      durationSec: number | null;
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
        clearPreviewPayloadCache(playlist.id);
        if (
          shouldClearComunicadoDraftAfterSave({
            completedVersion,
            latestVersion,
          })
        ) {
          clearComunicadoSlideDraftIfCoveredBySave(
            playlist.id,
            slide.id,
            completedVersion ?? latestVersion,
          );
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
    async (
      captured: {
        slide: Slide;
        nativeConfig: Record<string, unknown>;
        version: number;
      },
      options?: { keepalive?: boolean },
    ) => {
      const pl = playlistRef.current;
      if (!pl) return;
      try {
        const updated = await updateSlide(
          pl.id,
          captured.slide.id,
          {
            title: captured.slide.title,
            durationSec: captured.slide.durationSec ?? null,
            nativeConfig: captured.nativeConfig,
          },
          { keepalive: options?.keepalive },
        );
        const latestVersion = comunicadoAutosaveVersionRef.current.get(captured.slide.id) ?? 0;
        if (
          shouldClearComunicadoDraftAfterSave({
            completedVersion: captured.version,
            latestVersion,
          })
        ) {
          clearComunicadoSlideDraftIfCoveredBySave(pl.id, captured.slide.id, captured.version);
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
      } catch (caught) {
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
        if (!options?.keepalive) {
          tvDashboardNotice(
            caught instanceof Error
              ? caught.message
              : "Falha ao salvar o slide. Suas alterações ficaram guardadas localmente.",
          );
        }
      }
    },
    [deckHistory.cancelChange, deckHistory.confirmChange],
  );

  const flushPendingComunicadoSave = useCallback(
    async (options?: { keepalive?: boolean }) => {
      const pending = pendingComunicadoSaveRef.current;
      if (!pending) return;
      if (saveComunicadoTimerRef.current) {
        window.clearTimeout(saveComunicadoTimerRef.current);
        saveComunicadoTimerRef.current = null;
      }
      // Com keepalive no unload, mantém pending até confirmar — draft já está no localStorage.
      if (!options?.keepalive) {
        pendingComunicadoSaveRef.current = null;
      }
      await persistComunicadoPending(pending, options);
    },
    [persistComunicadoPending],
  );

  flushPendingComunicadoSaveRef.current = () => flushPendingComunicadoSave();

  useEffect(() => {
    registerPreviewHandoff({
      flush: () => flushPendingComunicadoSave(),
    });
    return () => registerPreviewHandoff(null);
  }, [flushPendingComunicadoSave]);

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
    const version = bumpComunicadoAutosaveVersion(comunicadoAutosaveVersionRef.current, slide.id);
    writeComunicadoSlideDraft(playlistId, slide.id, nativeConfig, Date.now(), version);
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
          durationSec: slide.durationSec ?? null,
          nativeConfig,
        },
        { autosaveVersion: version },
      ).catch((caught) => {
        tvDashboardNotice(
          caught instanceof Error
            ? caught.message
            : "Falha ao salvar o slide. Suas alterações ficaram guardadas localmente.",
        );
      });
    }, 400);

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
      void flushPendingComunicadoSave({ keepalive: true });
    };
    window.addEventListener("pagehide", onLeave);
    window.addEventListener("beforeunload", onLeave);
    return () => {
      window.removeEventListener("pagehide", onLeave);
      window.removeEventListener("beforeunload", onLeave);
      void flushPendingComunicadoSave({ keepalive: true });
    };
  }, [flushPendingComunicadoSave]);

  async function handleDuplicateSlide(slide: Slide) {
    await handleDuplicateSlides([slide]);
  }

  async function handleDuplicateSlides(targets: Slide[]) {
    if (!playlist || targets.length === 0) return;
    await flushPendingComunicadoSave();
    const unique = targets.filter(
      (slide, index, list) => list.findIndex((item) => item.id === slide.id) === index,
    );
    deckHistory.recordBeforeChange();
    try {
      let lastPlaced: Slide | null = null;
      for (const slide of unique) {
        const copy = await duplicateSlide(playlist.id, slide.id);
        const placed = await placeSlideAfterActive(copy, lastPlaced?.id ?? slide.id);
        lastPlaced = placed;
      }
      if (lastPlaced) selectSlide(lastPlaced.id, lastPlaced);
      await deckHistory.confirmChange();
    } catch (caught) {
      deckHistory.cancelChange();
      throw caught;
    }
  }

  function handleCopySlide(slide: Slide) {
    const liveConfig =
      slide.id === selectedSlideId && liveComunicadoConfigRef.current
        ? liveComunicadoConfigRef.current
        : slide.nativeConfig;
    slideClipboardRef.current = slidePayloadForClipboard({
      ...slide,
      nativeConfig: liveConfig ?? null,
    });
    setSlideClipboardRevision((value) => value + 1);
  }

  async function handlePasteSlide() {
    if (!playlist || !slideClipboardRef.current) return;
    await flushPendingComunicadoSave();
    const payload = slideClipboardRef.current;
    const anchorId = selectedSlideId ?? selectedSlide?.id ?? null;
    deckHistory.recordBeforeChange();
    try {
      const anchorSectionId =
        slides.find((item) => item.id === anchorId)?.sectionId ??
        selectedSlide?.sectionId ??
        payload.sectionId ??
        null;
      const slide = await addSlide(playlist.id, {
        ...payload,
        title: pasteTitleFromClipboard(payload),
        nativeScreenKey: payload.nativeScreenKey ?? undefined,
        nativeConfig: payload.nativeConfig ?? undefined,
        externalUrl: payload.externalUrl ?? undefined,
        sectionId: anchorSectionId,
      });
      const placed = await placeSlideAfterActive(slide, anchorId);
      selectSlide(placed.id, placed);
      await deckHistory.confirmChange();
    } catch (caught) {
      deckHistory.cancelChange();
      throw caught;
    }
  }

  const canPasteSlide = slideClipboardRef.current != null;
  void slideClipboardRevision;

  async function handleToggleSlideActive(slide: Slide) {
    await handleToggleSlidesActive([slide]);
  }

  async function handleToggleSlidesActive(targets: Slide[]) {
    if (!playlist || targets.length === 0) return;
    const unique = targets.filter(
      (slide, index, list) => list.findIndex((item) => item.id === slide.id) === index,
    );
    deckHistory.recordBeforeChange();
    try {
      const updates = new Map<string, Slide>();
      for (const slide of unique) {
        const updated = await updateSlide(playlist.id, slide.id, { isActive: !slide.isActive });
        updates.set(updated.id, updated);
      }
      setPlaylist({
        ...playlist,
        slides: (playlist.slides ?? []).map((item) => updates.get(item.id) ?? item),
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
    if (!playlist) return;
    const movingIds =
      dragSlideIds.length > 0
        ? dragSlideIds
        : dragIndex != null && slides[dragIndex]
          ? [slides[dragIndex]!.id]
          : [];
    if (movingIds.length === 0) return;
    if (movingIds.length === 1 && dragIndex === targetIndex) {
      endFilmstripDrag();
      return;
    }
    const ordered = relocateFilmstripSlides(slides, movingIds, {
      kind: "index",
      targetIndex,
    });
    const unchanged =
      ordered.length === slides.length &&
      ordered.every((slide, index) => {
        const prev = slides[index];
        return (
          prev != null &&
          prev.id === slide.id &&
          (prev.sectionId ?? null) === (slide.sectionId ?? null)
        );
      });
    if (unchanged) {
      endFilmstripDrag();
      return;
    }
    deckHistory.recordBeforeChange();
    try {
      await persistFilmstripRelocation(ordered);
      endFilmstripDrag();
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

  if (loading) {
    return <TvDashboardScreenLoading label="Carregando programação…" variant="fullscreen" />;
  }
  if (error || !playlist) return <div className="td-state">{error ?? "Programação não encontrada."}</div>;

  const admin = uiContent?.admin ?? {};
  const isCustomSlide = selectedSlide?.nativeScreenKey === "custom_message";
  const activeSlideCount = slides.filter((slide) => slide.isActive !== false).length;

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
      editingPresence:
        otherEditors.length > 0
          ? `Também editando: ${otherEditors.map((peer) => peer.displayName).join(", ")}`
          : null,
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
      onRename: () => setRenameOpen(true),
    },
  };

  const chromeProps = {
    playlist,
    slide: selectedSlide,
    slides,
    sections,
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
    sections,
    playlistId,
    selectedSlideId: selectedSlide?.id ?? null,
    selectedSlideIds:
      selectedSlideIds.length > 0
        ? selectedSlideIds
        : selectedSlide?.id
          ? [selectedSlide.id]
          : [],
    multiMode: filmstripMultiMode,
    previewBySlideId,
    dragIndex,
    dragSlideIds,
    inactiveLabel: admin.slideInactive ?? "Pausada",
    canPasteSlide,
    viewportProfile: playlist.viewportProfile,
    viewportWidth: playlist.viewportWidth,
    viewportHeight: playlist.viewportHeight,
    masterConfig: playlist.masterConfig,
    defaultDurationSec: playlist.defaultDurationSec,
    defaultTransitionStyle: playlist.transitionStyle,
    publicToken: playlist.publicToken,
    onSelect: handleFilmstripSelect,
    onLongPressSelect: handleFilmstripLongPress,
    onClearMultiSelection: clearFilmstripMultiSelection,
    onDragStart: beginFilmstripDrag,
    onDrop: (index: number) => void handleDropSlide(index),
    onDragEnd: endFilmstripDrag,
    onAdd: () => void handleAddCustomSlide(),
    onAddSection: () => void handleAddSection(),
    onCreateSection: (slide: Slide) => void handleAddSection(slide.id),
    onAddInSection: (sectionId: string) => void handleAddCustomSlide(sectionId),
    onCopySlide: handleCopySlide,
    onPasteSlide: () => void handlePasteSlide(),
    onDuplicateSlide: (targets: Slide[]) => void handleDuplicateSlides(targets),
    onRenameSlide: (slide: Slide, title: string) => void handleRenameSlide(slide, title),
    onToggleSlideActive: (targets: Slide[]) => void handleToggleSlidesActive(targets),
    onRemoveSlide: (targets: Slide[]) => void handleRemoveSlides(targets),
    onSectionNameCommit: (sectionId: string, name: string) =>
      void patchSection(sectionId, { name }),
    onSectionToggleCollapsed: (sectionId: string, collapsed: boolean) =>
      void patchSection(sectionId, { isCollapsed: collapsed }),
    onSectionToggleActive: (sectionId: string, active: boolean) =>
      void patchSection(sectionId, { isActive: active }),
    onSectionDelete: (sectionId: string, deleteSlides: boolean) =>
      void handleDeleteSection(sectionId, deleteSlides),
    onSectionProperties: (sectionId: string) => setSectionPropertiesId(sectionId),
    onDropOnSection: (sectionId: string) => void moveSlideToSection(sectionId),
    onDropOnUnsectioned: () => void moveSlideToSection(null),
  };

  return (
    <EditorShortcutsProvider active={editorActive}>
    <DeckEditorHistoryProvider value={deckHistoryValue}>
      <KeyboardShortcutsTipsProvider>
      <DeckKeyTipsProvider>
      <TvCopilotDockProvider>
      <div className="td-deck td-deck--editor">
      {isCustomSlide && selectedSlide && editorComunicadoValue ? (
        <ComunicadoEditorProvider
          playlistId={playlistId}
          publicToken={playlist.publicToken}
          globalRefreshSec={playlist.globalRefreshSec}
          slideId={selectedSlide.id}
          viewportProfile={playlist.viewportProfile}
          viewportWidth={playlist.viewportWidth}
          viewportHeight={playlist.viewportHeight}
          masterConfig={selectedSlideMaster}
          playlistDefaults={playlist.dataDefaults}
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
            copilotPanel={
              <TvCopilotDockSlot
                playlistId={playlistId}
                slideId={selectedSlide?.id ?? null}
                branchScope={branchScope}
              />
            }
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
                    viewportWidth={playlist.viewportWidth}
                    viewportHeight={playlist.viewportHeight}
                    masterConfig={selectedSlideMaster}
                    publicToken={playlist.publicToken}
                  />
                </div>
              )
            }
          />
        </>
      )}

      </div>
      {sectionPropertiesTarget ? (
        <SectionPropertiesPanel
          open
          section={sectionPropertiesTarget}
          onClose={() => setSectionPropertiesId(null)}
          onSave={(patch) => {
            void patchSection(sectionPropertiesTarget.id, patch);
          }}
        />
      ) : null}
      <PlaylistRenameDialog
        open={renameOpen}
        initialName={playlist.name}
        busy={renameBusy}
        onClose={() => {
          if (!renameBusy) setRenameOpen(false);
        }}
        onConfirm={(name) => void handleRenamePlaylist(name)}
      />
      <ExportPdfDialog
        open={exportPdfOpen}
        onClose={() => {
          if (!exportBusy) setExportPdfOpen(false);
        }}
        onGenerate={(opts) => handleGenerateExportPdf(opts)}
        activeSlideCount={activeSlideCount}
        hasCurrentSlide={Boolean(selectedSlide)}
        progressLabel={exportPdfProgress}
        busy={exportBusy}
      />
      <KeyboardShortcutsCatalogModal />
      </TvCopilotDockProvider>
      </DeckKeyTipsProvider>
      </KeyboardShortcutsTipsProvider>
    </DeckEditorHistoryProvider>
    </EditorShortcutsProvider>
  );
}
