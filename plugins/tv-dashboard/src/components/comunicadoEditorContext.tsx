import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { dismissActiveExclusiveAnchoredPanel } from "@delpi/plugin-ui/index";

import {
  applyFieldLabelsToResolved,
  bindingTargetId,
  collectCanvasTableSourceIds,
  defaultFrame,
  ensureEfficiencyPinResizableFrame,
  isComunicadoVisualBoxBlock,
  isDataBlockType,
  isDataSourceBlockType,
  isDataViewBlockType,
  isEfficiencyPinBlock,
  isFetchableDataBlockType,
  parseComunicadoConfig,
  resolveStageMasterLogo,
  serializeComunicadoConfig,
  sortBlocksByZIndex,
  type ComunicadoBackground,
  type ComunicadoConfig,
  type ComunicadoBlock,
  type ComunicadoDataDisplayMode,
  type ComunicadoDataSourceBlock,
  type PresentationSelectionUpdateEvent,
  type ComunicadoShapeBlock,
  type ComunicadoTextBlock,
  type TvDataModel,
} from "@delpi/tv-dashboard-presentation";

import type { PlaylistMasterConfig, WriteGuard } from "../api/tvDashboardApi";
import { useDeckEditorHistoryContext } from "../context/deckEditorHistoryContext";
import { useComunicadoEditorBlocks } from "../hooks/comunicadoEditor/useComunicadoEditorBlocks";
import { useComunicadoEditorClipboard } from "../hooks/comunicadoEditor/useComunicadoEditorClipboard";
import { useComunicadoEditorDrag } from "../hooks/comunicadoEditor/useComunicadoEditorDrag";
import { useComunicadoEditorHistory } from "../hooks/comunicadoEditor/useComunicadoEditorHistory";
import {
  fingerprintComunicadoValue,
  shouldAcceptExternalComunicadoValue,
  shouldForceAcceptRemoteComunicadoValue,
  shouldInvalidateLocalComunicadoHistory,
} from "../hooks/comunicadoEditor/comunicadoEditorValueSync";
import { useOptionalDataSourceDuplicateChoice } from "../context/DataSourceDuplicateChoiceProvider";
import { useComunicadoEditorMedia } from "../hooks/comunicadoEditor/useComunicadoEditorMedia";
import { useComunicadoEditorSelection } from "../hooks/comunicadoEditor/useComunicadoEditorSelection";
import { useComunicadoEditorStage } from "../hooks/comunicadoEditor/useComunicadoEditorStage";
import { useEditorVideoPosterAssets } from "../hooks/comunicadoEditor/useEditorVideoPosterAssets";
import { useComunicadoDataPreview } from "../hooks/useComunicadoDataPreview";
import { useInputFilterDataRefresh } from "../hooks/useInputFilterDataRefresh";
import { useComunicadoEditorKeyboard } from "../hooks/useComunicadoEditorKeyboard";
import { useSyncViewDataLinks } from "../hooks/useSyncViewDataLinks";
import { resolveCanvasTableMergeCommand } from "../utils/canvasTableMergeCommands";
import { serializeDataModelForPreview } from "../utils/dataPreviewRequest";
import { preferEditorViewResolved } from "../utils/preferEditorViewResolved";
import { buildDataModelEditPlan } from "../utils/dataModelPatchPlan";
import {
  commitDeleteDataModel,
  commitPatchDataModel,
  commitUpsertDataModel,
  type MutationCommitMeta,
} from "../utils/presentationMutationClient";
import type { MutationErrorHandler } from "../utils/mutationAckGeneration";
import {
  createPendingProjectionRegistry,
  resolvePersistableConfig,
  resolvePersistableDispatchDecision,
  resolveProjectionBaseline,
  type PersistableDispatchDecision,
} from "../utils/pendingMutationProjection";
import { resolveStageHasPartSelection } from "../utils/stageInteractionPolicy";
import { resolveViewportPixelSize } from "../utils/viewportPixelSize";
import { MediaLibraryModal } from "./MediaLibraryModal";
import {
  enrichComunicadoConfigForEditor,
  ensureComunicadoEditorMediaUrls,
  hydrateEditorVideoPosters,
  resolveMasterForPreview,
} from "./slideCardPreview";
import {
  ComunicadoEditorContext,
  useComunicadoEditor,
  type ComunicadoCanvasTableCellSelection,
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
  /** Token público — stream de vídeo/imagem no palco sem JWT na query. */
  publicToken?: string | null;
  slideId?: string;
  globalRefreshSec?: number;
  /** Dimensão canônica do slide (720p / 1080p / 4k / portrait / custom). */
  viewportProfile?: string;
  viewportWidth?: number | null;
  viewportHeight?: number | null;
  masterConfig?: PlaylistMasterConfig;
  /** Filtros globais da programação (live) — disparam refresh do preview. */
  playlistDefaults?: Record<string, unknown> | null;
  value: Record<string, unknown>;
  /** Bump a cada mudança remota (WS slide_draft / presentation_updated) — força aceitar `value`. */
  remoteRevision?: number;
  /**
   * Bump somente para baseline EXTERNA (outro editor/copiloto/draft de peer —
   * revisão remota acima do write-head compartilhado). Acks da própria escrita
   * sobem `remoteRevision` mas nunca este contador: o sinal dispara a
   * invalidação do histórico local de undo/redo.
   */
  foreignRemoteRevision?: number;
  /** Seleções remotas já filtradas para este slide. */
  remoteSelections?: PresentationSelectionUpdateEvent[];
  onSelectionChange?: (slideId: string, selectedIds: string[]) => void;
  onChange: (config: Record<string, unknown>) => void;
  /**
   * Há save de autosave agendado/em captura para o slide? (027) Usado pelo
   * refresh do canal de projeção pendente: reemissão só atualiza payload já
   * agendado — nunca cria PATCH redundante do estado que a mutation persistiu.
   */
  hasPendingPersistableSave?: (slideId: string) => boolean;
  /**
   * Cancela o save de autosave agendado do slide (027) — usado quando o
   * payload resolvido coincide com o estado autoritativo: a escrita seria
   * no-op e só criaria churn de revisão/WS para os peers.
   */
  cancelPendingPersistableSave?: (slideId: string) => void;
  /**
   * Guarda de dispatch do autosave (028): o provider preenche este ref com a
   * função que decide — já DENTRO da write lane, após o settle da mutation —
   * se o payload capturado ainda é a visão persistível segura do slide.
   * `send:false` descarta o write stale; `reEmit` carrega canônico+delta
   * autosave-only para reagendamento (ex.: flush de navegação pós-commit).
   */
  persistableDispatchResolverRef?: {
    current:
      | ((
          slideId: string,
          captured: Record<string, unknown>,
        ) => PersistableDispatchDecision)
      | null;
  };
  /** OCC guard resolved per persisted mutation — slide base revision + clientId. */
  resolveWriteGuard?: () => WriteGuard | null | undefined;
  /** Revision metadata emitted after each committed mutation. */
  onWriteCommitted?: (meta: MutationCommitMeta) => void;
  /** Persist failures (incl. 409 REVISION_CONFLICT) surfaced to the owner. */
  onWriteError?: MutationErrorHandler;
  children: ReactNode;
};

