import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import {
  applyFieldLabelsToResolved,
  isComunicadoVisualBoxBlock,
  isDataBlockType,
  isDataSourceBlockType,
  isDataViewBlockType,
  isFetchableDataBlockType,
  parseComunicadoConfig,
  serializeComunicadoConfig,
  sortBlocksByZIndex,
  type ComunicadoConfig,
  type ComunicadoBlock,
  type ComunicadoDataDisplayMode,
  type ComunicadoDataSourceBlock,
  type PresentationSelectionUpdateEvent,
  type ComunicadoTextBlock,
} from "@delpi/tv-dashboard-presentation";

import type { PlaylistMasterConfig } from "../api/tvDashboardApi";
import { useDeckEditorHistoryContext } from "../context/deckEditorHistoryContext";
import { useComunicadoEditorBlocks } from "../hooks/comunicadoEditor/useComunicadoEditorBlocks";
import { useComunicadoEditorClipboard } from "../hooks/comunicadoEditor/useComunicadoEditorClipboard";
import { useComunicadoEditorDrag } from "../hooks/comunicadoEditor/useComunicadoEditorDrag";
import { useComunicadoEditorHistory } from "../hooks/comunicadoEditor/useComunicadoEditorHistory";
import {
  fingerprintComunicadoValue,
  shouldAcceptExternalComunicadoValue,
  shouldForceAcceptRemoteComunicadoValue,
} from "../hooks/comunicadoEditor/comunicadoEditorValueSync";
import { useOptionalDataSourceDuplicateChoice } from "../context/DataSourceDuplicateChoiceProvider";
import { useComunicadoEditorMedia } from "../hooks/comunicadoEditor/useComunicadoEditorMedia";
import { useComunicadoEditorSelection } from "../hooks/comunicadoEditor/useComunicadoEditorSelection";
import { useComunicadoEditorStage } from "../hooks/comunicadoEditor/useComunicadoEditorStage";
import { useComunicadoDataPreview } from "../hooks/useComunicadoDataPreview";
import { useInputFilterDataRefresh } from "../hooks/useInputFilterDataRefresh";
import { useComunicadoEditorKeyboard } from "../hooks/useComunicadoEditorKeyboard";
import { useSyncViewDataLinks } from "../hooks/useSyncViewDataLinks";
import { resolveViewportPixelSize } from "../utils/viewportPixelSize";
import { MediaLibraryModal } from "./MediaLibraryModal";
import { enrichComunicadoConfigForEditor, resolveMasterForPreview } from "./slideCardPreview";
import {
  ComunicadoEditorContext,
  useComunicadoEditor,
  type ComunicadoEditorContextValue,
} from "./comunicadoEditorContextCore";

export type { MediaLibraryTarget } from "./comunicadoEditorTypes";
export {
  useComunicadoEditor,
  useOptionalComunicadoEditor,
  type ComunicadoEditorContextValue,
} from "./comunicadoEditorContextCore";

type ProviderProps = {
  playlistId: string;
  slideId?: string;
  globalRefreshSec?: number;
  /** Dimensão canônica do slide (720p / 1080p / 4k / portrait). */
  viewportProfile?: string;
  masterConfig?: PlaylistMasterConfig;
  value: Record<string, unknown>;
  /** Bump a cada mudança remota (WS slide_draft / presentation_updated) — força aceitar `value`. */
  remoteRevision?: number;
  /** Seleções remotas já filtradas para este slide. */
  remoteSelections?: PresentationSelectionUpdateEvent[];
  onSelectionChange?: (slideId: string, selectedIds: string[]) => void;
  onChange: (config: Record<string, unknown>) => void;
  children: ReactNode;
};

