import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  parseComunicadoConfig,
  serializeComunicadoConfig,
  type PresentationPresencePeer,
  type PresentationSelectionUpdateEvent,
  type PresentationVisualCaptureRequestEvent,
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
  StaleWriteEpochError,
  updatePlaylist,
  updatePlaylistSection,
  updateSlide,
  type BranchScope,
  type WriteGuard,
  type NativeScreenCatalogItem,
  type Playlist,
  type PlaylistSection,
  type PresentationPayload,
  type PresentationStatus,
  type Slide,
  type TvDashboardUiContent,
} from "../api/tvDashboardApi";
import {
  getAccessToken,
  isRevisionConflictError,
  revisionConflictCurrentRevision,
} from "../api/httpClient";
import { ComunicadoEditorProvider } from "../components/comunicadoEditorContext";
import { CustomSlideEditorLayout } from "../components/CustomSlideEditorLayout";
import { DeckEditorChrome } from "../components/DeckEditorChrome";
import { DeckWorkspace } from "../components/DeckWorkspace";
import { SectionPropertiesPanel } from "../components/SectionPropertiesPanel";
import { SlideStagePreview } from "../components/SlideStagePreview";
import {
  buildSlideThumbnailNative,
  enrichComunicadoConfigForEditor,
  mergeMasterConfigs,
} from "../components/slideCardPreview";
import { insertSlideAfterAnchor } from "../utils/insertSlideAfterAnchor";
import { assignSlideToSectionOrder } from "../utils/assignSlideToSectionOrder";
import { relocateFilmstripSlides } from "../utils/relocateFilmstripSlides";
import type { ListDropEdge } from "../utils/listReorderDrag";
import { claimSlidesForNewSection } from "../utils/claimSlidesForNewSection";
import {
  DeckEditorHistoryProvider,
  type DeckEditorHistoryContextValue,
} from "../context/deckEditorHistoryContext";
import { KeyboardShortcutsTipsProvider } from "../context/KeyboardShortcutsTipsProvider";
import { DeckKeyTipsProvider } from "../context/DeckKeyTipsProvider";
import { EditorShortcutsProvider } from "../keyboard";
import { KeyboardShortcutsCatalogModal } from "../components/KeyboardShortcutsCatalogModal";
import { PlaylistRenameDialog } from "../components/PlaylistRenameDialog";
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
  captureOffscreenNativeToPngDataUrl,
  exportActivePlaylistSlidesToPdf,
  exportSlidesToPdf,
  resolvePlaylistDesignSize,
} from "../utils/exportPlaylistPdf";
import {
  captureSlideElementToPngDataUrl,
  downloadPngDataUrls,
  exportSlideElementToPng,
  exportSlideElementToPdf,
  resolveSlideExportTarget,
} from "../utils/exportSlidePng";
import { exportSlidesPptx } from "../utils/exportSlidePptx";
import {
  resolveExportPptxTargets,
  resolveExportSlideTargets,
  uniqueExportFileName,
} from "../utils/exportSlideSelection";
import { readPlaylistShell, writePlaylistShell } from "../utils/editorSessionCache";
import { registerPreviewHandoff } from "../utils/previewHandoff";
import { clearPreviewPayloadCache } from "../utils/previewPayloadCache";
import {
  resolveSelectedSlideId,
  writeSelectedSlideId,
} from "../utils/deckSelectedSlidePreferences";
import { resolvePresentationSyncFocusSlideId } from "../utils/presentationSyncFocusSlide";
import { normalizeEditorFocusBlockIds } from "../utils/editorFocusSelection";
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
  isComunicadoDraftApplicable,
  markComunicadoSlideDraftConflicted,
  mergePlaylistSlidesWithComunicadoDrafts,
  readComunicadoSlideDraft,
  writeComunicadoSlideDraft,
} from "../utils/comunicadoSlideDraftPreferences";
import type { MutationCommitMeta } from "../utils/presentationMutationClient";
import {
  bumpComunicadoAutosaveVersion,
  bumpSlidePeerActivity,
  resolveNativeConfigAfterAutosave,
  shouldClearComunicadoDraftAfterSave,
  shouldClearComunicadoPendingAfterSave,
  slidePeerActivityAdvanced,
} from "../utils/comunicadoSlideAutosave";
import {
  getEditorPresenceClientId,
  resolveEditorDisplayName,
} from "../utils/editorPresence";
import {
  detectSharedSlideWrite,
  publishPlaylistWriteHead,
  readSharedPlaylistRevision,
} from "../utils/playlistWriteHead";
import {
  hasPendingPlaylistWrite,
  onPlaylistWriteSettled,
} from "../utils/playlistWriteLane";
import {
  resolvePresentationSyncReloadDecision,
  shouldRecoverAmbiguousSyncEvent,
} from "../utils/presentationSyncReloadDecision";
import { handleVisualCaptureRequest } from "../utils/liveStageVisualCapture";
import {
  applySlideBatchPatch,
  isCustomMessageSlide,
  pickSharedCustomSlideConfig,
  resolveSelectedSlides,
  type SlideBatchInput,
} from "../utils/applySlideBatchPatch";
import { tvDashboardNotice } from "../utils/tvDashboardNotice";
import { publishPlaylistWorkspaceContext } from "../utils/workspaceContext";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";

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
  const playlistSettingsSaveGenRef = useRef(0);
  const pendingComunicadoSaveRef = useRef<{
    slide: Slide;
    nativeConfig: Record<string, unknown>;
    version: number;
    /** Revisão na qual o config pendente foi derivado (OCC). */
    baseRevision?: number | null;
    /** Época de escrita em que o payload foi capturado (conflito/reload bumpeia). */
    epoch?: number;
    /** Tick de atividade de peer do slide na captura (proteção same-slide). */
    peerTick?: number;
  } | null>(null);
  const customFanOutBaselineRef = useRef<{
    slideId: string;
    nativeConfig: Record<string, unknown>;
  } | null>(null);
  const selectedSlidesRef = useRef<Slide[]>([]);
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
  /**
   * Bump só quando a baseline externa é de OUTRO writer (revisão remota acima
   * do write-head compartilhado, ou draft de peer) — invalida undo/redo local.
   * Acks das próprias escritas sobem `remoteConfigRevision`, nunca este.
   */
  const [foreignConfigRevision, setForeignConfigRevision] = useState(0);
  const playlistRef = useRef<Playlist | null>(null);
  const selectedSlideIdRef = useRef<string | null>(null);
  const selectedSlideIdsRef = useRef<string[]>([]);
  const liveComunicadoConfigRef = useRef<Record<string, unknown> | null>(null);
  const flushPendingComunicadoSaveRef = useRef<(() => Promise<void>) | null>(null);
  /** Última revisão persistida conhecida — reads + write acks (OCC If-Match). */
  const knownPlaylistRevisionRef = useRef(0);
  /** Base OCC por slide para escritas de nativeConfig (draft/mutation/autosave). */
  const slideWriteBaseRevisionRef = useRef<Map<string, number>>(new Map());
  /**
   * Época de escrita: bumpeia quando o estado autoritativo vence (conflito).
   * Payloads capturados em época anterior são descartados na lane — nunca
   * sobrescrevem o estado recém-recarregado com snapshot pré-conflito.
   */
  const comunicadoWriteEpochRef = useRef(0);
  /**
   * Revisão de evento presentation_updated ambíguo (rev == tracked+1 com
   * escrita em voo) aguardando confirmação. Reconciliado obrigatoriamente
   * no settle da lane: ACK cobrindo a revisão prova commit próprio;
   * rejeição/timeout/cancelamento sem cobertura exige reload — a remota
   * nunca pode ficar permanentemente ignorada (VISTA-TV-024-R1).
   */
  const pendingAmbiguousSyncRevisionRef = useRef<number | null>(null);
  /**
   * Tick de atividade de peer por slide (drafts e commits WS de outro
   * clientId). Como o CAS é por playlist, commits de peer no mesmo slide não
   * geram 409 — este tick é o sinal local para tratá-los como conflito.
   */
  const slidePeerActivityRef = useRef(new Map<string, number>());

  playlistRef.current = playlist;
  selectedSlideIdRef.current = selectedSlideId;
  selectedSlideIdsRef.current = selectedSlideIds;

  useEffect(() => {
    if (playlist) writePlaylistShell(playlist);
  }, [playlist]);

  // §6.130: publish the current playlist + selected slide as a bounded
  // workspace hint — DÉLIA uses it to ground "slide atual" questions
  // via the owner capability (vista.get_playlist_context). Untrusted,
  // never authority.
  useEffect(() => {
    publishPlaylistWorkspaceContext({
      playlistId,
      viewRef: editorActive ? "deck_editor" : "deck_preview",
      selectedSlideId,
      playlistLabel: playlist?.name,
    });
  }, [playlistId, selectedSlideId, editorActive, playlist?.name]);

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

  const selectedSlides = useMemo(
    () => resolveSelectedSlides(slides, selectedSlideIds, selectedSlide),
    [slides, selectedSlideIds, selectedSlide],
  );
  selectedSlidesRef.current = selectedSlides;

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
        (peer) =>
          peer.role === "editor" &&
          peer.clientId !== editorPresence?.clientId &&
          // «Também editando» exige atividade real — conectado/oculto não conta.
          peer.active !== false,
      ),
    [presencePeers, editorPresence?.clientId],
  );

  /** Nome distinto por usuário — mesma conta em 2 sessões vira «Nome (2 sessões)». */
  const otherEditorsLabel = useMemo(() => {
    const byUser = new Map<string, { name: string; count: number }>();
    for (const peer of otherEditors) {
      const key = peer.userId ?? peer.displayName;
      const entry = byUser.get(key);
      if (entry) entry.count += 1;
      else byUser.set(key, { name: peer.displayName, count: 1 });
    }
    return [...byUser.values()]
      .map((entry) =>
        entry.count > 1 ? `${entry.name} (${entry.count} sessões)` : entry.name,
      )
      .join(", ");
  }, [otherEditors]);

  /**
   * Registra a revisão confirmada pelo write ack. Quando a resposta não
   * carrega playlistRevision, a guarda If-Match vencida prova expected+1
   * (o repositório incrementa a revisão exatamente uma vez por escrita).
   */
  const recordWriteRevision = useCallback(
    (
      revision: unknown,
      slideId?: string | null,
      expectedRevision?: WriteGuard["expectedRevision"],
    ) => {
      // Thunks resolvem no ack → ainda valem a revisão enviada (lane serializa).
      const expected =
        typeof expectedRevision === "function" ? expectedRevision() : expectedRevision;
      let next: number | null = null;
      if (typeof revision === "number" && Number.isFinite(revision)) {
        next = Math.trunc(revision);
      } else if (typeof expected === "number" && Number.isFinite(expected)) {
        next = Math.trunc(expected) + 1;
      }
      if (next == null) return;
      if (next > knownPlaylistRevisionRef.current) {
        knownPlaylistRevisionRef.current = next;
      }
      if (slideId) slideWriteBaseRevisionRef.current.set(slideId, next);
      // Publica o commit próprio para contextos irmãos (abas/janelas
      // same-origin) — o thunk deles resolve a revisão fresca dentro do
      // Web Lock e o freshness gate por slide detecta escrita concorrente.
      publishPlaylistWriteHead(playlistId, {
        revision: next,
        slideId: slideId ?? null,
        clientId: editorPresence?.clientId ?? null,
      });
      // 024-R1: ack ≥ revisão ambígua prova incorporação — commit == amb ou
      // a posição CAS (expected ≥ amb) só foi possível com tracked ≥ amb.
      if (
        pendingAmbiguousSyncRevisionRef.current != null &&
        next >= pendingAmbiguousSyncRevisionRef.current
      ) {
        pendingAmbiguousSyncRevisionRef.current = null;
      }
    },
    [playlistId, editorPresence?.clientId],
  );

  const slideBaseRevision = useCallback(
    (slideId?: string | null) =>
      // playlists.revision é global e monotônica — a entrada por slide é piso,
      // nunca override. Sem o max, um ack de escrita em outro slide/seção deixava
      // a base deste slide abaixo da revisão conhecida → self-409 → conflito
      // falso → reload revertia a edição local (TV-ICON-COLOR-REVERSION).
      // O head compartilhado cobre commits de contextos irmãos do mesmo
      // origin; writers externos seguem cobertos pelo CAS (409 real).
      Math.max(
        slideId ? (slideWriteBaseRevisionRef.current.get(slideId) ?? 0) : 0,
        knownPlaylistRevisionRef.current,
        readSharedPlaylistRevision(playlistId),
      ),
    [playlistId],
  );

  const playlistWriteGuard = useCallback(
    (): WriteGuard => {
      // Época capturada no gesto: se um conflito server-wins ocorrer antes do
      // envio na lane, a escrita é descartada em vez de sobrescrever o estado
      // recém-recarregado com snapshot pré-conflito.
      const epoch = comunicadoWriteEpochRef.current;
      return {
        // Thunk: resolvido no envio, após o ack da escrita anterior na lane
        // (e após commits de contextos irmãos via write head compartilhado).
        expectedRevision: () => slideBaseRevision(null),
        ifFresh: () => comunicadoWriteEpochRef.current === epoch,
        clientId: editorPresence?.clientId,
      };
    },
    [editorPresence?.clientId, slideBaseRevision],
  );

  // Ponte tardia: o freshness gate do slideWriteGuard aciona o cleanup
  // server-wins, definido abaixo — ref evita reordenar o componente.
  const applyServerWinsConflictRef = useRef<
    ((slideId?: string | null, message?: string) => Promise<void>) | null
  >(null);

  const slideWriteGuard = useCallback(
    (slideId?: string | null): WriteGuard => {
      const epoch = comunicadoWriteEpochRef.current;
      // Base de autoria capturada no gesto. Se um contexto irmão (outra
      // aba/janela same-origin) comitar neste slide depois da captura, o
      // snapshot é stale: obter o Web Lock NÃO torna conteúdo velho seguro —
      // rejeita localmente e aciona o cleanup server-wins canônico em vez de
      // enviar o full-config com revisão artificialmente atualizada.
      const capturedBase = slideBaseRevision(slideId);
      return {
        expectedRevision: () => slideBaseRevision(slideId),
        ifFresh: () => {
          if (comunicadoWriteEpochRef.current !== epoch) return false;
          if (
            slideId &&
            detectSharedSlideWrite(
              playlistId,
              slideId,
              capturedBase,
              editorPresence?.clientId,
            )
          ) {
            queueMicrotask(() => {
              void applyServerWinsConflictRef.current?.(slideId);
            });
            return false;
          }
          return true;
        },
        clientId: editorPresence?.clientId,
      };
    },
    [editorPresence?.clientId, playlistId, slideBaseRevision],
  );

  /** Guard resolvido no commit — mutations do provider atuam no slide ativo. */
  const resolveWriteGuard = useCallback(
    (): WriteGuard => slideWriteGuard(selectedSlideIdRef.current),
    [slideWriteGuard],
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
      const remoteRevision =
        pl.revision ?? pl.currentRevision ?? knownPlaylistRevisionRef.current;
      /*
       * Baseline externa = revisão remota acima do write-head compartilhado
       * (commits próprios e de contextos irmãos são publicados no ack).
       * `presentation_updated` não carrega clientId — a revisão é o único
       * discriminador confiável entre ack próprio e escrita estrangeira.
       */
      const foreignBaseline =
        remoteRevision > knownPlaylistRevisionRef.current &&
        remoteRevision > readSharedPlaylistRevision(playlistId);
      knownPlaylistRevisionRef.current = Math.max(
        knownPlaylistRevisionRef.current,
        remoteRevision,
      );
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
      for (const slide of merged.slides ?? []) {
        if (slide.nativeScreenKey !== "custom_message") continue;
        const draft = readComunicadoSlideDraft(playlistId, slide.id);
        if (draft && !draft.conflicted && typeof draft.baseRevision === "number") {
          slideWriteBaseRevisionRef.current.set(slide.id, draft.baseRevision);
        } else {
          slideWriteBaseRevisionRef.current.set(slide.id, remoteRevision);
        }
      }
      const dirty = hasLocalComunicadoEdits({
        playlistId,
        slideId: activeId,
        pendingSlideId: pending?.slide.id ?? null,
      });
      if (!dirty) {
        setRemoteConfigRevision((revision) => revision + 1);
        // Baseline estrangeira aceita no canvas — snapshots locais de undo
        // ficam stale (undo reaplicaria o slide inteiro pré-remoto sob CAS).
        if (foreignBaseline) {
          setForeignConfigRevision((revision) => revision + 1);
        }
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

  /**
   * Server-wins canônico: o estado remoto vence — marca o draft local como
   * conflitado (preservado para recuperação), descarta pending/debounce
   * obsoletos e recarrega o estado autoritativo.
   */
  const applyServerWinsConflict = useCallback(
    async (slideId?: string | null, message?: string) => {
      // Nova época: payloads capturados antes do conflito não podem mais
      // escrever — a lane descarta via `ifFresh` (server-wins).
      comunicadoWriteEpochRef.current += 1;
      if (slideId) {
        slideWriteBaseRevisionRef.current.delete(slideId);
        markComunicadoSlideDraftConflicted(playlistId, slideId);
        const pending = pendingComunicadoSaveRef.current;
        if (pending?.slide.id === slideId) pendingComunicadoSaveRef.current = null;
      }
      // O debounce de autosave não pode disparar payload pré-conflito após o reload.
      if (saveComunicadoTimerRef.current) {
        window.clearTimeout(saveComunicadoTimerRef.current);
        saveComunicadoTimerRef.current = null;
      }
      await reloadPlaylistFromServer();
      tvDashboardNotice(
        message ?? "A programação foi alterada por outro editor. Recarregue e tente de novo.",
      );
    },
    [playlistId, reloadPlaylistFromServer],
  );
  useEffect(() => {
    applyServerWinsConflictRef.current = applyServerWinsConflict;
  }, [applyServerWinsConflict]);

  /** 409 REVISION_CONFLICT canônico — delega ao cleanup server-wins. */
  const handlePlaylistWriteConflict = useCallback(
    async (error: unknown, slideId?: string | null): Promise<boolean> => {
      // Captura de época anterior já descartada pelo cleanup server-wins —
      // tratada como resolvida para silenciar todos os catch sites.
      if (error instanceof StaleWriteEpochError) return true;
      if (!isRevisionConflictError(error)) return false;
      const current = revisionConflictCurrentRevision(error);
      if (current != null) {
        knownPlaylistRevisionRef.current = Math.max(
          knownPlaylistRevisionRef.current,
          current,
        );
      }
      await applyServerWinsConflict(
        slideId,
        error instanceof Error ? error.message : undefined,
      );
      return true;
    },
    [applyServerWinsConflict],
  );

  const applyRemoteSlideDraft = useCallback(
    (
      slideId: string,
      nativeConfig: Record<string, unknown>,
      clientId: string,
      baseRevision?: number,
    ) => {
      if (clientId === editorPresence?.clientId) return;
      // Atividade de peer neste slide — mesmo quando o draft não é aplicado
      // (edições locais presentes). O CAS é por playlist: escritas capturadas
      // antes desta atividade não podem sobrescrever silenciosamente o slide.
      bumpSlidePeerActivity(slidePeerActivityRef.current, slideId);
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
      // Draft derivado de revisão mais antiga que a remota conhecida é obsoleto.
      const remoteKnown = Math.max(
        knownPlaylistRevisionRef.current,
        playlistRef.current?.revision ?? playlistRef.current?.currentRevision ?? 0,
      );
      if (typeof baseRevision === "number" && baseRevision < remoteKnown) return;

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
      // O estado local agora espelha o draft do peer — base de escrita segue-o,
      // mas nunca regride abaixo do que os nossos próprios acks já confirmaram.
      const trackedBase = slideWriteBaseRevisionRef.current.get(slideId) ?? 0;
      slideWriteBaseRevisionRef.current.set(
        slideId,
        Math.max(trackedBase, baseRevision ?? remoteKnown),
      );
      setRemoteConfigRevision((revision) => revision + 1);
      // Draft de peer já passou pelo filtro de clientId próprio — baseline
      // externa por definição; invalida undo/redo local como write remoto.
      setForeignConfigRevision((revision) => revision + 1);
    },
    [editorPresence?.clientId, playlistId],
  );

  const handleMutationCommitted = useCallback(
    (meta: MutationCommitMeta) => {
      recordWriteRevision(meta.playlistRevision, selectedSlideIdRef.current);
    },
    [recordWriteRevision],
  );

  /**
   * 025-R1 — falha não-CAS de mutation (rede/5xx/timeout/cancelamento): a
   * projeção local não está confirmada. A recuperação é o reload
   * autoritativo — timeout/ACK perdido podem significar commit efetivado,
   * então o servidor decide. Só executa quando a lane drenar para não
   * reverter escritas irmãs ainda em voo. Guarda o slide que falhou: se o
   * usuário navegar antes do dreno, a marca de conflito segue o slide certo.
   */
  const pendingMutationRecoveryRef = useRef<string | null>(null);
  const recoverMutationAfterFailure = useCallback(() => {
    const failedSlideId = pendingMutationRecoveryRef.current;
    if (!failedSlideId) return;
    if (hasPendingPlaylistWrite(playlistId)) return;
    pendingMutationRecoveryRef.current = null;
    void applyServerWinsConflict(
      failedSlideId,
      "Não foi possível confirmar a alteração. O estado salvo foi restaurado.",
    );
  }, [playlistId, applyServerWinsConflict]);

  const handleMutationWriteError = useCallback(
    (error: unknown) => {
      const slideId = selectedSlideIdRef.current;
      void handlePlaylistWriteConflict(error, slideId).then((handled) => {
        if (handled) return;
        pendingMutationRecoveryRef.current = slideId;
        recoverMutationAfterFailure();
      });
    },
    [handlePlaylistWriteConflict, recoverMutationAfterFailure],
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
    onConnected: () => {
      // Re-publish editorFocus after WS reconnect (API recreate wipes in-memory store).
      flushEditorFocusRef.current?.();
    },
    onPresenceUpdate: handlePresenceUpdate,
    onSync: (event) => {
      // Sync canônico (WS presentation_updated) — inclui mutações do copiloto via CRUD.
      // Commit de peer num slide específico marca atividade — autosaves locais
      // capturados antes não podem sobrescrever silenciosamente esse slide.
      if (
        event?.clientId &&
        event.clientId !== editorPresence?.clientId &&
        event.slideId
      ) {
        bumpSlidePeerActivity(slidePeerActivityRef.current, event.slideId);
      }
      // VISTA-TV-024/024-R1 — dispensa reload quando a revisão do evento já
      // está incorporada (ACK próprio, contexto irmão via write-head). Rev
      // == tracked+1 com escrita em voo é ambígua: não é prova de autoria —
      // é registrada e reconciliada obrigatoriamente no settle da lane
      // (fulfilled+ack cobre → incorporado; rejeitada sem cobertura →
      // reload, a remota nunca fica permanentemente ignorada).
      // Evento sem revisão (payload antigo, reconexão) → sempre reload.
      const eventPlaylistRevision =
        typeof event?.playlistRevision === "number" &&
        Number.isFinite(event.playlistRevision)
          ? event.playlistRevision
          : null;
      const syncDecision = resolvePresentationSyncReloadDecision({
        eventRevision: eventPlaylistRevision,
        trackedRevision: slideBaseRevision(null),
        hasPendingOwnWrite: hasPendingPlaylistWrite(playlistId),
      });
      if (syncDecision === "skip_ambiguous_pending") {
        pendingAmbiguousSyncRevisionRef.current = Math.max(
          pendingAmbiguousSyncRevisionRef.current ?? 0,
          eventPlaylistRevision ?? 0,
        );
        return;
      }
      if (syncDecision === "skip_incorporated") {
        return;
      }
      // Foco só em criação/import/duplicação — nunca em slide_updated (autosave do peer).
      void reloadPlaylistFromServer({
        focusSlideId: resolvePresentationSyncFocusSlideId(event, {
          currentSlideId: selectedSlideIdRef.current,
        }),
      }).then(() => deckHistory.handleRemoteUpdate());
    },
    onSlideDraft: (event) => {
      applyRemoteSlideDraft(
        event.slideId,
        event.nativeConfig,
        event.clientId,
        event.baseRevision,
      );
    },
    onSelectionUpdate: handleRemoteSelection,
    onVisualCaptureRequest: (event: PresentationVisualCaptureRequestEvent) => {
      // VISTA live-editor visual verification: captura SOMENTE o palco visível
      // atual — nunca troca de slide, nunca renderiza em background.
      void handleVisualCaptureRequest(event, {
        playlistId,
        getSelectedSlideId: () => selectedSlideIdRef.current,
        getLocalRevision: () => {
          const current = playlistRef.current;
          const revision = current?.revision ?? current?.currentRevision;
          return typeof revision === "number" && Number.isFinite(revision)
            ? revision
            : null;
        },
        reloadFromServer: () => reloadPlaylistFromServer(),
        isEditorActive: () => editorActive,
        getClientId: () => editorPresence?.clientId,
        hasPendingLocalEdits: () => {
          const pending = pendingComunicadoSaveRef.current;
          return (
            Boolean(pending) ||
            hasLocalComunicadoEdits({
              playlistId,
              slideId: selectedSlideIdRef.current,
              pendingSlideId: pending?.slide.id ?? null,
            })
          );
        },
      });
    },
  });

  // 024-R1 — reconciliação diferida de evento ambíguo: avaliada um microtask
  // após o settle para o processamento do ACK (`recordWriteRevision`)
  // publicar o write-head primeiro; se a revisão ambígua continuar acima do
  // rastreado (escrita rejeitada/timeout/cancelada ou ack que não a cobriu),
  // a atualização remota é recuperada com reload obrigatório.
  useEffect(
    () =>
      onPlaylistWriteSettled(playlistId, () => {
        queueMicrotask(() => {
          const ambiguousRevision = pendingAmbiguousSyncRevisionRef.current;
          pendingAmbiguousSyncRevisionRef.current = null;
          if (
            shouldRecoverAmbiguousSyncEvent({
              ambiguousRevision,
              trackedRevision: slideBaseRevision(null),
            })
          ) {
            // O reload autoritativo abaixo já reconcilia falhas pendentes.
            pendingMutationRecoveryRef.current = null;
            void reloadPlaylistFromServer().then(() =>
              deckHistory.handleRemoteUpdate(),
            );
            return;
          }
          // 025-R1 — drena recuperação de falha não-CAS quando a lane esvaziou.
          recoverMutationAfterFailure();
        });
      }),
    [
      playlistId,
      slideBaseRevision,
      reloadPlaylistFromServer,
      deckHistory,
      recoverMutationAfterFailure,
    ],
  );

  /**
   * Última seleção de blocos do canvas (ComunicadoEditorProvider.onSelectionChange).
   * Heartbeat/reconnect devem reenviar ISTO — nunca `selectedSlideIds` do filmstrip
   * (IDs de slide ≠ blockId; filtrar o slideId atual deixa selectedIds=[] e a VISTA
   * perde «o bloco selecionado»).
   */
  const canvasSelectedIdsRef = useRef<string[]>([]);

  const sendSelectionUpdate = useCallback(
    (slideId: string, selectedIds: string[]) => {
      canvasSelectedIdsRef.current = normalizeEditorFocusBlockIds(selectedIds);
      const clientId = editorPresence?.clientId;
      if (!clientId) return;
      wsSendRef.current?.({
        type: "selection_update",
        slideId,
        clientId,
        selectedIds: canvasSelectedIdsRef.current,
      });
    },
    [editorPresence?.clientId, wsSendRef],
  );

  const sendSelectionUpdateRef = useRef(sendSelectionUpdate);
  sendSelectionUpdateRef.current = sendSelectionUpdate;

  const flushEditorFocus = useCallback(() => {
    const slideId = selectedSlideIdRef.current;
    if (!slideId || !editorPresence?.clientId) return;
    sendSelectionUpdateRef.current(slideId, canvasSelectedIdsRef.current);
  }, [editorPresence?.clientId]);

  const flushEditorFocusRef = useRef(flushEditorFocus);
  flushEditorFocusRef.current = flushEditorFocus;

  // Troca de slide: limpa seleção de bloco até o provider publicar a nova.
  useEffect(() => {
    canvasSelectedIdsRef.current = [];
  }, [selectedSlideId]);

  // Keep editorFocus snapshot warm for VISTA even when selection is empty (slide-only).
  useEffect(() => {
    if (!editorActive || !selectedSlideId) return;
    flushEditorFocus();
  }, [editorActive, selectedSlideId, flushEditorFocus]);

  // Retry when WS presence/clientId arrives after the first paint (common after API recreate).
  useEffect(() => {
    if (!editorActive || !selectedSlideId || !editorPresence?.clientId) return;
    flushEditorFocus();
  }, [editorActive, selectedSlideId, editorPresence?.clientId, flushEditorFocus]);

  useEffect(() => {
    if (!editorActive || !selectedSlideId) return;
    const intervalId = window.setInterval(() => {
      flushEditorFocus();
    }, 30_000);
    return () => window.clearInterval(intervalId);
  }, [editorActive, selectedSlideId, flushEditorFocus]);

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
      const remoteRevision =
        pl.revision ?? pl.currentRevision ?? knownPlaylistRevisionRef.current;
      knownPlaylistRevisionRef.current = remoteRevision;
      const merged = mergePlaylistSlidesWithComunicadoDrafts(playlistId, pl);
      setPlaylist(merged);
      writePlaylistShell(merged);
      // Base OCC por slide: draft aplicável deriva de sua própria baseRevision;
      // slide limpo deriva da revisão remota.
      for (const slide of merged.slides ?? []) {
        if (slide.nativeScreenKey !== "custom_message") continue;
        const draft = readComunicadoSlideDraft(playlistId, slide.id);
        const base =
          draft && !draft.conflicted && typeof draft.baseRevision === "number"
            ? draft.baseRevision
            : remoteRevision;
        slideWriteBaseRevisionRef.current.set(slide.id, base);
      }
      // Reenvia à API drafts locais ainda não confirmados (ex.: F5 no meio do debounce).
      // Nunca limpar draft sem guarda de versão — save antigo não pode apagar edição nova.
      for (const slide of merged.slides ?? []) {
        if (slide.nativeScreenKey !== "custom_message") continue;
        const draft = readComunicadoSlideDraft(playlistId, slide.id);
        if (!draft) continue;
        // Draft obsoleto/conflitado nunca reescreve o estado remoto automaticamente.
        if (!isComunicadoDraftApplicable(draft, remoteRevision)) continue;
        const draftVersion = draft.version;
        // Revisão resolvida no envio: escritas irmãs não podem gerar self-409;
        // floor por slide ainda protege contra draft de peer no mesmo slide.
        const replayEpoch = comunicadoWriteEpochRef.current;
        const replayGuard: WriteGuard = {
          ...slideWriteGuard(slide.id),
          ifFresh: () => comunicadoWriteEpochRef.current === replayEpoch,
          clientId: editorPresence?.clientId,
        };
        void updateSlide(
          playlistId,
          slide.id,
          {
            title: slide.title,
            durationSec: slide.durationSec ?? null,
            nativeConfig: draft.nativeConfig,
          },
          replayGuard,
        )
          .then((updated) => {
            recordWriteRevision(
              updated.playlistRevision,
              slide.id,
              replayGuard.expectedRevision,
            );
            clearComunicadoSlideDraftIfCoveredBySave(playlistId, slide.id, draftVersion);
          })
          .catch((caught) => {
            if (caught instanceof StaleWriteEpochError) return;
            void handlePlaylistWriteConflict(caught, slide.id);
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
    const saveGen = ++playlistSettingsSaveGenRef.current;
    // Otimista: evita salto no RangeField enquanto o PATCH não volta.
    if (field === "dataDefaults" && value && typeof value === "object") {
      setPlaylist({ ...playlist, dataDefaults: value as Record<string, unknown> });
    } else if (field === "viewport" && value && typeof value === "object") {
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
    } else if (typeof value === "number" || typeof value === "string") {
      setPlaylist({ ...playlist, [field]: value } as Playlist);
    }
    try {
      const body =
        field === "viewport" && value && typeof value === "object"
          ? (value as Parameters<typeof updatePlaylist>[1])
          : ({ [field]: value } as Parameters<typeof updatePlaylist>[1]);
      const guard = playlistWriteGuard();
      const updated = await updatePlaylist(playlist.id, body, guard);
      recordWriteRevision(
        updated.playlistRevision ?? updated.revision,
        null,
        guard.expectedRevision,
      );
      if (saveGen !== playlistSettingsSaveGenRef.current) return;
      setPlaylist({ ...updated, slides: previousPlaylist.slides });
      await deckHistory.confirmChange();
    } catch (caught) {
      if (saveGen === playlistSettingsSaveGenRef.current) {
        setPlaylist(previousPlaylist);
      }
      deckHistory.cancelChange();
      if (await handlePlaylistWriteConflict(caught)) return;
      throw caught;
    }
  }

  function formatExportNotice(template: string, values: Record<string, string | number>): string {
    return Object.entries(values).reduce(
      (text, [key, value]) => text.replace(`{${key}}`, String(value)),
      template,
    );
  }

  async function handleExportPng() {
    if (!playlist) return;
    const targets = resolveExportSlideTargets({
      scope: "selected",
      slides,
      selectedSlides,
      primary: selectedSlide,
    });
    if (targets.length === 0) return;
    const liveTarget = resolveSlideExportTarget(document.querySelector(".td-deck-stage__main"));
    const onlyPrimary =
      targets.length === 1 && selectedSlide && targets[0]?.id === selectedSlide.id;
    if (onlyPrimary) {
      if (!liveTarget) {
        tvDashboardNotice("Não foi possível localizar o palco para exportar.");
        return;
      }
      setExportBusy(true);
      try {
        await exportSlideElementToPng(liveTarget, {
          fileName: uniqueExportFileName(selectedSlide.title, new Set(), "png"),
        });
      } catch (err) {
        tvDashboardNotice(err instanceof Error ? err.message : "Falha ao exportar PNG.");
      } finally {
        setExportBusy(false);
      }
      return;
    }

    const designSize = resolvePlaylistDesignSize(playlist);
    setExportBusy(true);
    try {
      const used = new Set<string>();
      const pages: Array<{ dataUrl: string; fileName: string }> = [];
      let skipped = 0;
      for (const slide of targets) {
        if (slide.slideType === "external") {
          skipped += 1;
          continue;
        }
        if (slide.id === selectedSlide?.id && liveTarget) {
          pages.push({
            dataUrl: await captureSlideElementToPngDataUrl(liveTarget),
            fileName: uniqueExportFileName(slide.title, used, "png"),
          });
          continue;
        }
        const native = buildSlideThumbnailNative(
          slide,
          playlist.id,
          previewBySlideId[slide.id],
          playlist.masterConfig,
          playlist.publicToken,
        );
        if (!native) {
          skipped += 1;
          continue;
        }
        pages.push({
          dataUrl: await captureOffscreenNativeToPngDataUrl(native, designSize),
          fileName: uniqueExportFileName(slide.title, used, "png"),
        });
      }
      if (pages.length === 0) {
        tvDashboardNotice("Nenhuma tela exportável (nativa) encontrada.");
        return;
      }
      await downloadPngDataUrls(pages);
      if (skipped > 0) {
        tvDashboardNotice(
          formatExportNotice(TV_DASHBOARD_HELP_TOOLTIPS.ribbon.exportSkipped, {
            exported: pages.length,
            skipped,
          }),
        );
      }
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
    scope: "playlist" | "current" | "selected";
    pixelRatio: 1 | 2;
  }) {
    if (!playlist) return;
    const designSize = resolvePlaylistDesignSize(playlist);
    const safePlaylist = playlist.name.replace(/[^\w\-]+/g, "_").slice(0, 40) || "programacao";
    setExportBusy(true);
    setExportPdfProgress(options.scope === "current" ? "Capturando slide…" : "Preparando…");
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
        await exportSlideElementToPdf(target, {
          fileName: uniqueExportFileName(selectedSlide.title, new Set(), "pdf"),
          pixelRatio: options.pixelRatio,
          designSize,
        });
      } else {
        const targets =
          options.scope === "selected"
            ? resolveExportSlideTargets({
                scope: "selected",
                slides,
                selectedSlides,
                primary: selectedSlide,
              })
            : slides;
        const result =
          options.scope === "selected"
            ? await exportSlidesToPdf(targets, {
                playlistId: playlist.id,
                designSize,
                previewBySlideId,
                masterConfig: playlist.masterConfig,
                publicToken: playlist.publicToken,
                pixelRatio: options.pixelRatio,
                fileName: `${safePlaylist}-selecao.pdf`,
                onProgress: ({ current, total, slideTitle }) => {
                  setExportPdfProgress(
                    `Capturando ${current}/${total}${slideTitle ? ` · ${slideTitle}` : ""}`,
                  );
                },
              })
            : await exportActivePlaylistSlidesToPdf({
                playlistId: playlist.id,
                slides: targets,
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
            formatExportNotice(TV_DASHBOARD_HELP_TOOLTIPS.ribbon.exportSkipped, {
              exported: result.pageCount,
              skipped: result.skipped,
            }),
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
    if (!playlist) return;
    const { targets, skipped } = resolveExportPptxTargets(
      selectedSlides,
      selectedSlide,
      slides,
    );
    if (targets.length === 0) {
      tvDashboardNotice(TV_DASHBOARD_HELP_TOOLTIPS.ribbon.exportPptxCustomOnly);
      return;
    }
    setExportBusy(true);
    try {
      const configs = targets.map((slide) => {
        const raw =
          slide.id === selectedSlide?.id
            ? (liveComunicadoConfigRef.current ?? slide.nativeConfig ?? {})
            : (slide.nativeConfig ?? {});
        return enrichComunicadoConfigForEditor(raw, playlistId);
      });
      const fileName =
        targets.length === 1
          ? uniqueExportFileName(targets[0]?.title ?? "slide", new Set(), "pptx")
          : uniqueExportFileName(playlist.name, new Set(), "pptx");
      await exportSlidesPptx(configs, fileName);
      if (skipped > 0) {
        tvDashboardNotice(
          formatExportNotice(TV_DASHBOARD_HELP_TOOLTIPS.ribbon.exportPptxSkipped, { skipped }),
        );
      }
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
    const guard = playlistWriteGuard();
    const result = await reorderSlides(playlist.id, items, guard);
    recordWriteRevision(result.playlistRevision, null, guard.expectedRevision);
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
          const guard = playlistWriteGuard();
          const expanded = await updatePlaylistSection(
            playlist.id,
            explicitSectionId,
            { isCollapsed: false },
            guard,
          );
          recordWriteRevision(expanded.playlistRevision, null, guard.expectedRevision);
        }
      }
      const slideGuard = playlistWriteGuard();
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
      }, slideGuard);
      recordWriteRevision(slide.playlistRevision, null, slideGuard.expectedRevision);
      let placed = slide;
      if (explicitSectionId) {
        const ordered = assignSlideToSectionOrder(
          [...(playlist.slides ?? []), slide],
          slide.id,
          explicitSectionId,
        );
        const items = ordered.map((item, sortOrder) => ({ id: item.id, sortOrder }));
        const reorderGuard = playlistWriteGuard();
        const result = await reorderSlides(playlist.id, items, reorderGuard);
        recordWriteRevision(result.playlistRevision, null, reorderGuard.expectedRevision);
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
      if (await handlePlaylistWriteConflict(caught)) return;
      throw caught;
    }
  }

  async function handleAddSection(explicitAnchorId?: string | null) {
    if (!playlist) return;
    deckHistory.recordBeforeChange();
    try {
      const ensureGuard = playlistWriteGuard();
      const main = await ensurePlaylistMainSection(playlist.id, ensureGuard);
      recordWriteRevision(main.playlistRevision, null, ensureGuard.expectedRevision);
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
        const createGuard = playlistWriteGuard();
        const section = await createPlaylistSection(playlist.id, {
          name: `Seção ${userCount + 1}`,
          sortOrder: maxOrder + 1,
          isCollapsed: false,
        }, createGuard);
        recordWriteRevision(section.playlistRevision, null, createGuard.expectedRevision);
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
      const createGuard = playlistWriteGuard();
      const section = await createPlaylistSection(playlist.id, {
        name: `Seção ${userCount + 1}`,
        sortOrder: maxOrder + 1,
        isCollapsed: false,
      }, createGuard);
      recordWriteRevision(section.playlistRevision, null, createGuard.expectedRevision);

      const baseOrder = workingSections.filter((s) => s.id !== section.id);
      const afterIdx = baseOrder.findIndex((s) => s.id === afterSectionId);
      const insertAt = afterIdx >= 0 ? afterIdx + 1 : 1;
      const orderedSections = [...baseOrder];
      orderedSections.splice(insertAt, 0, section);
      const reorderItems = orderedSections.map((item, sortOrder) => ({
        id: item.id,
        sortOrder,
      }));
      const sectionReorderGuard = playlistWriteGuard();
      const reordered = await reorderPlaylistSections(
        playlist.id,
        reorderItems,
        sectionReorderGuard,
      );
      workingSections = reordered.items;
      recordWriteRevision(
        reordered.playlistRevision,
        null,
        sectionReorderGuard.expectedRevision,
      );

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
        const guard = playlistWriteGuard();
        const claimed = await updateSlide(
          playlist.id,
          update.id,
          { sectionId: update.sectionId },
          guard,
        );
        recordWriteRevision(claimed.playlistRevision, null, guard.expectedRevision);
      }

      const items = localSlides
        .slice()
        .sort((a, b) => a.sortOrder - b.sortOrder)
        .map((item, sortOrder) => ({ id: item.id, sortOrder }));
      const reorderGuard = playlistWriteGuard();
      const result = await reorderSlides(playlist.id, items, reorderGuard);
      recordWriteRevision(result.playlistRevision, null, reorderGuard.expectedRevision);
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
          const guard = playlistWriteGuard();
          const expanded = await updatePlaylistSection(
            playlist.id,
            sectionId,
            { isCollapsed: false },
            guard,
          );
          recordWriteRevision(expanded.playlistRevision, null, guard.expectedRevision);
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
      if (await handlePlaylistWriteConflict(caught)) return;
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
      const guard = playlistWriteGuard();
      const moved = await updateSlide(
        playlist.id,
        update.id,
        { sectionId: update.sectionId },
        guard,
      );
      recordWriteRevision(moved.playlistRevision, null, guard.expectedRevision);
    }
    const items = nextSlides.map((item, sortOrder) => ({ id: item.id, sortOrder }));
    const reorderGuard = playlistWriteGuard();
    const result = await reorderSlides(playlist.id, items, reorderGuard);
    recordWriteRevision(result.playlistRevision, null, reorderGuard.expectedRevision);
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
      const ensureGuard = playlistWriteGuard();
      const main =
        sections.find((section) => section.isMain) ??
        (await ensurePlaylistMainSection(playlist.id, ensureGuard));
      recordWriteRevision(main.playlistRevision, null, ensureGuard.expectedRevision);
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
        const guard = playlistWriteGuard();
        const expanded = await updatePlaylistSection(
          playlist.id,
          targetSectionId,
          { isCollapsed: false },
          guard,
        );
        recordWriteRevision(expanded.playlistRevision, null, guard.expectedRevision);
      }
      await persistFilmstripRelocation(ordered, { expandSectionId: targetSectionId });
      endFilmstripDrag();
      await deckHistory.confirmChange();
    } catch (caught) {
      deckHistory.cancelChange();
      if (await handlePlaylistWriteConflict(caught)) return;
      throw caught;
    }
  }

  async function patchSection(sectionId: string, patch: Partial<PlaylistSection>) {
    if (!playlist) return;
    deckHistory.recordBeforeChange();
    try {
      const guard = playlistWriteGuard();
      const updated = await updatePlaylistSection(playlist.id, sectionId, {
        name: patch.name,
        sortOrder: patch.sortOrder,
        isCollapsed: patch.isCollapsed,
        isActive: patch.isActive,
        defaultDurationSec: patch.defaultDurationSec,
        transitionStyle: patch.transitionStyle,
        masterConfig: patch.masterConfig,
      }, guard);
      recordWriteRevision(updated.playlistRevision, null, guard.expectedRevision);
      setPlaylist({
        ...playlist,
        sections: (playlist.sections ?? []).map((item) =>
          item.id === sectionId ? updated : item,
        ),
      });
      await deckHistory.confirmChange();
    } catch (caught) {
      deckHistory.cancelChange();
      if (await handlePlaylistWriteConflict(caught)) return;
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
      const guard = playlistWriteGuard();
      await deletePlaylistSection(playlist.id, sectionId, {
        deleteSlides,
        expectedRevision: guard.expectedRevision,
      });
      recordWriteRevision(null, null, guard.expectedRevision);
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
      if (await handlePlaylistWriteConflict(caught)) return;
      throw caught;
    }
  }

  async function handleRenameSlide(slide: Slide, nextTitle: string) {
    if (!playlist) return;
    const title = nextTitle.trim();
    if (!title || title === slide.title) return;
    deckHistory.recordBeforeChange();
    try {
      const guard = slideWriteGuard(slide.id);
      const updated = await updateSlide(playlist.id, slide.id, { title }, guard);
      recordWriteRevision(updated.playlistRevision, slide.id, guard.expectedRevision);
      setPlaylist({
        ...playlist,
        slides: (playlist.slides ?? []).map((item) => (item.id === slide.id ? updated : item)),
      });
      await deckHistory.confirmChange();
    } catch (caught) {
      deckHistory.cancelChange();
      if (await handlePlaylistWriteConflict(caught, slide.id)) return;
      throw caught;
    }
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
        const guard = playlistWriteGuard();
        await deleteSlide(playlist.id, slide.id, guard);
        recordWriteRevision(null, null, guard.expectedRevision);
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
      if (await handlePlaylistWriteConflict(caught)) return;
      throw caught;
    }
  }

  async function handleToggleActive() {
    if (!playlist) return;
    try {
      const guard = playlistWriteGuard();
      const updated = playlist.isActive
        ? await deactivatePlaylist(playlist.id, guard)
        : await activatePlaylist(playlist.id, guard);
      recordWriteRevision(
        updated.playlistRevision ?? updated.revision,
        null,
        guard.expectedRevision,
      );
      setPlaylist({ ...updated, slides: playlist.slides });
    } catch (caught) {
      if (await handlePlaylistWriteConflict(caught)) return;
      throw caught;
    }
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
    options?: {
      recordHistory?: boolean;
      autosaveVersion?: number;
      epoch?: number;
      peerTick?: number;
    },
  ) {
    if (!playlist) return;
    if (options?.recordHistory) deckHistory.recordBeforeChange();
    try {
      const callEpoch = options?.epoch ?? comunicadoWriteEpochRef.current;
      const peerTick =
        options?.peerTick ?? slidePeerActivityRef.current.get(slide.id) ?? 0;
      const capturedBase = slideBaseRevision(slide.id);
      const guard: WriteGuard = {
        ...slideWriteGuard(slide.id),
        ifFresh: () => {
          if (comunicadoWriteEpochRef.current !== callEpoch) return false;
          if (
            slidePeerActivityAdvanced(slidePeerActivityRef.current, slide.id, peerTick) ||
            detectSharedSlideWrite(
              playlistId,
              slide.id,
              capturedBase,
              editorPresence?.clientId,
            )
          ) {
            // Peer ou contexto irmão tocou o mesmo slide após a captura —
            // CAS por playlist não geraria 409; tratar como conflito server-wins.
            queueMicrotask(() => void applyServerWinsConflict(slide.id));
            return false;
          }
          return true;
        },
      };
      const updated = await updateSlide(playlist.id, slide.id, payload, guard);
      recordWriteRevision(updated.playlistRevision, slide.id, guard.expectedRevision);
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
      // 409: conflito já tratado (reload + notice) — não propagar como falha genérica.
      if (await handlePlaylistWriteConflict(caught, slide.id)) return;
      throw caught;
    }
  }

  async function persistSharedCustomFanOut(
    source: Slide,
    nextConfig: Record<string, unknown>,
  ) {
    const pl = playlistRef.current;
    if (!pl) return;
    const baseline =
      customFanOutBaselineRef.current?.slideId === source.id
        ? customFanOutBaselineRef.current.nativeConfig
        : source.nativeConfig;
    const slice = pickSharedCustomSlideConfig(nextConfig, baseline);
    if (!slice) return;
    const others = selectedSlidesRef.current.filter(
      (item) => item.id !== source.id && isCustomMessageSlide(item),
    );
    if (others.length === 0) return;
    const { applied } = applySlideBatchPatch(others, { nativeConfig: slice });
    if (applied.length === 0) return;
    const updates = new Map<string, Slide>();
    for (const item of applied) {
      const guard = slideWriteGuard(item.slideId);
      try {
        const updated = await updateSlide(pl.id, item.slideId, item.payload, guard);
        recordWriteRevision(updated.playlistRevision, item.slideId, guard.expectedRevision);
        updates.set(item.slideId, updated);
      } catch (caught) {
        if (await handlePlaylistWriteConflict(caught, item.slideId)) return;
        throw caught;
      }
    }
    setPlaylist((current) => {
      if (!current) return current;
      return {
        ...current,
        slides: (current.slides ?? []).map((item) => updates.get(item.id) ?? item),
      };
    });
  }

  async function handleSaveSlides(targets: Slide[], patch: SlideBatchInput) {
    if (!playlist || targets.length === 0) return;
    const { applied } = applySlideBatchPatch(targets, patch);
    if (applied.length === 0) return;
    deckHistory.recordBeforeChange();
    try {
      const updates = new Map<string, Slide>();
      for (const item of applied) {
        const guard = slideWriteGuard(item.slideId);
        try {
          const updated = await updateSlide(playlist.id, item.slideId, item.payload, guard);
          recordWriteRevision(updated.playlistRevision, item.slideId, guard.expectedRevision);
          updates.set(item.slideId, updated);
        } catch (caught) {
          if (await handlePlaylistWriteConflict(caught, item.slideId)) return;
          throw caught;
        }
      }
      setPlaylist((current) => {
        if (!current) return current;
        return {
          ...current,
          slides: (current.slides ?? []).map((item) => updates.get(item.id) ?? item),
        };
      });
      await deckHistory.confirmChange();
      if (applied.length > 1) {
        tvDashboardNotice(
          TV_DASHBOARD_HELP_TOOLTIPS.ribbon.slideBatchSaved.replace(
            "{count}",
            String(applied.length),
          ),
        );
      }
    } catch (caught) {
      deckHistory.cancelChange();
      throw caught;
    }
  }

  const persistComunicadoPending = useCallback(
    async (
      captured: {
        slide: Slide;
        nativeConfig: Record<string, unknown>;
        version: number;
        baseRevision?: number | null;
        epoch?: number;
        peerTick?: number;
      },
      options?: { keepalive?: boolean },
    ) => {
      const pl = playlistRef.current;
      if (!pl) return;
      try {
        // Revisão fresca no envio (conteúdo é snapshot cumulativo do local); a
        // guarda de época descarta capturas anteriores a um conflito server-wins.
        const expectedRevision = () => slideBaseRevision(captured.slide.id);
        const epoch = captured.epoch ?? comunicadoWriteEpochRef.current;
        const peerTick =
          captured.peerTick ??
          slidePeerActivityRef.current.get(captured.slide.id) ??
          0;
        const updated = await updateSlide(
          pl.id,
          captured.slide.id,
          {
            title: captured.slide.title,
            durationSec: captured.slide.durationSec ?? null,
            nativeConfig: captured.nativeConfig,
          },
          {
            keepalive: options?.keepalive,
            expectedRevision,
            ifFresh: () => {
              if (comunicadoWriteEpochRef.current !== epoch) return false;
              if (
                slidePeerActivityAdvanced(
                  slidePeerActivityRef.current,
                  captured.slide.id,
                  peerTick,
                )
              ) {
                // Peer tocou o mesmo slide após a captura — CAS por playlist não
                // geraria 409; tratar como conflito server-wins.
                queueMicrotask(() =>
                  void applyServerWinsConflict(captured.slide.id),
                );
                return false;
              }
              return true;
            },
            clientId: editorPresence?.clientId,
          },
        );
        recordWriteRevision(updated.playlistRevision, captured.slide.id, expectedRevision);
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
        // Captura de época anterior ao último conflito — descarte silencioso,
        // o reload server-wins já aplicou o estado autoritativo.
        if (caught instanceof StaleWriteEpochError) return;
        // Conflito de revisão: servidor vence — draft vira conflicted e o
        // estado remoto é recarregado; pending obsoleto não é reenfileirado.
        if (await handlePlaylistWriteConflict(caught, captured.slide.id)) return;
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
    [
      applyServerWinsConflict,
      deckHistory.cancelChange,
      deckHistory.confirmChange,
      editorPresence?.clientId,
      handlePlaylistWriteConflict,
      recordWriteRevision,
      slideBaseRevision,
    ],
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
      await persistSharedCustomFanOut(pending.slide, pending.nativeConfig);
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
      void persistSharedCustomFanOut(previous.slide, previous.nativeConfig);
      customFanOutBaselineRef.current = null;
    }
    if (!previous || previous.slide.id !== slide.id) {
      customFanOutBaselineRef.current = {
        slideId: slide.id,
        nativeConfig: { ...(slide.nativeConfig ?? {}) },
      };
    }

    liveComunicadoConfigRef.current = nativeConfig;
    const version = bumpComunicadoAutosaveVersion(comunicadoAutosaveVersionRef.current, slide.id);
    const baseRevision = slideBaseRevision(slide.id);
    writeComunicadoSlideDraft(playlistId, slide.id, nativeConfig, Date.now(), version, {
      baseRevision,
    });
    const captureEpoch = comunicadoWriteEpochRef.current;
    const peerTick = slidePeerActivityRef.current.get(slide.id) ?? 0;
    pendingComunicadoSaveRef.current = {
      slide,
      nativeConfig,
      version,
      baseRevision,
      epoch: captureEpoch,
      peerTick,
    };
    const sharedSlice = pickSharedCustomSlideConfig(
      nativeConfig,
      customFanOutBaselineRef.current?.nativeConfig,
    );
    const fanOutIds = new Set(
      selectedSlidesRef.current
        .filter((item) => item.id !== slide.id && isCustomMessageSlide(item))
        .map((item) => item.id),
    );
    // Otimista: atualiza nativeConfig no estado já — o save API continua debounced.
    // Sem isso, re-renders (WS/thumbnails) reaplicam o config antigo no editor mid-drag.
    setPlaylist((current) => {
      if (!current) return current;
      return {
        ...current,
        slides: (current.slides ?? []).map((item) => {
          if (item.id === slide.id) return { ...item, nativeConfig };
          if (sharedSlice && fanOutIds.has(item.id)) {
            return { ...item, nativeConfig: { ...(item.nativeConfig ?? {}), ...sharedSlice } };
          }
          return item;
        }),
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
        { autosaveVersion: version, epoch: captureEpoch, peerTick },
      ).catch((caught) => {
        if (caught instanceof StaleWriteEpochError) return;
        tvDashboardNotice(
          caught instanceof Error
            ? caught.message
            : "Falha ao salvar o slide. Suas alterações ficaram guardadas localmente.",
        );
      });
      void persistSharedCustomFanOut(slide, nativeConfig);
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
        baseRevision,
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
        const guard = playlistWriteGuard();
        const copy = await duplicateSlide(playlist.id, slide.id, guard);
        recordWriteRevision(copy.playlistRevision, null, guard.expectedRevision);
        const placed = await placeSlideAfterActive(copy, lastPlaced?.id ?? slide.id);
        lastPlaced = placed;
      }
      if (lastPlaced) selectSlide(lastPlaced.id, lastPlaced);
      await deckHistory.confirmChange();
      if (unique.length > 1) {
        tvDashboardNotice(
          TV_DASHBOARD_HELP_TOOLTIPS.ribbon.slideBatchDuplicated.replace(
            "{count}",
            String(unique.length),
          ),
        );
      }
    } catch (caught) {
      deckHistory.cancelChange();
      if (await handlePlaylistWriteConflict(caught)) return;
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
      const guard = playlistWriteGuard();
      const slide = await addSlide(playlist.id, {
        ...payload,
        title: pasteTitleFromClipboard(payload),
        nativeScreenKey: payload.nativeScreenKey ?? undefined,
        nativeConfig: payload.nativeConfig ?? undefined,
        externalUrl: payload.externalUrl ?? undefined,
        sectionId: anchorSectionId,
      }, guard);
      recordWriteRevision(slide.playlistRevision, null, guard.expectedRevision);
      const placed = await placeSlideAfterActive(slide, anchorId);
      selectSlide(placed.id, placed);
      await deckHistory.confirmChange();
    } catch (caught) {
      deckHistory.cancelChange();
      if (await handlePlaylistWriteConflict(caught)) return;
      throw caught;
    }
  }

  const canPasteSlide = slideClipboardRef.current != null;
  void slideClipboardRevision;

  async function handleToggleSlidesActive(targets: Slide[]) {
    if (!playlist || targets.length === 0) return;
    const unique = targets.filter(
      (slide, index, list) => list.findIndex((item) => item.id === slide.id) === index,
    );
    deckHistory.recordBeforeChange();
    try {
      const updates = new Map<string, Slide>();
      for (const slide of unique) {
        const guard = playlistWriteGuard();
        const updated = await updateSlide(
          playlist.id,
          slide.id,
          { isActive: !slide.isActive },
          guard,
        );
        recordWriteRevision(updated.playlistRevision, null, guard.expectedRevision);
        updates.set(updated.id, updated);
      }
      setPlaylist({
        ...playlist,
        slides: (playlist.slides ?? []).map((item) => updates.get(item.id) ?? item),
      });
      await deckHistory.confirmChange();
      if (unique.length > 1) {
        tvDashboardNotice(
          TV_DASHBOARD_HELP_TOOLTIPS.ribbon.slideBatchSaved.replace(
            "{count}",
            String(unique.length),
          ),
        );
      }
    } catch (caught) {
      deckHistory.cancelChange();
      if (await handlePlaylistWriteConflict(caught)) return;
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

  async function handleDropSlide(targetIndex: number, edge?: ListDropEdge) {
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
      edge,
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
      if (await handlePlaylistWriteConflict(caught)) return;
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
    onDuplicate: (targets: Slide[]) => void handleDuplicateSlides(targets),
    onToggleActive: (targets: Slide[]) => void handleToggleSlidesActive(targets),
    onRemove: (targets: Slide[]) => void handleRemoveSlides(targets),
    onExportPng: () => void handleExportPng(),
    onExportPdf: () => void handleExportPdf(),
    onExportPptx: selectedSlides.some(isCustomMessageSlide)
      ? () => void handleExportPptx()
      : undefined,
    exportBusy,
    playlistChrome: {
      playlistName: playlist.name,
      tvStatusLabel: tvStatusLabel(),
      tvStatusClass: tvStatusClass(),
      editingPresence:
        otherEditors.length > 0
          ? `Também editando: ${otherEditorsLabel}`
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
    selectedSlideCount: selectedSlides.length,
    selectedSlides,
    onSavePlaylistSettings: (field: string, value: string | number | Record<string, unknown>) =>
      void saveSettings(field, value),
    onSaveSlide: (slide: Slide, payload: Parameters<DeckSettingsProps["onSaveSlide"]>[1]) =>
      void handleSaveSlide(slide, payload, { recordHistory: true }).catch((caught) => {
        if (caught instanceof StaleWriteEpochError) return;
        tvDashboardNotice(
          caught instanceof Error ? caught.message : "Falha ao salvar o slide.",
        );
      }),
    onSaveSlides: (targets: Slide[], patch: SlideBatchInput) => void handleSaveSlides(targets, patch),
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
    onDrop: (index, edge) => void handleDropSlide(index, edge),
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
          foreignRemoteRevision={foreignConfigRevision}
          remoteSelections={currentRemoteSelections}
          onSelectionChange={sendSelectionUpdate}
          onChange={(config) => scheduleCustomSlideSave(selectedSlide, config)}
          resolveWriteGuard={resolveWriteGuard}
          onWriteCommitted={handleMutationCommitted}
          onWriteError={handleMutationWriteError}
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
        selectedSlideCount={selectedSlides.length}
        hasCurrentSlide={Boolean(selectedSlide)}
        progressLabel={exportPdfProgress}
        busy={exportBusy}
      />
      <KeyboardShortcutsCatalogModal />
      </DeckKeyTipsProvider>
      </KeyboardShortcutsTipsProvider>
    </DeckEditorHistoryProvider>
    </EditorShortcutsProvider>
  );
}