function ComunicadoEditorKeyboardBridge() {
  const {
    blocks,
    selectedIds,
    preferGroupChildrenSelection,
    editingTextId,
    enterTextEdit,
    setEditingTextId,
    selectBlock,
    selectedChartPart,
    selectedKpiPart,
    selectedTablePart,
    selectedInputPart,
    selectedCanvasTableCell,
    clearPartSelections,
    selectBlocksByIds,
    clearSelection,
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
    groupSelected,
    ungroupSelected,
    nudgeSelected,
    stageDrawTool,
    setStageDrawTool,
    updateBlock,
  } = useComunicadoEditor();

  const mergeCanvasTableSelection = useCallback(() => {
    if (!selectedCanvasTableCell) return false;
    const block = blocks.find((item) => item.id === selectedCanvasTableCell.blockId);
    if (!block || block.type !== "canvas_table") return false;
    const next = resolveCanvasTableMergeCommand({
      merges: block.merges,
      cells: selectedCanvasTableCell.cells,
      mode: "merge",
      cellMatrix: block.cells,
    });
    if (!next) return false;
    updateBlock(block.id, {
      merges: next.merges.length ? next.merges : undefined,
      ...(next.cells ? { cells: next.cells } : {}),
    });
    return true;
  }, [blocks, selectedCanvasTableCell, updateBlock]);

  const unmergeCanvasTableSelection = useCallback(() => {
    if (!selectedCanvasTableCell) return false;
    const block = blocks.find((item) => item.id === selectedCanvasTableCell.blockId);
    if (!block || block.type !== "canvas_table") return false;
    const next = resolveCanvasTableMergeCommand({
      merges: block.merges,
      cells: selectedCanvasTableCell.cells,
      mode: "unmerge",
    });
    if (!next) return false;
    updateBlock(block.id, { merges: next.merges.length ? next.merges : undefined });
    return true;
  }, [blocks, selectedCanvasTableCell, updateBlock]);

  useComunicadoEditorKeyboard({
    selectedIds,
    preferGroupChildrenSelection,
    editingTextId,
    blocks,
    selectBlocksByIds,
    stageDrawTool,
    clearStageDrawTool: () => setStageDrawTool(null),
    hasPartSelection: resolveStageHasPartSelection({
      selectedChartPart,
      selectedKpiPart,
      selectedTablePart,
      selectedInputPart,
      selectedCanvasTableCell,
    }),
    clearPartSelection: clearPartSelections,
    clearSelection,
    enterTextEdit,
    exitTextEdit: () => setEditingTextId(null),
    isolateChild: (blockId) => selectBlock(blockId, { expandGroup: false }),
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
    groupSelected,
    ungroupSelected,
    nudgeSelected,
    mergeCanvasTableSelection,
    unmergeCanvasTableSelection,
    /* Undo do slide é local/imediato — deck history é só trilha de revisão. */
    enableHistoryShortcuts: true,
  });
  return null;
}