function ComunicadoEditorKeyboardBridge() {
  const deckHistory = useDeckEditorHistoryContext();
  const {
    blocks,
    selectedIds,
    editingTextId,
    selectedChartPart,
    selectedKpiPart,
    selectedTablePart,
    selectedInputPart,
    clearChartPartSelection,
    clearKpiPartSelection,
    clearTablePartSelection,
    clearInputPartSelection,
    selectBlocksByIds,
    undo,
    redo,
    canUndo,
    canRedo,
    duplicateSelected,
    removeSelected,
    cutSelected,
    copySelected,
    pasteSelected,
    canPaste,
    nudgeSelected,
  } = useComunicadoEditor();
  useComunicadoEditorKeyboard({
    selectedIds,
    editingTextId,
    blocks,
    selectBlocksByIds,
    hasPartSelection: Boolean(
      selectedChartPart || selectedKpiPart || selectedTablePart || selectedInputPart,
    ),
    clearPartSelection: () => {
      clearChartPartSelection();
      clearKpiPartSelection();
      clearTablePartSelection();
      clearInputPartSelection();
    },
    undo,
    redo,
    canUndo,
    canRedo,
    duplicateSelected,
    removeSelected,
    cutSelected,
    copySelected,
    pasteSelected,
    canPaste,
    nudgeSelected,
    enableHistoryShortcuts: !deckHistory,
  });
  return null;
}

export function ComunicadoEditorProvider({
  playlistId,
  slideId,
  globalRefreshSec = 300,
  viewportProfile = "1080p",
  masterConfig,
  value,
  remoteRevision = 0,
  remoteSelections = [],
  onSelectionChange,
  onChange,
  children,
}: ProviderProps) {
  const deckHistory = useDeckEditorHistoryContext();
  const [config, setConfig] = useState<ComunicadoConfig>(() =>
    enrichComunicadoConfigForEditor(value, playlistId),
  );
  const [appliedSlideId, setAppliedSlideId] = useState(slideId);
  const [lastDataDisplayMode, setLastDataDisplayMode] = useState<ComunicadoDataDisplayMode>("kpi");
  const [dataPanelOpen, setDataPanelOpen] = useState(false);
  const [dataPanelIntent, setDataPanelIntent] = useState<"binding" | "catalog">("binding");
  const [dataCatalogModalOpen, setDataCatalogModalOpen] = useState(false);
  const [dataCatalogAnchor, setDataCatalogAnchor] = useState<HTMLElement | null>(null);
  const [dataCatalogMode, setDataCatalogMode] = useState<"insert" | "replace">("insert");
  const [shapeMenuOpen, setShapeMenuOpen] = useState(false);

  const configRef = useRef(config);
  configRef.current = config;
  const lastEmittedFingerprintRef = useRef<string | null>(null);
  const syncIdentityRef = useRef(`${playlistId}:${slideId ?? ""}`);
  const lastHistoryEpochRef = useRef(deckHistory?.historyEpoch ?? 0);
  const lastRemoteRevisionRef = useRef(remoteRevision);

  const removeSelectedRef = useRef<() => void>(() => {});
  const editingTextIdRef = useRef<string | null>(null);
  const updateBlockTextFieldsRef = useRef<
    (blockId: string, fields: Pick<ComunicadoTextBlock, "content" | "contentRuns">) => void
  >(() => {});
  const updateBlocksRef = useRef<(next: ComunicadoBlock[]) => void>(() => {});

  const {
    resolvedByBlockId,
    loading: dataPreviewLoading,
    error: dataPreviewError,
    isDataPreviewStale,
    staleSourceIds,
    refreshingSourceIds,
    loadingMoreSourceIds,
    loadingProgressPercent: dataPreviewLoadingProgress,
    refreshDataPreview,
    loadMoreDataPreview,
    clearStaleForSourceIds,
  } = useComunicadoDataPreview({
    playlistId,
    config,
  });

  const { scheduleInputFilterRefresh, scheduleInputFilterRefreshById } = useInputFilterDataRefresh({
    blocks: config.blocks,
    refreshDataPreview,
    clearStaleForSourceIds,
  });

  const onInputBlocksRemoved = useCallback(
    ({ sourceIds }: { sourceIds: string[] }) => {
      if (sourceIds.length === 0) return;
      clearStaleForSourceIds?.(sourceIds);
      void refreshDataPreview({ force: true, blockIds: sourceIds });
    },
    [clearStaleForSourceIds, refreshDataPreview],
  );

  const blocks = useMemo(() => {
    const sorted = sortBlocksByZIndex(config.blocks ?? []);
    const fieldLabelsBySourceId = new Map<string, ComunicadoDataSourceBlock["fieldLabels"]>();
    for (const block of sorted) {
      if (isDataSourceBlockType(block.type)) {
        fieldLabelsBySourceId.set(block.id, (block as ComunicadoDataSourceBlock).fieldLabels);
      }
    }
    return sorted.map((block) => {
      if (isFetchableDataBlockType(block.type) && "dataBinding" in block) {
        const preview = resolvedByBlockId[block.id];
        if (preview) {
          const labeled =
            isDataSourceBlockType(block.type)
              ? applyFieldLabelsToResolved(
                  preview,
                  (block as ComunicadoDataSourceBlock).fieldLabels,
                ) ?? preview
              : preview;
          return { ...block, resolved: labeled };
        }
        return block;
      }
      if (
        isDataViewBlockType(block.type) &&
        "dataSourceId" in block &&
        typeof block.dataSourceId === "string" &&
        block.dataSourceId
      ) {
        const preview = resolvedByBlockId[block.dataSourceId];
        if (preview) {
          const labeled =
            applyFieldLabelsToResolved(
              preview,
              fieldLabelsBySourceId.get(block.dataSourceId),
            ) ?? preview;
          return { ...block, resolved: labeled };
        }
      }
      if (isComunicadoVisualBoxBlock(block) && block.dataSourceId?.trim()) {
        const sourceId = block.dataSourceId.trim();
        const preview = resolvedByBlockId[sourceId];
        if (preview) {
          const labeled =
            applyFieldLabelsToResolved(preview, fieldLabelsBySourceId.get(sourceId)) ??
            preview;
          return { ...block, resolved: labeled };
        }
      }
      if (isDataBlockType(block.type)) {
        const preview = resolvedByBlockId[block.id];
        if (preview) return { ...block, resolved: preview };
      }
      return block;
    });
  }, [config.blocks, resolvedByBlockId]);

  const selection = useComunicadoEditorSelection({
    configRef,
    blocks,
    updateBlockTextFieldsRef,
    updateBlocksRef,
  });

  useEffect(() => {
    if (!slideId) return;
    onSelectionChange?.(slideId, selection.selectedIds);
  }, [onSelectionChange, selection.selectedIds, slideId]);

  useEffect(
    () => () => {
      if (slideId) onSelectionChange?.(slideId, []);
    },
    [onSelectionChange, slideId],
  );

  // Troca de slide: sincroniza config no mesmo render (evita 1 frame com gráfico do slide anterior).
  if (slideId !== appliedSlideId) {
    setAppliedSlideId(slideId);
    const enriched = enrichComunicadoConfigForEditor(value, playlistId);
    setConfig(enriched);
    lastEmittedFingerprintRef.current = fingerprintComunicadoValue(
      serializeComunicadoConfig(enriched),
    );
    syncIdentityRef.current = `${playlistId}:${slideId ?? ""}`;
    selection.resetSelectionForSlide();
  }

  const stage = useComunicadoEditorStage();
  const designSizeRef = useRef(resolveViewportPixelSize(viewportProfile));
  designSizeRef.current = resolveViewportPixelSize(viewportProfile);

  const applyConfig = useCallback(
    (next: ComunicadoConfig) => {
      // Atualiza o ref no mesmo tick — consumidores encadeados (ex.: input + dataFilters)
      // não devem ler o config prévio e sobrescrever a primeira edição.
      configRef.current = next;
      setConfig(next);
      const serialized = serializeComunicadoConfig(next);
      lastEmittedFingerprintRef.current = fingerprintComunicadoValue(serialized);
      deckHistory?.setLiveComunicadoConfig(serialized);
      onChange(serialized);
    },
    [deckHistory, onChange],
  );

  const {
    pushPast,
    commitWithHistory,
    undo,
    redo,
    canUndo,
    canRedo,
    resetLocalHistory,
  } = useComunicadoEditorHistory({
    configRef,
    applyConfig,
    deckHistory,
  });

  const {
    canvasRef,
    startDrag,
    clearDragSnapshot,
    armMultiDragSelection,
    activeSmartGuides,
  } = useComunicadoEditorDrag({
    configRef,
    selectedIds: selection.selectedIds,
    selectedId: selection.selectedId,
    applyConfig,
    pushPast,
    deckHistory,
    snapEnabledRef: stage.snapEnabledRef,
    showStageGuidesRef: stage.showStageGuidesRef,
    stageGridSizePercentRef: stage.stageGridSizePercentRef,
  });
  stage.bindCanvasRef(canvasRef);

  useEffect(() => {
    const identity = `${playlistId}:${slideId ?? ""}`;
    const identityChanged = syncIdentityRef.current !== identity;
    syncIdentityRef.current = identity;

    const historyEpoch = deckHistory?.historyEpoch ?? 0;
    const forceAcceptFromHistory = historyEpoch !== lastHistoryEpochRef.current;
    if (forceAcceptFromHistory) {
      lastHistoryEpochRef.current = historyEpoch;
    }

    const remoteRevisionChanged = remoteRevision !== lastRemoteRevisionRef.current;
    lastRemoteRevisionRef.current = remoteRevision;

    const enriched = enrichComunicadoConfigForEditor(value, playlistId);
    const incomingFp = fingerprintComunicadoValue(serializeComunicadoConfig(enriched));
    const currentFp = fingerprintComunicadoValue(serializeComunicadoConfig(configRef.current));

    const forceAcceptFromRemote = shouldForceAcceptRemoteComunicadoValue({
      remoteRevisionChanged,
      incomingFingerprint: incomingFp,
      currentFingerprint: currentFp,
    });

    if (
      !shouldAcceptExternalComunicadoValue({
        identityChanged,
        incomingFingerprint: incomingFp,
        lastEmittedFingerprint: lastEmittedFingerprintRef.current,
        currentFingerprint: currentFp,
        forceAccept: forceAcceptFromHistory || forceAcceptFromRemote,
      })
    ) {
      return;
    }

    setConfig(enriched);
    lastEmittedFingerprintRef.current = incomingFp;
    if (identityChanged) {
      clearDragSnapshot();
      resetLocalHistory();
    }
  }, [
    value,
    playlistId,
    slideId,
    remoteRevision,
    resetLocalHistory,
    clearDragSnapshot,
    deckHistory?.historyEpoch,
  ]);

  const chooseDataSourceDuplicatePolicy = useOptionalDataSourceDuplicateChoice();

  const blockActions = useComunicadoEditorBlocks({
    configRef,
    commitWithHistory,
    selectedIds: selection.selectedIds,
    selectedId: selection.selectedId,
    selected: selection.selected,
    selectedBlocks: selection.selectedBlocks,
    selectedChartPart: selection.selectedChartPart,
    selectedTablePart: selection.selectedTablePart,
    selectedKpiPart: selection.selectedKpiPart,
    selectedInputPart: selection.selectedInputPart,
    editingChartPart: selection.editingChartPart,
    editingKpiPart: selection.editingKpiPart,
    setSelectedId: selection.setSelectedId,
    selectBlocksByIds: selection.selectBlocksByIds,
    setSelectedChartPart: selection.setSelectedChartPart,
    setEditingChartPart: selection.setEditingChartPart,
    setSelectedTablePart: selection.setSelectedTablePart,
    setSelectedKpiPart: selection.setSelectedKpiPart,
    setEditingKpiPart: selection.setEditingKpiPart,
    setLastDataDisplayMode,
    setDataPanelOpen,
    setDataPanelIntent,
    setDataCatalogModalOpen,
    setDataCatalogAnchor,
    setDataCatalogMode,
    setShapeMenuOpen,
    setRibbonTabRequest: selection.setRibbonTabRequest,
    removeSelectedRef,
    updateBlockTextFieldsRef,
    onInputBlocksRemoved,
    getSourceResolved: (sourceId: string) => resolvedByBlockId[sourceId],
    chooseDataSourceDuplicatePolicy: chooseDataSourceDuplicatePolicy ?? undefined,
  });

  updateBlocksRef.current = blockActions.updateBlocks;

  useSyncViewDataLinks({
    configRef,
    blocks: config.blocks ?? [],
    resolvedByBlockId,
    commitBlocks: blockActions.updateBlocks,
  });


  const setSpeakerNotes = useCallback(
    (speakerNotes: string) => {
      commitWithHistory({
        ...configRef.current,
        speakerNotes: speakerNotes || undefined,
      });
    },
    [commitWithHistory],
  );

  const updateBlocksAtomically = useCallback(
    (
      patches: ReadonlyArray<{
        blockId: string;
        patch: Partial<ComunicadoBlock>;
      }>,
    ) => {
      if (patches.length === 0) return;
      const byId = new Map(patches.map((item) => [item.blockId, item.patch]));
      const nextBlocks = (configRef.current.blocks ?? []).map((block) => {
        const patch = byId.get(block.id);
        return patch ? ({ ...block, ...patch } as ComunicadoBlock) : block;
      });
      blockActions.updateBlocks(nextBlocks);
    },
    [blockActions],
  );

  const getClipboardSources = useCallback(
    () =>
      selection.selectedBlocks.length > 0
        ? selection.selectedBlocks
        : selection.selected
          ? [selection.selected]
          : [],
    [selection.selected, selection.selectedBlocks],
  );

  const updateBlocksForClipboard = useCallback(
    (nextBlocks: typeof blocks) => {
      commitWithHistory({ ...configRef.current, blocks: nextBlocks });
    },
    [commitWithHistory],
  );

  const getExistingBlocksForClipboard = useCallback(
    () => configRef.current.blocks ?? [],
    [],
  );

  editingTextIdRef.current = selection.editingTextId;

  const { copySelected, cutSelected, pasteSelected, pasteFromSystemClipboard, canPaste } =
    useComunicadoEditorClipboard({
      playlistId,
      getSources: getClipboardSources,
      getExistingBlocks: getExistingBlocksForClipboard,
      selectBlocksByIds: selection.selectBlocksByIds,
      updateBlocks: updateBlocksForClipboard,
      removeSelected: () => removeSelectedRef.current(),
      chooseDataSourceDuplicatePolicy: chooseDataSourceDuplicatePolicy ?? undefined,
      getEditingTextId: () => editingTextIdRef.current,
    });

  const media = useComunicadoEditorMedia({
    playlistId,
    configRef,
    selectedId: selection.selectedId,
    selected: selection.selected,
    commitWithHistory,
    updateBlocks: blockActions.updateBlocks,
    setSelectedId: selection.setSelectedId,
  });

  const resolvedMaster = useMemo(
    () => resolveMasterForPreview(masterConfig, playlistId),
    [masterConfig, playlistId],
  );

  const background = config.background
    ?? (resolvedMaster?.background as ComunicadoConfig["background"] | undefined)
    ?? { type: "color", value: "#ffffff" };
  const masterLogo =
    resolvedMaster && typeof resolvedMaster.logo === "object" && resolvedMaster.logo
      ? (resolvedMaster.logo as {
          url?: string;
          frame?: { x?: number; y?: number; w?: number; h?: number };
          opacity?: number;
        })
      : null;

  const ctxValue: ComunicadoEditorContextValue = {
    config,
    viewportProfile: viewportProfile || "1080p",
    appliedSlideId,
    blocks,
    selectedIds: selection.selectedIds,
    selectedId: selection.selectedId,
    selected: selection.selected,
    selectedBlocks: selection.selectedBlocks,
    remoteSelections,
    isBlockSelected: selection.isBlockSelected,
    selectBlock: selection.selectBlock,
    selectBlocksByIds: selection.selectBlocksByIds,
    clearSelection: selection.clearSelection,
    setSelectedId: selection.setSelectedId,
    selectedChartPart: selection.selectedChartPart,
    selectChartPart: selection.selectChartPart,
    clearChartPartSelection: selection.clearChartPartSelection,
    editingChartPart: selection.editingChartPart,
    beginEditChartPart: selection.beginEditChartPart,
    commitChartPartContent: blockActions.commitChartPartContent,
    cancelEditChartPart: selection.cancelEditChartPart,
    selectedTablePart: selection.selectedTablePart,
    selectedTableParts: selection.selectedTableParts,
    selectTablePart: selection.selectTablePart,
    clearTablePartSelection: selection.clearTablePartSelection,
    editingTablePart: selection.editingTablePart,
    beginEditTablePart: selection.beginEditTablePart,
    cancelEditTablePart: selection.cancelEditTablePart,
    selectedKpiPart: selection.selectedKpiPart,
    selectKpiPart: selection.selectKpiPart,
    clearKpiPartSelection: selection.clearKpiPartSelection,
    editingKpiPart: selection.editingKpiPart,
    beginEditKpiPart: selection.beginEditKpiPart,
    selectedInputPart: selection.selectedInputPart,
    selectInputPart: selection.selectInputPart,
    clearInputPartSelection: selection.clearInputPartSelection,
    commitKpiPartContent: blockActions.commitKpiPartContent,
    cancelEditKpiPart: selection.cancelEditKpiPart,
    editingTextId: selection.editingTextId,
    setEditingTextId: selection.setEditingTextId,
    textEditSelection: selection.textEditSelection,
    textEditSelectionStyle: selection.textEditSelectionStyle,
    textEditListSelection: selection.textEditListSelection,
    textEditNamedStyleSelection: selection.textEditNamedStyleSelection,
    registerTextEditorBridge: selection.registerTextEditorBridge,
    reportTextEditSelection: selection.reportTextEditSelection,
    toggleEditingTextRunStyle: selection.toggleEditingTextRunStyle,
    toggleSelectedTextListType: selection.toggleSelectedTextListType,
    applySelectedNamedTextStyle: selection.applySelectedNamedTextStyle,
    insertDataFieldAtCursor: selection.insertDataFieldAtCursor,
    uploading: media.uploading,
    shapeMenuOpen,
    setShapeMenuOpen,
    background,
    canvasRef,
    startDrag,
    armMultiDragSelection,
    addBlock: blockActions.addBlock,
    addDataBlock: blockActions.addDataBlock,
    addDataSourceBlock: blockActions.addDataSourceBlock,
    addChartViewBlock: blockActions.addChartViewBlock,
    addCanvasTableBlock: blockActions.addCanvasTableBlock,
    addInputBlock: blockActions.addInputBlock,
    addTableViewBlock: blockActions.addTableViewBlock,
    addKpiViewBlock: blockActions.addKpiViewBlock,
    openDataPanel: blockActions.openDataPanel,
    openLayersPanel: selection.openLayersPanel,
    openDataCatalog: blockActions.openDataCatalog,
    dataCatalogModalOpen,
    setDataCatalogModalOpen,
    dataCatalogAnchor,
    setDataCatalogAnchor,
    dataCatalogMode,
    setDataCatalogMode,
    dataPanelOpen,
    setDataPanelOpen,
    dataPanelIntent,
    setDataPanelIntent,
    selectionPanelTab: selection.selectionPanelTab,
    setSelectionPanelTab: selection.setSelectionPanelTab,
    addShape: blockActions.addShape,
    addIconBlock: blockActions.addIconBlock,
    groupSelected: blockActions.groupSelected,
    ungroupSelected: blockActions.ungroupSelected,
    connectSelected: blockActions.connectSelected,
    setDataFilters: blockActions.setDataFilters,
    patchInputBlock: blockActions.patchInputBlock,
    setSpeakerNotes,
    updateSelected: blockActions.updateSelected,
    updateBlock: blockActions.updateBlock,
    updateBlocksAtomically,
    updateBlockContent: blockActions.updateBlockContent,
    updateBlockTextFields: blockActions.updateBlockTextFields,
    updateBlockLink: blockActions.updateBlockLink,
    updateSelectedStyle: blockActions.updateSelectedStyle,
    updateSelectedTextFormatStyle: blockActions.updateSelectedTextFormatStyle,
    removeSelected: blockActions.removeSelected,
    duplicateSelected: blockActions.duplicateSelected,
    cutSelected,
    copySelected,
    pasteSelected,
    pasteFromSystemClipboard,
    canPaste,
    bringToFront: blockActions.bringToFront,
    sendToBack: blockActions.sendToBack,
    bringForward: blockActions.bringForward,
    sendBackward: blockActions.sendBackward,
    requestRibbonTab: selection.requestRibbonTab,
    ribbonTabRequest: selection.ribbonTabRequest,
    clearRibbonTabRequest: selection.clearRibbonTabRequest,
    replaceSelectedDataRoute: blockActions.replaceSelectedDataRoute,
    moveLayer: blockActions.moveLayer,
    reorderBlockLayer: blockActions.reorderBlockLayer,
    nudgeSelected: blockActions.nudgeSelected,
    undo,
    redo,
    canUndo,
    canRedo,
    playlistId,
    masterLogo,
    mediaLibraryOpen: media.mediaLibraryOpen,
    mediaLibraryTarget: media.mediaLibraryTarget,
    openMediaLibrary: media.openMediaLibrary,
    closeMediaLibrary: media.closeMediaLibrary,
    applyMediaAsset: media.applyMediaAsset,
    triggerUpload: media.triggerUpload,
    setBackgroundColor: blockActions.setBackgroundColor,
    setBackgroundGradient: blockActions.setBackgroundGradient,
    bindSelectedVisualBoxToData: blockActions.bindSelectedVisualBoxToData,
    insertTextDataFieldBlock: blockActions.insertTextDataFieldBlock,
    applySlideTemplate: blockActions.applySlideTemplate,
    applySlideTheme: blockActions.applySlideTheme,
    alignSelected: blockActions.alignSelected,
    stageZoom: stage.stageZoom,
    setStageZoom: stage.setStageZoom,
    fitStageToView: stage.fitStageToView,
    restoreStageViewPosition: stage.restoreStageViewPosition,
    bootstrapStageViewPosition: stage.bootstrapStageViewPosition,
    stageViewReady: stage.stageViewReady,
    persistStageViewPosition: stage.persistStageViewPosition,
    canvasWrapRef: stage.canvasWrapRef,
    showStageRulers: stage.showStageRulers,
    setShowStageRulers: stage.setShowStageRulers,
    showStageGrid: stage.showStageGrid,
    setShowStageGrid: stage.setShowStageGrid,
    stageGridSizePercent: stage.stageGridSizePercent,
    setStageGridSizePercent: stage.setStageGridSizePercent,
    showStageGuides: stage.showStageGuides,
    setShowStageGuides: stage.setShowStageGuides,
    activeSmartGuides,
    snapEnabled: stage.snapEnabled,
    setSnapEnabled: stage.setSnapEnabled,
    stagePanMode: stage.stagePanMode,
    setStagePanMode: stage.setStagePanMode,
    fileInputRef: media.fileInputRef,
    handleUploadFile: media.handleUploadFile,
    uploadCustomFont: media.uploadCustomFont,
    dataPreviewLoading,
    dataPreviewLoadingProgress,
    dataPreviewError,
    isDataPreviewStale,
    staleSourceIds,
    refreshingSourceIds,
    loadingMoreSourceIds,
    refreshDataPreview,
    loadMoreDataPreview,
    scheduleInputFilterRefresh,
    scheduleInputFilterRefreshById,
    globalRefreshSec,
    lastDataDisplayMode,
    setLastDataDisplayMode,
  };

  return (
    <ComunicadoEditorContext.Provider value={ctxValue}>
      <ComunicadoEditorKeyboardBridge />
      <input
        ref={media.fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp,image/gif,video/mp4,video/webm"
        hidden
        onChange={(event) => {
          const file = event.target.files?.[0];
          event.target.value = "";
          if (file) void media.handleUploadFile(file, media.uploadTargetRef.current);
        }}
      />
      <MediaLibraryModal
        open={media.mediaLibraryOpen}
        target={media.mediaLibraryTarget}
        playlistId={playlistId}
        uploading={media.uploading}
        onClose={media.closeMediaLibrary}
        onPick={media.applyMediaAsset}
        onUploaded={() => {
          /* lista recarrega ao reabrir */
        }}
      />
      {children}
    </ComunicadoEditorContext.Provider>
  );
}

export function parseCustomSlideConfig(raw: Record<string, unknown>): Record<string, unknown> {
  return serializeComunicadoConfig(parseComunicadoConfig(raw));
}