export function ComunicadoEditorProvider({
  playlistId,
  publicToken = null,
  slideId,
  globalRefreshSec = 300,
  viewportProfile = "1080p",
  viewportWidth = null,
  viewportHeight = null,
  masterConfig,
  playlistDefaults = null,
  value,
  remoteRevision = 0,
  foreignRemoteRevision = 0,
  remoteSelections = [],
  onSelectionChange,
  onChange,
  hasPendingPersistableSave,
  cancelPendingPersistableSave,
  persistableDispatchResolverRef,
  resolveWriteGuard,
  onWriteCommitted,
  onWriteError,
  children,
}: ProviderProps) {
  const deckHistory = useDeckEditorHistoryContext();
  const {
    posterAssets: videoPosterAssets,
    posterAssetsRef: videoPosterAssetsRef,
    registerMediaAsset: registerVideoMediaAsset,
  } = useEditorVideoPosterAssets(playlistId);
  const [config, setConfig] = useState<ComunicadoConfig>(() =>
    enrichComunicadoConfigForEditor(value, playlistId, videoPosterAssets),
  );
  const [appliedSlideId, setAppliedSlideId] = useState(slideId);
  const [lastDataDisplayMode, setLastDataDisplayMode] = useState<ComunicadoDataDisplayMode>("kpi");
  const [dataPanelOpen, setDataPanelOpen] = useState(false);
  const [dataPanelIntent, setDataPanelIntent] = useState<"binding" | "catalog">("binding");
  const [dataCatalogModalOpen, setDataCatalogModalOpen] = useState(false);
  const [dataCatalogAnchor, setDataCatalogAnchor] = useState<HTMLElement | null>(null);
  const [dataCatalogMode, setDataCatalogMode] = useState<"insert" | "replace">("insert");
  const [expressionEditRequest, setExpressionEditRequest] =
    useState<import("./comunicadoEditorContextCore").ExpressionEditRequest | null>(null);
  const openExpressionEditorCallback = useCallback(
    (request: import("./comunicadoEditorContextCore").ExpressionEditRequest) => {
      // Anchored panels sit above the modal layer by design (nested selects
      // inside modals); the originating popover must close before the modal.
      dismissActiveExclusiveAnchoredPanel();
      setExpressionEditRequest(request);
    },
    [],
  );
  const closeExpressionEditorCallback = useCallback(() => {
    setExpressionEditRequest(null);
  }, []);
  const [shapeMenuOpen, setShapeMenuOpen] = useState(false);
  const [stageDrawTool, setStageDrawTool] = useState<
    import("@delpi/tv-dashboard-presentation").ComunicadoLineToolId | null
  >(null);

  const configRef = useRef(config);
  configRef.current = config;
  const lastEmittedFingerprintRef = useRef<string | null>(null);
  /**
   * Ledger de projeções mutation-backed in-flight (027). Enquanto uma entidade
   * está coberta por mutation pendente, a serialização emitida ao autosave
   * resolve para o baseline confirmado — a projeção nunca entra no PATCH.
   */
  const pendingProjectionRegistryRef = useRef(createPendingProjectionRegistry());
  /** Baseline do último applyConfig — dispatch de mutation usa como baseline. */
  const projectionBaselineStashRef = useRef<{ prev: ComunicadoConfig } | null>(
    null,
  );
  /** Último payload persistível emitido ao onChange (dedupe do autosave). */
  const lastScheduledPersistableRef = useRef<string | null>(null);
  /**
   * Último estado persistível confirmado como persistido (slide load,
   * aplicação remota, ACK canônico). Um save pendente cujo payload resolvido
   * coincide com ele é no-op de escrita — é cancelado, não reagendado (027).
   */
  const authoritativePersistableRef = useRef<string | null>(null);
  /**
   * Mesmo estado confirmado de `authoritativePersistableRef` em forma de
   * config — fallback do baseline da projeção quando o stash foi limpo
   * (slide-switch/remote-apply) e a mutation dispara antes de novo
   * applyConfig (028). Estado confirmado real; nunca um baseline inventado.
   */
  const authoritativeConfigRef = useRef<ComunicadoConfig | null>(null);
  /**
   * Último commit mutation-backed por slide (028). A write lane é FIFO: um
   * PATCH de autosave capturado com baseline coberto só DESPACHA depois do
   * settle da mutation — se ela commitou, o baseline capturado ficou stale e
   * o PATCH reverteria a projeção já confirmada. A guarda de dispatch
   * (`persistableDispatchResolverRef`) consulta este registro para descartar
   * o save ou reemitir canônico+delta autosave-only (ex.: flush A→B).
   */
  const committedBySlideRef = useRef(
    new Map<
      string,
      { canonical: ComunicadoConfig; coveredKeys: ReadonlySet<string> }
    >(),
  );
  const syncIdentityRef = useRef(`${playlistId}:${slideId ?? ""}`);
  const lastHistoryEpochRef = useRef(deckHistory?.historyEpoch ?? 0);
  const lastRemoteRevisionRef = useRef(remoteRevision);
  const lastForeignRemoteRevisionRef = useRef(foreignRemoteRevision);

  const removeSelectedRef = useRef<() => void>(() => {});
  const editingTextIdRef = useRef<string | null>(null);
  const selectedCanvasTableCellRef = useRef<ComunicadoCanvasTableCellSelection | null>(null);
  const slideIdRef = useRef(slideId);
  slideIdRef.current = slideId;
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
    loadingProgressLabel: dataPreviewLoadingLabel,
    refreshDataPreview,
    loadMoreDataPreview,
    clearStaleForSourceIds,
  } = useComunicadoDataPreview({
    playlistId,
    config,
    playlistDefaults,
    globalRefreshSec,
  });

  const { scheduleInputFilterRefresh, scheduleInputFilterRefreshById } = useInputFilterDataRefresh({
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
    // DataModels carregam fieldLabels próprios (contrato DM1) — lookup por target id.
    const fieldLabelsByTargetId = new Map<string, ComunicadoDataSourceBlock["fieldLabels"]>();
    for (const model of config.dataModels ?? []) {
      if (model.fieldLabels) fieldLabelsByTargetId.set(model.id, model.fieldLabels);
    }
    const labelsForTarget = (targetId: string) =>
      fieldLabelsBySourceId.get(targetId) ?? fieldLabelsByTargetId.get(targetId);
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
      if (isDataViewBlockType(block.type) && bindingTargetId(block)) {
        const targetId = bindingTargetId(block);
        const sourcePreview = resolvedByBlockId[targetId];
        const linked =
          sourcePreview?.linkedResolvedByBlockId?.[block.id] ??
          resolvedByBlockId[block.id];
        const preview = preferEditorViewResolved({
          blockType: block.type,
          linked,
          source: sourcePreview,
        });
        if (preview) {
          const labeled =
            applyFieldLabelsToResolved(
              preview,
              labelsForTarget(targetId),
            ) ?? preview;
          return { ...block, resolved: labeled };
        }
      }
      if (isComunicadoVisualBoxBlock(block) && bindingTargetId(block)) {
        const targetId = bindingTargetId(block);
        const sourcePreview = resolvedByBlockId[targetId];
        const linked =
          sourcePreview?.linkedResolvedByBlockId?.[block.id] ??
          resolvedByBlockId[block.id];
        const preview = preferEditorViewResolved({
          blockType: block.type,
          linked,
          source: sourcePreview,
        });
        if (preview) {
          const labeled =
            applyFieldLabelsToResolved(preview, labelsForTarget(targetId)) ??
            preview;
          return { ...block, resolved: labeled };
        }
      }
      if (block.type === "canvas_table") {
        const sourceIds = collectCanvasTableSourceIds(block);
        if (sourceIds.length === 0) return block;
        const resolvedBySourceId: Record<string, NonNullable<(typeof resolvedByBlockId)[string]>> =
          {};
        for (const sourceId of sourceIds) {
          const preview = resolvedByBlockId[sourceId];
          if (!preview) continue;
          resolvedBySourceId[sourceId] =
            applyFieldLabelsToResolved(preview, labelsForTarget(sourceId)) ?? preview;
        }
        if (Object.keys(resolvedBySourceId).length === 0) return block;
        const primary = bindingTargetId(block);
        // Prefer canvas enrich stamp from any linked source map.
        const linkedCanvas =
          (primary &&
            resolvedByBlockId[primary]?.linkedResolvedByBlockId?.[block.id]) ||
          Object.values(resolvedByBlockId)
            .map((r) => r?.linkedResolvedByBlockId?.[block.id])
            .find(Boolean);
        const resolved =
          linkedCanvas ||
          (primary && resolvedBySourceId[primary]) ||
          Object.values(resolvedBySourceId)[0];
        return {
          ...block,
          resolved,
          resolvedBySourceId,
        };
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
    const enriched = enrichComunicadoConfigForEditor(value, playlistId, videoPosterAssets);
    setConfig(enriched);
    lastEmittedFingerprintRef.current = fingerprintComunicadoValue(
      serializeComunicadoConfig(enriched),
    );
    // O ledger é por slide: o slide anterior mantém marks no provider antigo;
    // o novo começa do estado autoritativo carregado.
    pendingProjectionRegistryRef.current.clear();
    projectionBaselineStashRef.current = null;
    // Nova época para o slide entrante: commits anteriores dele não podem
    // marcar saves capturados nesta visita como stale.
    if (slideId) committedBySlideRef.current.delete(slideId);
    lastScheduledPersistableRef.current = JSON.stringify(
      serializeComunicadoConfig(enriched),
    );
    authoritativePersistableRef.current = lastScheduledPersistableRef.current;
    authoritativeConfigRef.current = enriched;
    syncIdentityRef.current = `${playlistId}:${slideId ?? ""}`;
    selection.resetSelectionForSlide();
  }

  const stage = useComunicadoEditorStage();
  const designSizeRef = useRef(
    resolveViewportPixelSize(viewportProfile, { width: viewportWidth, height: viewportHeight }),
  );
  designSizeRef.current = resolveViewportPixelSize(viewportProfile, {
    width: viewportWidth,
    height: viewportHeight,
  });

  /**
   * Emissão persistível (027): entidades cobertas por mutation in-flight
   * serializam o baseline confirmado — a projeção local fica restrita ao palco.
   * Emissões que não mudam o payload persistível são suprimidas (dedupe).
   */
  const emitPersistableConfig = useCallback(
    (live: ComunicadoConfig) => {
      const { resolved } = resolvePersistableConfig(
        live,
        pendingProjectionRegistryRef.current,
      );
      const serialized = serializeComunicadoConfig(resolved);
      const key = JSON.stringify(serialized);
      if (key === lastScheduledPersistableRef.current) return;
      lastScheduledPersistableRef.current = key;
      /* 028: payload resolvido igual ao estado autoritativo = write no-op —
       * suprime a emissão e cancela um save agendado residual. Sem isso, um
       * applyConfig pós-ACK reemite o estado canônico como autosave novo
       * (PATCH redundante que bumpa revisão e quebra o CAS de peers). */
      if (slideId && key === authoritativePersistableRef.current) {
        if (hasPendingPersistableSave?.(slideId)) {
          cancelPendingPersistableSave?.(slideId);
        }
        return;
      }
      onChange(serialized);
    },
    [
      cancelPendingPersistableSave,
      hasPendingPersistableSave,
      onChange,
      slideId,
    ],
  );

  const applyConfig = useCallback(
    (
      next: ComunicadoConfig,
      options?: { persist?: boolean; authoritative?: boolean },
    ) => {
      // Serialize omite url; re-injetar no estado local evita placeholder até troca de slide.
      const withMedia = ensureComunicadoEditorMediaUrls(
        next,
        playlistId,
        videoPosterAssetsRef.current,
      );
      const serialized = serializeComunicadoConfig(withMedia);
      if (options?.authoritative) {
        // Aplicação de estado confirmado (ACK/read-back/reconcile): passa a
        // ser a referência "o servidor já tem isto" do canal persistível (027).
        authoritativePersistableRef.current = JSON.stringify(serialized);
        authoritativeConfigRef.current = withMedia;
      }
      // Baseline da projeção: o config anterior a ESTA aplicação é o último
      // estado confirmável para o canal de persistência (027).
      projectionBaselineStashRef.current = { prev: configRef.current };
      // Atualiza o ref no mesmo tick — consumidores encadeados (ex.: input + dataFilters)
      // não devem ler o config prévio e sobrescrever a primeira edição.
      configRef.current = withMedia;
      setConfig(withMedia);
      lastEmittedFingerprintRef.current = fingerprintComunicadoValue(serialized);
      // Live (drag/resize) atualiza eco WS/preview sem disparar autosave a cada pointermove.
      deckHistory?.setLiveComunicadoConfig(serialized);
      if (options?.persist === false) return;
      emitPersistableConfig(withMedia);
    },
    [deckHistory, emitPersistableConfig, playlistId, videoPosterAssetsRef],
  );

  /**
   * Atualiza SOMENTE as referências autoritativas do canal persistível — usado
   * quando o ACK canônico coincide com o live (applyServerConfig no-op): o
   * stage não precisa de re-render, mas a referência "já persistido" precisa
   * refletir o commit para que refresh/emissão reconheçam no-op (028).
   */
  const markAuthoritativeConfig = useCallback(
    (next: ComunicadoConfig) => {
      const withMedia = ensureComunicadoEditorMediaUrls(
        next,
        playlistId,
        videoPosterAssetsRef.current,
      );
      authoritativePersistableRef.current = JSON.stringify(
        serializeComunicadoConfig(withMedia),
      );
      authoritativeConfigRef.current = withMedia;
    },
    [playlistId, videoPosterAssetsRef],
  );

  /**
   * Canal único entregue aos hooks de mutation (027):
   * - `getStashBaseline`: baseline do último applyConfig (projeção já aplicada).
   * - `getLive`: config corrente — baseline de ops que projetam via `optimistic`.
   * - `refresh`: reemite a visão persistível após mark/settle para que um save
   *   JÁ agendado carregue baseline/canônico em vez da projeção capturada.
   *   Sem save pendente → noop: o settle do ACK nunca cria PATCH redundante do
   *   estado que a mutation acabou de persistir (churn de revisão quebraria o
   *   CAS de peers e abriria janela de supressão de evento WS estrangeiro).
   */
  const pendingMutationProjection = useMemo(
    () => ({
      registry: pendingProjectionRegistryRef.current,
      // 028: stash vazio (pós slide-switch/remote-apply) cai no último estado
      // confirmado autoritativo — baseline ausente não pode deixar a projeção
      // sem cobertura no canal persistível.
      getStashBaseline: () =>
        resolveProjectionBaseline(
          projectionBaselineStashRef.current?.prev,
          authoritativeConfigRef.current,
        ),
      getLive: () => configRef.current,
      refresh: () => {
        if (!slideId) return;
        const { resolved } = resolvePersistableConfig(
          configRef.current,
          pendingProjectionRegistryRef.current,
        );
        const key = JSON.stringify(serializeComunicadoConfig(resolved));
        const savePending = hasPendingPersistableSave?.(slideId) ?? false;
        if (key === lastScheduledPersistableRef.current) return;
        lastScheduledPersistableRef.current = key;
        if (key === authoritativePersistableRef.current) {
          /* Payload resolvido já é o estado persistido: o save pendente só
           * existia pela projeção emitida antes do mark — cancelar em vez de
           * escrever baseline redundante e bump de revisão (CAS dos peers). */
          if (savePending) cancelPendingPersistableSave?.(slideId);
          return;
        }
        if (!savePending) return;
        onChange(serializeComunicadoConfig(resolved));
      },
      // 028: edições autosave-only não-cobertas reaplicadas por cima do
      // canônico do ACK — persist:true reemite o delta ao autosave.
      applyOverlay: (merged: ComunicadoConfig) => applyConfig(merged),
      // 028: ACK de slide que o provider já não hospeda (navegação A→B) não
      // pode sobrescrever o palco/config do slide corrente.
      isCurrentSlide: (targetSlideId: string) =>
        targetSlideId === slideIdRef.current,
      // 028: commit registrado por slide — a guarda de dispatch do autosave
      // decide se um PATCH capturado pré-commit virou stale (post-commit).
      recordCommitted: (
        targetSlideId: string,
        canonical: ComunicadoConfig,
        coveredKeys: ReadonlySet<string>,
      ) => {
        committedBySlideRef.current.set(targetSlideId, {
          canonical,
          coveredKeys,
        });
      },
    }),
    [
      applyConfig,
      cancelPendingPersistableSave,
      hasPendingPersistableSave,
      onChange,
      slideId,
    ],
  );

  /**
   * Guarda de dispatch consultada pela página no ifFresh da write lane (028).
   * A decisão roda no instante do dispatch — depois que a mutation assentou —
   * então um PATCH capturado com baseline coberto que virou stale pós-commit
   * é descartado (ou reemitido como canônico+delta) em vez de reverter a
   * projeção já confirmada.
   */
  const resolvePersistableDispatch = useCallback(
    (targetSlideId: string, captured: Record<string, unknown>) => {
      const decision = resolvePersistableDispatchDecision({
        captured,
        isCurrentSlide: targetSlideId === slideIdRef.current,
        live: configRef.current,
        registry: pendingProjectionRegistryRef.current,
        committed: committedBySlideRef.current.get(targetSlideId) ?? null,
        authoritativeKey: authoritativePersistableRef.current,
        serialize: serializeComunicadoConfig,
      });
      return decision;
    },
    [],
  );

  useEffect(() => {
    if (!persistableDispatchResolverRef) return;
    persistableDispatchResolverRef.current = resolvePersistableDispatch;
    return () => {
      persistableDispatchResolverRef.current = null;
    };
  }, [persistableDispatchResolverRef, resolvePersistableDispatch]);

  // Metadado de poster chegou/mudou: re-hidrata só o estado local (posterUrl não é persistido).
  useEffect(() => {
    const hydrated = hydrateEditorVideoPosters(
      configRef.current,
      playlistId,
      videoPosterAssets,
    );
    if (hydrated === configRef.current) return;
    configRef.current = hydrated;
    setConfig(hydrated);
  }, [playlistId, videoPosterAssets]);

  /* Pins CT legados (w/h≈0): persiste frame redimensionável no modelo — chrome sozinho não basta. */
  useEffect(() => {
    const blocks = config.blocks ?? [];
    const defaultPin = defaultFrame("shape", "efficiency-pin");
    let changed = false;
    const nextBlocks = blocks.map((block) => {
      if (!isEfficiencyPinBlock(block)) return block;
      const fixed = ensureEfficiencyPinResizableFrame(block as ComunicadoShapeBlock, defaultPin);
      if (
        fixed.frame.w !== block.frame.w ||
        fixed.frame.h !== block.frame.h ||
        fixed.vertices !== block.vertices
      ) {
        changed = true;
        return fixed;
      }
      return block;
    });
    if (!changed) return;
    applyConfig({ ...configRef.current, blocks: nextBlocks });
  }, [applyConfig, config.blocks]);

  const {
    pushPast,
    commitWithHistory,
    applyServerConfig,
    undo: historyUndo,
    redo: historyRedo,
    canUndo,
    canRedo,
    resetLocalHistory,
  } = useComunicadoEditorHistory({
    configRef,
    applyConfig,
    markAuthoritativeConfig,
    deckHistory,
  });

  const {
    canvasRef,
    startDrag,
    clearDragSnapshot,
    armMultiDragSelection,
    armTapDeselect,
    cancelPendingTapDeselect,
    activeSmartGuides,
    connectionSitesPreview,
    activeGroupGesture,
  } = useComunicadoEditorDrag({
    playlistId,
    slideId,
    configRef,
    selectedIds: selection.selectedIds,
    selectedId: selection.selectedId,
    applyConfig,
    pushPast,
    deckHistory,
    snapToGridRef: stage.snapToGridRef,
    snapToObjectsRef: stage.snapToObjectsRef,
    stageGridSizePercentRef: stage.stageGridSizePercentRef,
    clearSelection: selection.clearSelection,
    getSlideAspectRatio: () =>
      designSizeRef.current.width / Math.max(designSizeRef.current.height, 1),
    resolveWriteGuard,
    onWriteCommitted,
    onWriteError,
    pendingProjection: pendingMutationProjection,
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
    const foreignRevisionChanged =
      foreignRemoteRevision !== lastForeignRemoteRevisionRef.current;
    lastForeignRemoteRevisionRef.current = foreignRemoteRevision;

    const enriched = enrichComunicadoConfigForEditor(
      value,
      playlistId,
      videoPosterAssetsRef.current,
    );
    const incomingFp = fingerprintComunicadoValue(serializeComunicadoConfig(enriched));
    const currentFp = fingerprintComunicadoValue(serializeComunicadoConfig(configRef.current));

    if (identityChanged) {
      /* O value do slide recém-carregado/selecionado É o estado persistido
       * conhecido — semeia a referência autoritativa mesmo quando o apply é
       * descartado como eco (incoming == current). Sem isso a supressão de
       * emissão canônica pós-ACK e o fallback de baseline ficavam inertes até
       * o primeiro apply autoritativo bem-sucedido. */
      authoritativePersistableRef.current = JSON.stringify(
        serializeComunicadoConfig(enriched),
      );
      authoritativeConfigRef.current = enriched;
      committedBySlideRef.current.delete(slideId ?? "");
    }

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
      // Eco rejeitado ainda pode ter perdido url no estado local (undo/snapshot).
      const ensured = ensureComunicadoEditorMediaUrls(
        configRef.current,
        playlistId,
        videoPosterAssetsRef.current,
      );
      if (ensured !== configRef.current) {
        configRef.current = ensured;
        setConfig(ensured);
      }
      return;
    }

    if (
      shouldInvalidateLocalComunicadoHistory({
        identityChanged,
        foreignRevisionChanged,
        fromHistoryRestore: forceAcceptFromHistory,
        incomingFingerprint: incomingFp,
        currentFingerprint: currentFp,
      })
    ) {
      resetLocalHistory();
    }

    setConfig(enriched);
    lastEmittedFingerprintRef.current = incomingFp;
    // Estado autoritativo (reload/conflict/reconcile) substitui marks e
    // baselines: entidades pendentes passam a ser as do servidor (027).
    pendingProjectionRegistryRef.current.clear();
    projectionBaselineStashRef.current = null;
    lastScheduledPersistableRef.current = JSON.stringify(
      serializeComunicadoConfig(enriched),
    );
    authoritativePersistableRef.current = lastScheduledPersistableRef.current;
    authoritativeConfigRef.current = enriched;
    if (identityChanged) {
      clearDragSnapshot();
      resetLocalHistory();
    }
  }, [
    value,
    playlistId,
    slideId,
    remoteRevision,
    foreignRemoteRevision,
    resetLocalHistory,
    clearDragSnapshot,
    deckHistory?.historyEpoch,
    videoPosterAssetsRef,
  ]);

  const chooseDataSourceDuplicatePolicy = useOptionalDataSourceDuplicateChoice();

  const blockActions = useComunicadoEditorBlocks({
    playlistId,
    slideId,
    configRef,
    commitWithHistory,
    applyServerConfig,
    selectedIds: selection.selectedIds,
    getActionSelectedIds: selection.getActionSelectedIds,
    selectedId: selection.selectedId,
    selected: selection.selected,
    selectedBlocks: selection.selectedBlocks,
    selectedChartPart: selection.selectedChartPart,
    selectedTablePart: selection.selectedTablePart,
    selectedTableParts: selection.selectedTableParts,
    selectedKpiPart: selection.selectedKpiPart,
    selectedInputPart: selection.selectedInputPart,
    selectedCanvasTableCell: selection.selectedCanvasTableCell,
    editingChartPart: selection.editingChartPart,
    editingKpiPart: selection.editingKpiPart,
    lastPartialTextEditSelection: selection.lastPartialTextEditSelection,
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
    requestRibbonTab: selection.requestRibbonTab,
    removeSelectedRef,
    updateBlockTextFieldsRef,
    onInputBlocksRemoved,
    getSourceResolved: (sourceId: string) => resolvedByBlockId[sourceId],
    chooseDataSourceDuplicatePolicy: chooseDataSourceDuplicatePolicy ?? undefined,
    canvasRef,
    canvasWrapRef: stage.canvasWrapRef,
    getSlideAspectRatio: () =>
      designSizeRef.current.width / Math.max(designSizeRef.current.height, 1),
    resolveWriteGuard,
    onWriteCommitted,
    onWriteError,
    pendingProjection: pendingMutationProjection,
  });

  updateBlocksRef.current = blockActions.updateBlocks;

  /* 027: undo/redo sobre entidade com mutation in-flight precisa de mutation
   * compensatória governada — o autosave serializa só o baseline confirmado,
   * então a reversão não vaza por PATCH nem é sobreposta pelo ACK. */
  const reconcilePendingProjectionRef = useRef(
    blockActions.reconcilePendingProjection,
  );
  reconcilePendingProjectionRef.current =
    blockActions.reconcilePendingProjection;
  const undo = useCallback(() => {
    historyUndo();
    reconcilePendingProjectionRef.current?.();
  }, [historyUndo]);
  const redo = useCallback(() => {
    historyRedo();
    reconcilePendingProjectionRef.current?.();
  }, [historyRedo]);

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

  const updateBlockLive = useCallback(
    (blockId: string, patch: Partial<ComunicadoBlock>) => {
      const nextBlocks = (configRef.current.blocks ?? []).map((block) =>
        block.id === blockId ? ({ ...block, ...patch } as ComunicadoBlock) : block,
      );
      applyConfig({ ...configRef.current, blocks: nextBlocks }, { persist: false });
    },
    [applyConfig],
  );

  /**
   * DataModel mutations — ops governadas (`patch_data_model` para edições
   * pontuais, `upsert_data_model` só para create/structural replace,
   * `delete_data_model`) quando há playlist+slide persistidos; fallback
   * local apenas no editor standalone. Erros da API propagam para o
   * chamador — falha de persistência nunca vira escrita local silenciosa.
   */
  const saveDataModel = useCallback(
    async (model: TvDataModel) => {
      const existing = (configRef.current.dataModels ?? []).find(
        (item) => item.id === model.id,
      );
      const next = {
        ...configRef.current,
        dataModels: [
          ...(configRef.current.dataModels ?? []).filter((item) => item.id !== model.id),
          model,
        ],
      };
      const currentSlideId = slideIdRef.current;
      if (playlistId && currentSlideId) {
        const plan = existing
          ? buildDataModelEditPlan(existing, model)
          : ({ kind: "replace" } as const);
        if (plan.kind === "noop") {
          commitWithHistory(next);
          return;
        }
        const canonical =
          plan.kind === "patch"
            ? await commitPatchDataModel({
                playlistId,
                slideId: currentSlideId,
                modelId: plan.patch.modelId,
                inputPatches: plan.patch.inputPatches,
                modelPatch: plan.patch.modelPatch,
                writeGuard: resolveWriteGuard?.() ?? undefined,
                onCommitted: onWriteCommitted,
              })
            : await commitUpsertDataModel({
                playlistId,
                slideId: currentSlideId,
                model: serializeDataModelForPreview(model),
                writeGuard: resolveWriteGuard?.() ?? undefined,
                onCommitted: onWriteCommitted,
              });
        if (!canonical) {
          throw new Error(
            "Persisted DataModel mutation returned no canonical config.",
          );
        }
        commitWithHistory(canonical);
        return;
      }
      commitWithHistory(next);
    },
    [commitWithHistory, playlistId],
  );

  const deleteDataModel = useCallback(
    async (modelId: string) => {
      const currentSlideId = slideIdRef.current;
      if (playlistId && currentSlideId) {
        const canonical = await commitDeleteDataModel({
          playlistId,
          slideId: currentSlideId,
          modelId,
          writeGuard: resolveWriteGuard?.() ?? undefined,
          onCommitted: onWriteCommitted,
        });
        if (!canonical) {
          throw new Error(
            "Persisted DataModel delete returned no canonical config.",
          );
        }
        commitWithHistory(canonical);
        return;
      }
      commitWithHistory({
        ...configRef.current,
        dataModels: (configRef.current.dataModels ?? []).filter(
          (model) => model.id !== modelId,
        ),
      });
    },
    [commitWithHistory, playlistId],
  );

  const getDataPreviewResolved = useCallback(
    (targetId: string) => resolvedByBlockId[targetId],
    [resolvedByBlockId],
  );

  const snapshotEditorConfig = useCallback(() => configRef.current, []);

  const finalizeHistoryGesture = useCallback(
    (before: ComunicadoConfig) => {
      pushPast(before);
      deckHistory?.recordBeforeChange(serializeComunicadoConfig(before));
      applyConfig(configRef.current);
    },
    [applyConfig, deckHistory, pushPast],
  );

  const getClipboardSources = useCallback(() => {
    const ids = new Set(selection.getActionSelectedIds());
    if (ids.size === 0) {
      return selection.selected ? [selection.selected] : [];
    }
    return (configRef.current.blocks ?? []).filter((block) => ids.has(block.id));
  }, [selection]);

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
  selectedCanvasTableCellRef.current = selection.selectedCanvasTableCell;

  const getClipboardSlideId = useCallback(() => slideIdRef.current ?? null, []);

  const { copySelected, cutSelected, pasteSelected, pasteFromSystemClipboard, canPaste } =
    useComunicadoEditorClipboard({
      playlistId,
      getSlideId: getClipboardSlideId,
      getSources: getClipboardSources,
      getExistingBlocks: getExistingBlocksForClipboard,
      selectBlocksByIds: selection.selectBlocksByIds,
      updateBlocks: updateBlocksForClipboard,
      removeSelected: () => removeSelectedRef.current(),
      chooseDataSourceDuplicatePolicy: chooseDataSourceDuplicatePolicy ?? undefined,
      getEditingTextId: () => editingTextIdRef.current,
      getSelectedCanvasTableCell: () => selectedCanvasTableCellRef.current,
      updateBlock: blockActions.updateBlock,
      canvasRef,
      canvasWrapRef: stage.canvasWrapRef,
    });

  const media = useComunicadoEditorMedia({
    playlistId,
    configRef,
    selectedId: selection.selectedId,
    selected: selection.selected,
    commitWithHistory,
    updateBlocks: blockActions.updateBlocks,
    setSelectedId: selection.setSelectedId,
    canvasRef,
    canvasWrapRef: stage.canvasWrapRef,
    onMediaAssetApplied: registerVideoMediaAsset,
  });

  const resolvedMaster = useMemo(
    () => resolveMasterForPreview(masterConfig, playlistId),
    [masterConfig, playlistId],
  );

  const background = config.background
    ?? (resolvedMaster?.background as ComunicadoConfig["background"] | undefined)
    ?? { type: "color", value: "#ffffff" };
  const customMasterLogo =
    resolvedMaster && typeof resolvedMaster.logo === "object" && resolvedMaster.logo
      ? (resolvedMaster.logo as {
          url?: string;
          frame?: { x?: number; y?: number; w?: number; h?: number };
          opacity?: number;
        })
      : null;
  const masterLogo = resolveStageMasterLogo({
    background: background as ComunicadoBackground,
    customLogo: customMasterLogo,
    brandThemeKey: config.brandThemeKey,
  });

  const ctxValue: ComunicadoEditorContextValue = {
    config,
    viewportProfile: viewportProfile || "1080p",
    viewportWidth: viewportWidth ?? null,
    viewportHeight: viewportHeight ?? null,
    appliedSlideId,
    blocks,
    selectedIds: selection.selectedIds,
    selectedId: selection.selectedId,
    selected: selection.selected,
    selectedBlocks: selection.selectedBlocks,
    preferGroupChildrenSelection: selection.preferGroupChildrenSelection,
    remoteSelections,
    isBlockSelected: selection.isBlockSelected,
    selectBlock: selection.selectBlock,
    selectBlocksByIds: selection.selectBlocksByIds,
    clearSelection: selection.clearSelection,
    getActionSelectedIds: selection.getActionSelectedIds,
    runWithActionSelectedIds: selection.runWithActionSelectedIds,
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
    reconcileTablePartsForVisibleKeys: selection.reconcileTablePartsForVisibleKeys,
    reconcileChartPartForSeriesFields: selection.reconcileChartPartForSeriesFields,
    editingTablePart: selection.editingTablePart,
    beginEditTablePart: selection.beginEditTablePart,
    cancelEditTablePart: selection.cancelEditTablePart,
    selectedKpiPart: selection.selectedKpiPart,
    selectedKpiParts: selection.selectedKpiParts,
    selectKpiPart: selection.selectKpiPart,
    clearKpiPartSelection: selection.clearKpiPartSelection,
    editingKpiPart: selection.editingKpiPart,
    beginEditKpiPart: selection.beginEditKpiPart,
    selectedInputPart: selection.selectedInputPart,
    selectedInputParts: selection.selectedInputParts,
    selectInputPart: selection.selectInputPart,
    clearInputPartSelection: selection.clearInputPartSelection,
    clearPartSelections: selection.clearPartSelections,
    selectedCanvasTableCell: selection.selectedCanvasTableCell,
    selectCanvasTableCell: selection.selectCanvasTableCell,
    clearCanvasTableCellSelection: selection.clearCanvasTableCellSelection,
    commitKpiPartContent: blockActions.commitKpiPartContent,
    cancelEditKpiPart: selection.cancelEditKpiPart,
    editingTextId: selection.editingTextId,
    setEditingTextId: selection.setEditingTextId,
    enterTextEdit: (blockId: string) => {
      cancelPendingTapDeselect();
      selection.enterTextEdit(blockId);
    },
    textEditSelection: selection.textEditSelection,
    lastPartialTextEditSelection: selection.lastPartialTextEditSelection,
    textFormatContextMenu: selection.textFormatContextMenu,
    openTextFormatContextMenu: selection.openTextFormatContextMenu,
    closeTextFormatContextMenu: selection.closeTextFormatContextMenu,
    textEditSelectionStyle: selection.textEditSelectionStyle,
    textEditListSelection: selection.textEditListSelection,
    textEditNamedStyleSelection: selection.textEditNamedStyleSelection,
    registerTextEditorBridge: selection.registerTextEditorBridge,
    reportTextEditSelection: selection.reportTextEditSelection,
    toggleEditingTextRunStyle: selection.toggleEditingTextRunStyle,
    applyEditingTextRunStylePatch: selection.applyEditingTextRunStylePatch,
    toggleSelectedTextListType: selection.toggleSelectedTextListType,
    applySelectedNamedTextStyle: selection.applySelectedNamedTextStyle,
    insertDataFieldAtCursor: selection.insertDataFieldAtCursor,
    applyDynamicContentSpec: selection.applyDynamicContentSpec,
    uploading: media.uploading,
    uploadProgress: media.uploadProgress,
    uploadStatusMessage: media.uploadStatusMessage,
    clearUploadStatusMessage: media.clearUploadStatusMessage,
    insertDroppedMediaFiles: media.insertDroppedMediaFiles,
    shapeMenuOpen,
    setShapeMenuOpen,
    stageDrawTool,
    setStageDrawTool,
    background,
    canvasRef,
    startDrag,
    activeGroupGesture,
    armMultiDragSelection,
    armTapDeselect,
    cancelPendingTapDeselect,
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
    expressionEditRequest,
    openExpressionEditor: openExpressionEditorCallback,
    closeExpressionEditor: closeExpressionEditorCallback,
    selectionPanelTab: selection.selectionPanelTab,
    setSelectionPanelTab: selection.setSelectionPanelTab,
    addShape: blockActions.addShape,
    addPreparedShapeBlock: blockActions.addPreparedShapeBlock,
    addIconBlock: blockActions.addIconBlock,
    groupSelected: blockActions.groupSelected,
    ungroupSelected: blockActions.ungroupSelected,
    regroupSelected: blockActions.regroupSelected,
    lastUngroupedIds: blockActions.lastUngroupedIds,
    connectSelected: blockActions.connectSelected,
    setDataFilters: blockActions.setDataFilters,
    patchInputBlock: blockActions.patchInputBlock,
    setSpeakerNotes,
    updateSelected: blockActions.updateSelected,
    updateBlock: blockActions.updateBlock,
    updateBlockLive,
    snapshotEditorConfig,
    finalizeHistoryGesture,
    updateBlocksAtomically,
    updateBlockContent: blockActions.updateBlockContent,
    updateBlockTextFields: blockActions.updateBlockTextFields,
    updateBlockLink: blockActions.updateBlockLink,
    updateSelectedStyle: blockActions.updateSelectedStyle,
    updateSelectedTextFormatStyle: blockActions.updateSelectedTextFormatStyle,
    transformSelectedTextCase: blockActions.transformSelectedTextCase,
    bumpSelectedFontSize: blockActions.bumpSelectedFontSize,
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
    publicToken: publicToken?.trim() || null,
    playlistDefaults: playlistDefaults ?? null,
    resolvedMaster,
    masterLogo,
    mediaLibraryOpen: media.mediaLibraryOpen,
    mediaLibraryTarget: media.mediaLibraryTarget,
    openMediaLibrary: media.openMediaLibrary,
    closeMediaLibrary: media.closeMediaLibrary,
    applyMediaAsset: media.applyMediaAsset,
    triggerUpload: media.triggerUpload,
    probeClipboardHasImage: media.probeClipboardHasImage,
    replaceSelectedMediaFromClipboard: media.replaceSelectedMediaFromClipboard,
    setBackgroundColor: blockActions.setBackgroundColor,
    setBackgroundFill: blockActions.setBackgroundFill,
    setBackgroundGradient: blockActions.setBackgroundGradient,
    setBackground: blockActions.setBackground,
    bindSelectedVisualBoxToData: blockActions.bindSelectedVisualBoxToData,
    insertTextDataFieldBlock: blockActions.insertTextDataFieldBlock,
    applySlideTemplate: blockActions.applySlideTemplate,
    replaceSlideNativeConfig: blockActions.replaceSlideNativeConfig,
    applySlideTheme: blockActions.applySlideTheme,
    alignSelected: blockActions.alignSelected,
    sameSizeSelected: blockActions.sameSizeSelected,
    rotateSelected: blockActions.rotateSelected,
    flipSelectedHorizontal: blockActions.flipSelectedHorizontal,
    flipSelectedVertical: blockActions.flipSelectedVertical,
    setBlocksHidden: blockActions.setBlocksHidden,
    toggleBlockHidden: blockActions.toggleBlockHidden,
    showAllBlocks: blockActions.showAllBlocks,
    hideAllBlocks: blockActions.hideAllBlocks,
    focusFrameRotationField: blockActions.focusFrameRotationField,
    stageZoom: stage.stageZoom,
    setStageZoom: stage.setStageZoom,
    setStageZoomTowardPointer: stage.setStageZoomTowardPointer,
    reportStagePointerClient: stage.reportStagePointerClient,
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
    connectionSitesPreview,
    snapToGrid: stage.snapToGrid,
    setSnapToGrid: stage.setSnapToGrid,
    snapToObjects: stage.snapToObjects,
    setSnapToObjects: stage.setSnapToObjects,
    stagePanMode: stage.stagePanMode,
    setStagePanMode: stage.setStagePanMode,
    fileInputRef: media.fileInputRef,
    handleUploadFile: media.handleUploadFile,
    uploadCustomFont: media.uploadCustomFont,
    dataPreviewLoading,
    dataPreviewLoadingProgress,
    dataPreviewLoadingLabel,
    dataPreviewError,
    isDataPreviewStale,
    staleSourceIds,
    refreshingSourceIds,
    loadingMoreSourceIds,
    refreshDataPreview,
    loadMoreDataPreview,
    getDataPreviewResolved,
    saveDataModel,
    deleteDataModel,
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
        accept="image/jpeg,image/png,image/webp,image/gif,image/svg+xml,video/mp4,video/webm"
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
