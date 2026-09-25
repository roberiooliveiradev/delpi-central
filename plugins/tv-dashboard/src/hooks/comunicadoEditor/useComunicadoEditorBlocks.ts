import {
  useCallback,
  useRef,
  useState,
  type Dispatch,
  type MutableRefObject,
  type RefObject,
  type SetStateAction,
} from "react";

import {
  chartPartAllowsDelete,
  chartPartAllowsMove,
  mergeChartPartsWithOptions,
  createBlock,
  createChartViewBlock,
  createCanvasTableBlock,
  createInputBlock,
  createConnectorBlock,
  createIconBlock,
  createKpiViewBlock,
  createShapeBlock,
  createTableViewBlock,
  canConnectBlocks,
  deleteChartPart,
  deleteKpiPart,
  deleteTablePart,
  findSharedEfficiencyPinDataSourceId,
  isDataBlockType,
  isDataSourceBlockType,
  isDataViewBlockType,
  isEfficiencyPinShapeKind,
  kpiPartAllowsDelete,
  mergeComunicadoChartOptions,
  mergeComunicadoKpiOptions,
  isComunicadoInputBlock,
  newBlockId,
  nextZIndex,
  nudgeChartPartFrame,
  parseComunicadoConfig,
  partsToChartOptions,
  partsToKpiOptions,
  pruneOrphanConnectors,
  pruneSlideDataFiltersAfterInputRemoval,
  reconcileConnectorsAfterDrag,
  resolvePreferredDataSourceId,
  resolveRemovedInputRefreshSourceIds,
  sortBlocksByZIndex,
  syncAllConnectors,
  syncTextBlockFields,
  tablePartAllowsDelete,
  upsertChartPartState,
  upsertKpiPartState,
  getChartPartState,
  getKpiPartState,
  mergeKpiPartsWithOptions,
  buildViewDataLinkPatch,
  buildCanvasTableDataLinkPatch,
  buildTextDataLinkPatch,
  isCanvasTableDataBoundBlockType,
  duplicateBlocksWithDataPolicy,
  enrichClipboardWithLinkedDataSources,
  isComunicadoVisualBoxBlock,
  isLineShapeKind,
  plainTextFromContentRuns,
  resolveBlockPasteDataPolicy,
  staticLabelFromTextBoundBlock,
  transformContentRunsCase,
  translateLineEndpoints,
  patchBackgroundUnderlay,
  type ComunicadoBackground,
  type ComunicadoBlock,
  type ComunicadoChartPartRef,
  type ComunicadoChartType,
  type ComunicadoConfig,
  type ComunicadoContentRun,
  type ComunicadoDataDisplayMode,
  type ComunicadoDataFilters,
  type ComunicadoDataResolved,
  type DataSourceDuplicatePolicy,
  type ComunicadoInputBlock,
  type ComunicadoInputPartRef,
  type ComunicadoKpiPartRef,
  type ComunicadoShapeBlock,
  type ComunicadoShapeKind,
  type ComunicadoTablePartRef,
  type ComunicadoTablePreset,
  type ComunicadoTextBlock,
  type ComunicadoTextCaseTransform,
} from "@delpi/tv-dashboard-presentation";

import {
  applyComunicadoSlideTheme,
  type ComunicadoSlideTheme,
} from "../../content/comunicadoSlideThemes";
import type {
  ComunicadoRibbonTabRequest,
  DataCatalogMode,
  DataInsertPreferredView,
  DataPanelIntent,
  OpenDataCatalogOptions,
} from "../../components/comunicadoEditorContextCore";
import { alignComunicadoBlocks, type LayoutAlignCommand } from "../../utils/comunicadoLayoutAlign";
import {
  resizeComunicadoBlocksSameSize,
  type SameSizeAxis,
} from "../../utils/comunicadoSameSize";
import { applyComunicadoBlockStylePatch } from "../../utils/applyComunicadoBlockStylePatch";
import { DATE_RANGE_PRESET_PARAM, PERIOD_DAYS_PARAM } from "../../utils/dateRangePresets";
import { renameKpiMetricFieldLabel } from "../../utils/renameKpiMetricFieldLabel";
import {
  bringForward,
  bringToFront,
  reorderLayerIds,
  sendBackward,
  sendToBack,
} from "../../utils/comunicadoLayerOrder";
import { groupBlocks, ungroupBlocks, expandSelectionWithGroups } from "../../utils/comunicadoGrouping";
import { applyGroupRotationOnce } from "../../utils/stageGroupGesture";
import {
  clampRotationDeg,
  flipHorizontalStyle,
  flipVerticalStyle,
  rotateBlockStyle,
} from "../../utils/comunicadoTransform";
import { placeBlockInViewportCenter } from "../../utils/placeBlockInViewport";
import type { TextFormatStyleSnapshot } from "../../utils/selectedTextFormatTarget";
import { buildSelectedTextFormatBlockPatch } from "../../utils/applySelectedTextFormatStyle";
import {
  resolveAppliedNumericProperty,
  sparsePropertyPatch,
  type SelectionPropertyApplyOptions,
} from "../../utils/selectionPropertyApply";
import { clampFontSize } from "@delpi/tv-dashboard-presentation";
import {
  commitAlignBlocks,
  commitCreateBlock,
  commitDuplicateBlocks,
  commitPatchNativeConfig,
  commitPresentationOps,
  commitReorderBlockZ,
} from "../../utils/presentationMutationClient";
import {
  ackUpsertBlocksWithGeneration,
  commitOpsAndApplyAck,
  createMutationGenerationGate,
} from "../../utils/mutationAckGeneration";

type Options = {
  playlistId?: string;
  slideId?: string;
  canvasRef?: RefObject<HTMLElement | null>;
  canvasWrapRef?: RefObject<HTMLElement | null>;
  configRef: MutableRefObject<ComunicadoConfig>;
  commitWithHistory: (next: ComunicadoConfig) => void;
  selectedIds: string[];
  /** Ids efetivos para mutações (override do menu de contexto ou live). */
  getActionSelectedIds: () => string[];
  selectedId: string | null;
  selected: ComunicadoBlock | null;
  selectedBlocks: ComunicadoBlock[];
  selectedChartPart: ComunicadoChartPartRef | null;
  selectedTablePart: ComunicadoTablePartRef | null;
  selectedTableParts?: ComunicadoTablePartRef[];
  selectedKpiPart: ComunicadoKpiPartRef | null;
  selectedInputPart: ComunicadoInputPartRef | null;
  selectedCanvasTableCell?: {
    blockId: string;
    cells: Array<{ row: number; col: number }>;
    focus: { row: number; col: number };
  } | null;
  editingChartPart: ComunicadoChartPartRef | null;
  editingKpiPart: ComunicadoKpiPartRef | null;
  lastPartialTextEditSelection?: {
    blockId: string;
    start: number;
    end: number;
  } | null;
  setSelectedId: (id: string | null) => void;
  selectBlocksByIds: (blockIds: string[]) => void;
  setSelectedChartPart: Dispatch<SetStateAction<ComunicadoChartPartRef | null>>;
  setEditingChartPart: Dispatch<SetStateAction<ComunicadoChartPartRef | null>>;
  setSelectedTablePart: Dispatch<SetStateAction<ComunicadoTablePartRef | null>>;
  setSelectedKpiPart: Dispatch<SetStateAction<ComunicadoKpiPartRef | null>>;
  setEditingKpiPart: Dispatch<SetStateAction<ComunicadoKpiPartRef | null>>;
  setLastDataDisplayMode: Dispatch<SetStateAction<ComunicadoDataDisplayMode>>;
  setDataPanelOpen: Dispatch<SetStateAction<boolean>>;
  setDataPanelIntent: Dispatch<SetStateAction<DataPanelIntent>>;
  setDataCatalogModalOpen: Dispatch<SetStateAction<boolean>>;
  setDataCatalogAnchor: Dispatch<SetStateAction<HTMLElement | null>>;
  setDataCatalogMode: Dispatch<SetStateAction<DataCatalogMode>>;
  setShapeMenuOpen: Dispatch<SetStateAction<boolean>>;
  setRibbonTabRequest: Dispatch<SetStateAction<ComunicadoRibbonTabRequest | null>>;
  requestRibbonTab?: (tab: ComunicadoRibbonTabRequest) => void;
  /** Preenchido pelo Provider para o clipboard. */
  removeSelectedRef: MutableRefObject<() => void>;
  /** Preenchido pelo Provider para o bridge de texto na seleção. */
  updateBlockTextFieldsRef: MutableRefObject<
    (blockId: string, fields: Pick<ComunicadoTextBlock, "content" | "contentRuns">) => void
  >;
  /** Após excluir blocos `input`, recalcular preview das fontes afetadas. */
  onInputBlocksRemoved?: (payload: { sourceIds: string[] }) => void;
  /** Resolved atual da fonte (preview) — para materializar projection no link. */
  getSourceResolved?: (sourceId: string) => ComunicadoDataResolved | undefined;
  chooseDataSourceDuplicatePolicy?: () => Promise<DataSourceDuplicatePolicy | null>;
  /** Largura/altura do palco (design) — órbita de rotação em grupo. */
  getSlideAspectRatio?: () => number;
};

/**
 * Mutações de blocos (add/update/remove/group/layer/nudge/align/theme) via histórico.
 */
export function useComunicadoEditorBlocks({
  playlistId,
  slideId,
  configRef,
  commitWithHistory,
  selectedIds,
  getActionSelectedIds,
  selectedId,
  selected,
  selectedBlocks,
  selectedChartPart,
  selectedTablePart,
  selectedTableParts = [],
  selectedKpiPart,
  selectedInputPart,
  selectedCanvasTableCell = null,
  editingChartPart,
  editingKpiPart,
  lastPartialTextEditSelection = null,
  setSelectedId,
  selectBlocksByIds,
  setSelectedChartPart,
  setEditingChartPart,
  setSelectedTablePart,
  setSelectedKpiPart,
  setEditingKpiPart,
  setLastDataDisplayMode,
  setDataPanelOpen,
  setDataPanelIntent,
  setDataCatalogModalOpen,
  setDataCatalogAnchor,
  setDataCatalogMode,
  setShapeMenuOpen,
  setRibbonTabRequest,
  requestRibbonTab,
  removeSelectedRef,
  updateBlockTextFieldsRef,
  onInputBlocksRemoved,
  getSourceResolved,
  chooseDataSourceDuplicatePolicy,
  canvasRef,
  canvasWrapRef,
  getSlideAspectRatio,
}: Options) {
  const [lastUngroupedIds, setLastUngroupedIds] = useState<string[]>([]);
  const getSlideAspectRatioRef = useRef(getSlideAspectRatio ?? (() => 1));
  getSlideAspectRatioRef.current = getSlideAspectRatio ?? (() => 1);
  const mutationGateRef = useRef(createMutationGenerationGate());

  const placeInserted = useCallback(
    <T extends ComunicadoBlock>(block: T): T =>
      placeBlockInViewportCenter(block, canvasRef?.current, canvasWrapRef?.current),
    [canvasRef, canvasWrapRef],
  );

  const updateBlocks = useCallback(
    (
      nextBlocks: ComunicadoBlock[],
      configPatch?: Pick<ComunicadoConfig, "groupTransforms">,
    ) => {
      const withConnectors = syncAllConnectors(pruneOrphanConnectors(nextBlocks));
      commitWithHistory({ ...configRef.current, ...configPatch, blocks: withConnectors });
    },
    [commitWithHistory, configRef],
  );

  const ackBlocksMutation = useCallback(
    (blocks: ComunicadoBlock[]) => {
      if (!playlistId || !slideId || blocks.length === 0) return;
      void ackUpsertBlocksWithGeneration({
        playlistId,
        slideId,
        blocks: blocks as unknown as Record<string, unknown>[],
        gate: mutationGateRef.current,
        applyAck: (canonical) => {
          commitWithHistory(canonical);
        },
      });
    },
    [commitWithHistory, playlistId, slideId],
  );

  /**
   * Inserção: commit antes da seleção.
   * `selectBlocksByIds` / `setSelectedId` resolvem contra `configRef` —
   * selecionar antes do commit deixa o id fora do ref e a seleção vazia.
   * Ack PresentationMutation so BE owns the inserted block defaults/geometry.
   */
  const commitAndSelectInserted = useCallback(
    (
      nextBlocks: ComunicadoBlock[],
      selectIds: string[],
      configPatch?: Pick<ComunicadoConfig, "groupTransforms">,
    ) => {
      updateBlocks(nextBlocks, configPatch);
      selectBlocksByIds(selectIds);
      ackBlocksMutation(nextBlocks.filter((b) => selectIds.includes(b.id)));
    },
    [ackBlocksMutation, selectBlocksByIds, updateBlocks],
  );

  const connectSelected = useCallback(() => {
    if (selectedIds.length !== 2) return;
    const blocks = configRef.current.blocks ?? [];
    const [idA, idB] = selectedIds;
    const a = blocks.find((block) => block.id === idA);
    const b = blocks.find((block) => block.id === idB);
    if (!a || !b || !canConnectBlocks(a, b)) return;
    const connector = createConnectorBlock(a, b, { zIndex: nextZIndex(blocks) });
    commitAndSelectInserted([...blocks, connector], [connector.id]);
  }, [commitAndSelectInserted, configRef, selectedIds]);

  const addBlock = useCallback(
    (type: ComunicadoBlock["type"]) => {
      const content =
        type === "heading" ? "Novo título" : type === "text" ? "Texto" : "";
      const applyLocal = () => {
        let block = createBlock(type, content);
        block.style = { ...block.style, zIndex: nextZIndex(configRef.current.blocks ?? []) };
        block = placeInserted(block);
        commitAndSelectInserted([...(configRef.current.blocks ?? []), block], [block.id]);
        return block;
      };

      if (!playlistId || !slideId) {
        applyLocal();
        return;
      }

      const blockId = newBlockId();
      void commitCreateBlock({
        playlistId,
        slideId,
        type,
        blockId,
        content: content || undefined,
      })
        .then((canonical) => {
          if (!canonical) {
            applyLocal();
            return;
          }
          const created = (canonical.blocks ?? []).find((b) => b.id === blockId);
          if (!created) {
            applyLocal();
            return;
          }
          let placed = placeInserted({
            ...created,
            style: {
              ...created.style,
              zIndex: nextZIndex(configRef.current.blocks ?? []),
            },
          } as ComunicadoBlock);
          // Persist viewport placement as geometry authority ack.
          void ackUpsertBlocksWithGeneration({
            playlistId,
            slideId,
            blocks: [placed as unknown as Record<string, unknown>],
            gate: mutationGateRef.current,
            applyAck: (canonical) => {
              commitWithHistory(canonical);
            },
          });
          commitAndSelectInserted([...(configRef.current.blocks ?? []), placed], [placed.id]);
        })
        .catch(() => {
          applyLocal();
        });
    },
    [commitAndSelectInserted, commitWithHistory, configRef, placeInserted, playlistId, slideId],
  );

  const addDataBlock = useCallback(
    (block: ComunicadoBlock) => {
      let withZ = {
        ...block,
        style: { ...block.style, zIndex: nextZIndex(configRef.current.blocks ?? []) },
      };
      if (isDataBlockType(withZ.type) && "dataBinding" in withZ) {
        const mode = withZ.dataBinding.displayMode;
        if (mode && mode !== "auto") {
          setLastDataDisplayMode(mode);
        }
      }
      withZ = placeInserted(withZ);
      commitAndSelectInserted([...(configRef.current.blocks ?? []), withZ], [withZ.id]);
    },
    [commitAndSelectInserted, configRef, placeInserted, setLastDataDisplayMode],
  );

  const linkViewToSource = useCallback(
    (
      block: ComunicadoBlock,
      sourceId: string,
    ): ComunicadoBlock => {
      if (isComunicadoVisualBoxBlock(block)) {
        const resolved = getSourceResolved?.(sourceId);
        const patch = buildTextDataLinkPatch({
          dataSourceId: sourceId,
          resolved,
          existing: block.textProjection,
          staticContent: staticLabelFromTextBoundBlock(block),
        });
        return { ...block, ...patch } as ComunicadoBlock;
      }
      if (isCanvasTableDataBoundBlockType(block.type) && block.type === "canvas_table") {
        const resolved = getSourceResolved?.(sourceId);
        const patch = buildCanvasTableDataLinkPatch({
          dataSourceId: sourceId,
          resolved,
          existingCells: block.cells,
        });
        return { ...block, ...patch } as ComunicadoBlock;
      }
      if (!isDataViewBlockType(block.type)) {
        return { ...block, dataSourceId: sourceId } as ComunicadoBlock;
      }
      const resolved = getSourceResolved?.(sourceId);
      const patch = buildViewDataLinkPatch({
        viewType: block.type,
        dataSourceId: sourceId,
        resolved,
        currentFrame: block.frame,
        existing: {
          kpiProjection: "kpiProjection" in block ? block.kpiProjection : undefined,
          chartProjection: "chartProjection" in block ? block.chartProjection : undefined,
          tableProjection: "tableProjection" in block ? block.tableProjection : undefined,
        },
        chartType: block.type === "chart_view" ? block.chartType : undefined,
      });
      return { ...block, ...patch } as ComunicadoBlock;
    },
    [getSourceResolved],
  );

  const addChartViewBlock = useCallback(
    (chartType: ComunicadoChartType) => {
      let block = createChartViewBlock(chartType);
      const sourceId = resolvePreferredDataSourceId(configRef.current.blocks ?? [], selectedId);
      if (sourceId) {
        block = linkViewToSource(block, sourceId);
      }
      block.style = { ...block.style, zIndex: nextZIndex(configRef.current.blocks ?? []) };
      block = placeInserted(block);
      commitAndSelectInserted([...(configRef.current.blocks ?? []), block], [block.id]);
    },
    [commitAndSelectInserted, configRef, linkViewToSource, placeInserted, selectedId],
  );

  const addTableViewBlock = useCallback(
    (rows: number, cols: number, preset: ComunicadoTablePreset) => {
      let block = createTableViewBlock(rows, cols, preset);
      const sourceId = resolvePreferredDataSourceId(configRef.current.blocks ?? [], selectedId);
      if (sourceId) {
        block = linkViewToSource(block, sourceId);
      }
      block.style = { ...block.style, zIndex: nextZIndex(configRef.current.blocks ?? []) };
      block = placeInserted(block);
      commitAndSelectInserted([...(configRef.current.blocks ?? []), block], [block.id]);
    },
    [commitAndSelectInserted, configRef, linkViewToSource, placeInserted, selectedId],
  );

  const addCanvasTableBlock = useCallback(
    (rows = 3, cols = 3) => {
      let block = createCanvasTableBlock(rows, cols);
      block.style = { ...block.style, zIndex: nextZIndex(configRef.current.blocks ?? []) };
      block = placeInserted(block);
      commitAndSelectInserted([...(configRef.current.blocks ?? []), block], [block.id]);
    },
    [commitAndSelectInserted, configRef, placeInserted],
  );

  const addInputBlock = useCallback(() => {
    let block = createInputBlock({ targetScope: "slide", paramKey: "" });
    block.style = { ...block.style, zIndex: nextZIndex(configRef.current.blocks ?? []) };
    block = placeInserted(block);
    commitAndSelectInserted([...(configRef.current.blocks ?? []), block], [block.id]);
  }, [commitAndSelectInserted, configRef, placeInserted]);

  const addKpiViewBlock = useCallback(() => {
    let block = createKpiViewBlock();
    const sourceId = resolvePreferredDataSourceId(configRef.current.blocks ?? [], selectedId);
    if (sourceId) {
      block = linkViewToSource(block, sourceId);
    }
    block.style = { ...block.style, zIndex: nextZIndex(configRef.current.blocks ?? []) };
    block = placeInserted(block);
    commitAndSelectInserted([...(configRef.current.blocks ?? []), block], [block.id]);
  }, [commitAndSelectInserted, configRef, linkViewToSource, placeInserted, selectedId]);

  const addDataSourceBlock = useCallback(
    (block: ComunicadoBlock, options?: { preferredView?: DataInsertPreferredView }) => {
      const selectedBlock = configRef.current.blocks?.find((item) => item.id === selectedId);
      let nextBlocks = [...(configRef.current.blocks ?? [])];
      let withZ: ComunicadoBlock = {
        ...block,
        style: { ...block.style, zIndex: nextZIndex(nextBlocks) },
      };
      let linkedExistingView = false;
      if (
        selectedBlock &&
        isDataViewBlockType(selectedBlock.type) &&
        !("dataSourceId" in selectedBlock && selectedBlock.dataSourceId?.trim())
      ) {
        linkedExistingView = true;
      } else if (
        selectedBlock &&
        isComunicadoVisualBoxBlock(selectedBlock) &&
        !selectedBlock.dataSourceId?.trim()
      ) {
        linkedExistingView = true;
      }
      // Com visual novo: centraliza o visual; chip da fonte fica no canto superior esquerdo do visual.
      // Sem visual: centraliza a fonte. Ligando a view existente: só adiciona a fonte no centro.
      if (!linkedExistingView && options?.preferredView) {
        let viewBlock: ComunicadoBlock;
        if (options.preferredView === "series") {
          viewBlock = createChartViewBlock("line");
        } else if (options.preferredView === "table") {
          viewBlock = createTableViewBlock(6, 5, "grid");
        } else if (options.preferredView === "text") {
          viewBlock = createBlock("text", "Texto");
        } else if (options.preferredView === "shape") {
          viewBlock = createShapeBlock("rectangle");
        } else {
          viewBlock = createKpiViewBlock();
        }
        viewBlock = linkViewToSource(viewBlock, withZ.id);
        viewBlock.style = {
          ...viewBlock.style,
          zIndex: nextZIndex([...nextBlocks, withZ]),
        };
        viewBlock = placeInserted(viewBlock);
        withZ = {
          ...withZ,
          frame: {
            ...withZ.frame,
            x: Math.max(0, Math.min(100 - withZ.frame.w, viewBlock.frame.x)),
            y: Math.max(0, Math.min(100 - withZ.frame.h, Math.max(0, viewBlock.frame.y - withZ.frame.h - 1))),
          },
        };
        nextBlocks = [...nextBlocks, withZ, viewBlock];
        if (isDataBlockType(withZ.type) && "dataBinding" in withZ) {
          const mode = withZ.dataBinding.displayMode;
          if (mode && mode !== "auto") {
            setLastDataDisplayMode(mode);
          }
        }
        setDataPanelOpen(false);
        commitAndSelectInserted(nextBlocks, [viewBlock.id]);
        return;
      }

      withZ = placeInserted(withZ);
      nextBlocks = [...nextBlocks, withZ];
      if (linkedExistingView && selectedBlock) {
        nextBlocks = nextBlocks.map((item) =>
          item.id === selectedBlock.id ? linkViewToSource(item, withZ.id) : item,
        );
      }
      if (isDataBlockType(withZ.type) && "dataBinding" in withZ) {
        const mode = withZ.dataBinding.displayMode;
        if (mode && mode !== "auto") {
          setLastDataDisplayMode(mode);
        }
      }
      setDataPanelOpen(false);
      commitAndSelectInserted(nextBlocks, [withZ.id]);
    },
    [
      commitAndSelectInserted,
      configRef,
      linkViewToSource,
      placeInserted,
      selectedId,
      setDataPanelOpen,
      setLastDataDisplayMode,
    ],
  );

  const openDataPanel = useCallback(() => {
    setDataPanelIntent("binding");
    setDataPanelOpen(true);
    setRibbonTabRequest("data");
  }, [setDataPanelIntent, setDataPanelOpen, setRibbonTabRequest]);

  const openDataCatalog = useCallback(
    (mode: DataCatalogMode = "insert", options?: OpenDataCatalogOptions) => {
      setDataCatalogMode(mode);
      setDataCatalogAnchor(options?.anchor ?? null);
      setDataCatalogModalOpen(true);
    },
    [setDataCatalogAnchor, setDataCatalogMode, setDataCatalogModalOpen],
  );

  const setDataFilters = useCallback(
    (filters: ComunicadoDataFilters | undefined) => {
      commitWithHistory({
        ...configRef.current,
        dataFilters: filters,
        version: Math.max(configRef.current.version ?? 3, 4),
      });
    },
    [commitWithHistory, configRef],
  );

  /**
   * Atualiza bloco `input` e, se alvo = slide, espelha defaultValue em dataFilters
   * no mesmo commit (evita corrida updateSelected → setDataFilters).
   * Trocar/limpar paramKey remove a chave antiga de dataFilters.
   */
  const patchInputBlock = useCallback(
    (
      blockId: string,
      inputPatch: Partial<ComunicadoInputBlock["input"]>,
      filterBundle?: Record<string, string | number | boolean | null | undefined>,
    ) => {
      const current = configRef.current;
      let nextFilters = current.dataFilters;
      const nextBlocks = (current.blocks ?? []).map((item) => {
        if (item.id !== blockId || item.type !== "input") return item;
        const prevKey = String(item.input?.paramKey || "").trim();
        const nextInput = { ...item.input, ...inputPatch };
        const nextKey = String(nextInput.paramKey || "").trim();
        const scope = nextInput.targetScope === "sources" ? "sources" : "slide";
        if (scope === "slide") {
          const filters = { ...(current.dataFilters ?? {}) };
          if (prevKey && prevKey !== nextKey) {
            delete filters[prevKey];
            if (prevKey === DATE_RANGE_PRESET_PARAM || nextKey === DATE_RANGE_PRESET_PARAM) {
              delete filters[PERIOD_DAYS_PARAM];
            }
          }
          if (nextKey) {
            const value = nextInput.defaultValue;
            if (value === undefined || value === null || value === "") {
              delete filters[nextKey];
            } else {
              filters[nextKey] = value;
            }
          }
          if (filterBundle) {
            for (const [key, value] of Object.entries(filterBundle)) {
              if (value === undefined || value === null || value === "") delete filters[key];
              else filters[key] = value;
            }
          }
          nextFilters = Object.keys(filters).length > 0 ? filters : undefined;
        }
        return { ...item, input: nextInput } as ComunicadoBlock;
      });
      commitWithHistory({
        ...current,
        blocks: nextBlocks,
        dataFilters: nextFilters,
        version: Math.max(current.version ?? 3, 4),
      });
    },
    [commitWithHistory, configRef],
  );

  const addShape = useCallback(
    (shape: ComunicadoShapeKind) => {
      let block = createShapeBlock(shape);
      block.style = { ...block.style, zIndex: nextZIndex(configRef.current.blocks ?? []) };
      /* Pin CT: reutiliza a fonte de eficiência já no slide (só o CT muda por pin). */
      if (block.type === "shape" && isEfficiencyPinShapeKind(shape)) {
        const sharedId = findSharedEfficiencyPinDataSourceId(configRef.current.blocks ?? []);
        if (sharedId) {
          block = { ...block, dataSourceId: sharedId };
        }
      }
      block = placeInserted(block);
      setShapeMenuOpen(false);
      setRibbonTabRequest("element");
      commitAndSelectInserted([...(configRef.current.blocks ?? []), block], [block.id]);
    },
    [
      commitAndSelectInserted,
      configRef,
      placeInserted,
      setRibbonTabRequest,
      setShapeMenuOpen,
    ],
  );

  /** Insere bloco shape já posicionado (desenho no palco — linhas/conectores). */
  const addPreparedShapeBlock = useCallback(
    (block: ComunicadoShapeBlock) => {
      const next: ComunicadoShapeBlock = {
        ...block,
        style: {
          ...block.style,
          zIndex: block.style?.zIndex ?? nextZIndex(configRef.current.blocks ?? []),
        },
      };
      setRibbonTabRequest("element");
      commitAndSelectInserted([...(configRef.current.blocks ?? []), next], [next.id]);
    },
    [commitAndSelectInserted, configRef, setRibbonTabRequest],
  );

  const addIconBlock = useCallback(
    (iconName: string) => {
      let block = createIconBlock(iconName);
      block.style = { ...block.style, zIndex: nextZIndex(configRef.current.blocks ?? []) };
      block = placeInserted(block);
      commitAndSelectInserted([...(configRef.current.blocks ?? []), block], [block.id]);
    },
    [commitAndSelectInserted, configRef, placeInserted],
  );

  const groupSelected = useCallback(() => {
    const ids = getActionSelectedIds();
    if (ids.length < 2) return;
    const nextBlocks = groupBlocks(configRef.current.blocks ?? [], ids);
    const groupId = nextBlocks.find((block) => ids.includes(block.id))?.groupId;
    updateBlocks(
      nextBlocks,
      groupId
        ? {
            groupTransforms: {
              ...(configRef.current.groupTransforms ?? {}),
              [groupId]: { rotation: 0 },
            },
          }
        : undefined,
    );
    setLastUngroupedIds([]);
  }, [configRef, getActionSelectedIds, updateBlocks]);

  const ungroupSelected = useCallback(() => {
    const ids = getActionSelectedIds();
    if (ids.length === 0) return;
    const current = configRef.current.blocks ?? [];
    const expanded = expandSelectionWithGroups(current, ids);
    const removedGroupIds = new Set(
      current
        .filter((block) => expanded.includes(block.id))
        .map((block) => block.groupId)
        .filter((id): id is string => Boolean(id)),
    );
    const members = expanded.filter((id) => Boolean(current.find((block) => block.id === id)?.groupId));
    if (members.length >= 2) setLastUngroupedIds(members);
    const groupTransforms = { ...(configRef.current.groupTransforms ?? {}) };
    for (const groupId of removedGroupIds) delete groupTransforms[groupId];
    updateBlocks(ungroupBlocks(current, expanded), {
      groupTransforms:
        Object.keys(groupTransforms).length > 0 ? groupTransforms : undefined,
    });
  }, [configRef, getActionSelectedIds, updateBlocks]);

  const regroupSelected = useCallback(() => {
    const current = configRef.current.blocks ?? [];
    const present = new Set(current.map((block) => block.id));
    const ids = lastUngroupedIds.filter((id) => present.has(id));
    if (ids.length < 2) return;
    const nextBlocks = groupBlocks(current, ids);
    const groupId = nextBlocks.find((block) => ids.includes(block.id))?.groupId;
    updateBlocks(
      nextBlocks,
      groupId
        ? {
            groupTransforms: {
              ...(configRef.current.groupTransforms ?? {}),
              [groupId]: { rotation: 0 },
            },
          }
        : undefined,
    );
    selectBlocksByIds(ids);
    setLastUngroupedIds([]);
  }, [configRef, lastUngroupedIds, selectBlocksByIds, updateBlocks]);

  const updateSelected = useCallback(
    (patch: Partial<ComunicadoBlock>) => {
      if (selectedIds.length === 0) return;
      const idSet = new Set(selectedIds);
      const nextBlocks = (configRef.current.blocks ?? []).map((block) =>
        idSet.has(block.id) ? ({ ...block, ...patch } as ComunicadoBlock) : block,
      );
      updateBlocks(nextBlocks);
      ackBlocksMutation(nextBlocks.filter((b) => idSet.has(b.id)));
    },
    [ackBlocksMutation, configRef, selectedIds, updateBlocks],
  );

  const updateBlock = useCallback(
    (blockId: string, patch: Partial<ComunicadoBlock>) => {
      const nextBlocks = (configRef.current.blocks ?? []).map((block) =>
        block.id === blockId ? ({ ...block, ...patch } as ComunicadoBlock) : block,
      );
      updateBlocks(nextBlocks);
      const patched = nextBlocks.find((b) => b.id === blockId);
      if (patched) ackBlocksMutation([patched]);
    },
    [ackBlocksMutation, configRef, updateBlocks],
  );

  const commitChartPartContent = useCallback(
    (
      content: string,
      meta?: { contentRuns?: import("@delpi/plugin-ui/index").DeckContentRun[] },
    ) => {
      const part = editingChartPart;
      const blockId = selectedIds[selectedIds.length - 1] ?? null;
      setEditingChartPart(null);
      if (!part || !blockId) return;
      const block = configRef.current.blocks?.find((item) => item.id === blockId);
      if (!block || block.type !== "chart_view") return;

      const nextParts = upsertChartPartState(block.chartParts, part, {
        content,
        contentRuns: meta?.contentRuns,
        visible: true,
      });
      const nextOptions = mergeComunicadoChartOptions({
        ...block.chartOptions,
        ...partsToChartOptions(nextParts),
      });
      if (part.kind === "title") {
        nextOptions.title = content;
        nextOptions.showTitle = true;
      } else if (part.kind === "legend" || part.kind === "series") {
        nextOptions.seriesName = content;
      } else if (part.kind === "axisTitle" && part.axis === "x") {
        nextOptions.xAxisTitle = content;
        nextOptions.showXAxisTitle = true;
      } else if (part.kind === "axisTitle" && part.axis === "y") {
        nextOptions.yAxisTitle = content;
        nextOptions.showYAxisTitle = true;
      }
      updateBlock(blockId, {
        chartParts: mergeChartPartsWithOptions(nextParts, nextOptions),
        chartOptions: nextOptions,
      } as Partial<ComunicadoBlock>);
    },
    [configRef, editingChartPart, selectedIds, setEditingChartPart, updateBlock],
  );

  const commitKpiPartContent = useCallback(
    (
      content: string,
      meta?: { contentRuns?: import("@delpi/plugin-ui/index").DeckContentRun[] },
    ) => {
      const part = editingKpiPart;
      const blockId = selectedIds[selectedIds.length - 1] ?? null;
      setEditingKpiPart(null);
      if (!part || !blockId) return;
      const block = configRef.current.blocks?.find((item) => item.id === blockId);
      if (!block || block.type !== "kpi_view") return;

      const metricField =
        part.kind === "metricCard"
          ? part.field
          : part.kind === "title"
            ? block.kpiProjection?.metrics?.[0]?.field ??
              block.resolved?.kpiMetrics?.[0]?.field
            : undefined;
      const renameViaSource =
        Boolean(metricField) &&
        Boolean(block.dataSourceId?.trim()) &&
        (part.kind === "metricCard" ||
          (part.kind === "title" && !block.kpiOptions?.title?.trim()));

      if (renameViaSource && metricField) {
        const { sourcePatch, kpiProjection } = renameKpiMetricFieldLabel({
          blocks: configRef.current.blocks ?? [],
          kpiBlock: block,
          field: metricField,
          label: content,
        });
        if (sourcePatch) {
          updateBlock(sourcePatch.id, {
            fieldLabels: sourcePatch.fieldLabels,
          } as Partial<ComunicadoBlock>);
        }
        const viewPatch: Partial<ComunicadoBlock> = {};
        if (kpiProjection) {
          (viewPatch as ComunicadoBlock & { kpiProjection?: typeof kpiProjection }).kpiProjection =
            kpiProjection;
        }
        if (part.kind === "title") {
          viewPatch.kpiOptions = mergeComunicadoKpiOptions({
            ...block.kpiOptions,
            title: undefined,
          });
        }
        if (Object.keys(viewPatch).length > 0) {
          updateBlock(blockId, viewPatch);
        }
        return;
      }

      const nextParts = upsertKpiPartState(block.kpiParts, part, {
        content,
        contentRuns: meta?.contentRuns,
        visible: true,
      });
      const nextOptions = mergeComunicadoKpiOptions({
        ...block.kpiOptions,
        ...partsToKpiOptions(nextParts),
      });
      if (part.kind === "title") {
        nextOptions.title = content.trim() || undefined;
      } else if (part.kind === "hint") {
        nextOptions.subtitle = content.trim() || undefined;
      }
      updateBlock(blockId, {
        kpiParts: nextParts,
        kpiOptions: nextOptions,
      } as Partial<ComunicadoBlock>);
    },
    [configRef, editingKpiPart, selectedIds, setEditingKpiPart, updateBlock],
  );

  const updateBlockTextFields = useCallback(
    (blockId: string, fields: Pick<ComunicadoTextBlock, "content" | "contentRuns">) => {
      const textFields = syncTextBlockFields(fields.content, fields.contentRuns);
      const nextBlocks = (configRef.current.blocks ?? []).map((block) => {
        if (block.id !== blockId) return block;
        if (block.type === "heading" || block.type === "text") {
          return { ...block, ...textFields } as ComunicadoBlock;
        }
        if (block.type === "shape") {
          return {
            ...block,
            content: textFields.content,
            contentRuns: textFields.contentRuns,
          } as ComunicadoBlock;
        }
        return block;
      });
      updateBlocks(nextBlocks);
    },
    [configRef, updateBlocks],
  );
  updateBlockTextFieldsRef.current = updateBlockTextFields;

  const updateBlockContent = useCallback(
    (blockId: string, content: string) => {
      updateBlockTextFields(blockId, syncTextBlockFields(content, undefined));
    },
    [updateBlockTextFields],
  );

  const updateBlockLink = useCallback(
    (blockId: string, href: string | undefined) => {
      const nextBlocks = (configRef.current.blocks ?? []).map((block) => {
        if (block.id !== blockId) return block;
        if (
          block.type !== "heading" &&
          block.type !== "text" &&
          block.type !== "image" &&
          block.type !== "video" &&
          block.type !== "shape" &&
          block.type !== "icon"
        ) {
          return block;
        }
        return {
          ...block,
          href: href?.trim() || undefined,
          linkTarget: href?.trim() ? "_blank" : undefined,
        } as ComunicadoBlock;
      });
      updateBlocks(nextBlocks);
    },
    [configRef, updateBlocks],
  );

  const updateSelectedStyle = useCallback(
    (
      patch: NonNullable<ComunicadoBlock["style"]>,
      applyOptions?: SelectionPropertyApplyOptions,
    ) => {
      const targets = selectedBlocks.length > 0 ? selectedBlocks : selected ? [selected] : [];
      if (targets.length === 0) return;
      const idSet = new Set(targets.map((block) => block.id));
      const nextBlocks = (configRef.current.blocks ?? []).map((block) => {
        if (!idSet.has(block.id)) return block;
        const currentSize =
          typeof block.style?.fontSize === "number" && block.style.fontSize > 0
            ? block.style.fontSize
            : block.type === "heading"
              ? 56
              : 28;
        const nextFontSize = resolveAppliedNumericProperty({
          current: currentSize,
          value: typeof patch.fontSize === "number" ? patch.fontSize : undefined,
          mode: applyOptions?.fontSizeMode,
          delta: applyOptions?.fontSizeDelta,
          clamp: clampFontSize,
        });
        const effective = sparsePropertyPatch({
          ...(patch as Record<string, unknown>),
          ...(nextFontSize != null
            ? { fontSize: nextFontSize }
            : applyOptions?.fontSizeMode === "delta"
              ? { fontSize: undefined }
              : {}),
        }) as NonNullable<ComunicadoBlock["style"]>;
        return applyComunicadoBlockStylePatch(block, effective, {
          selectedInputPart: block.type === "input" ? selectedInputPart : null,
        });
      });
      updateBlocks(nextBlocks);
      ackBlocksMutation(nextBlocks.filter((b) => idSet.has(b.id)));
    },
    [ackBlocksMutation, configRef, selected, selectedBlocks, selectedInputPart, updateBlocks],
  );

  /** Tipografia da ribbon Formatar — bloco text/heading/shape ou tipografia de complexo/parte. */
  const updateSelectedTextFormatStyle = useCallback(
    (patch: TextFormatStyleSnapshot, applyOptions?: SelectionPropertyApplyOptions) => {
      if (!selected) return;

      const complexPatch = buildSelectedTextFormatBlockPatch({
        selected,
        patch,
        selectedKpiPart,
        selectedChartPart,
        selectedTablePart,
        selectedTableParts,
        selectedInputPart,
        selectedCanvasTableCell,
        applyOptions,
      });
      if (complexPatch) {
        updateSelected(complexPatch);
        return;
      }

      updateSelectedStyle(patch as NonNullable<ComunicadoBlock["style"]>, applyOptions);
    },
    [
      selected,
      selectedCanvasTableCell,
      selectedChartPart,
      selectedInputPart,
      selectedKpiPart,
      selectedTablePart,
      selectedTableParts,
      updateSelected,
      updateSelectedStyle,
    ],
  );

  /**
   * Mutação de conteúdo (maiúsculas) — BE `transform_text_case` com range opcional.
   * Authoring runs only (nunca display projection). dataRef permanece atômico.
   */
  const transformSelectedTextCase = useCallback(
    (mode: ComunicadoTextCaseTransform) => {
      const targets =
        selectedBlocks.length > 0
          ? selectedBlocks.filter((b) => isComunicadoVisualBoxBlock(b))
          : selected && isComunicadoVisualBoxBlock(selected)
            ? [selected]
            : [];
      if (targets.length === 0) return;

      const partial =
        lastPartialTextEditSelection &&
        targets.some((b) => b.id === lastPartialTextEditSelection.blockId) &&
        lastPartialTextEditSelection.end > lastPartialTextEditSelection.start
          ? lastPartialTextEditSelection
          : null;

      const authoringRuns = (block: ComunicadoBlock) => {
        if (!isComunicadoVisualBoxBlock(block)) return [] as ComunicadoContentRun[];
        if (block.contentRuns?.length) return block.contentRuns;
        const text = block.content ?? "";
        return text ? [{ text }] : [];
      };

      if (playlistId && slideId) {
        const ops =
          partial && targets.length === 1
            ? [
                {
                  op: "transform_text_case",
                  blockId: targets[0].id,
                  mode,
                  start: partial.start,
                  end: partial.end,
                },
              ]
            : targets.map((block) => ({
                op: "transform_text_case",
                blockId: block.id,
                mode,
              }));

        void commitOpsAndApplyAck({
          playlistId,
          slideId,
          ops,
          gate: mutationGateRef.current,
          applyAck: (canonical) => {
            commitWithHistory(canonical);
          },
          optimistic: () => {
            const nextBlocks = (configRef.current.blocks ?? []).map((block) => {
              if (!targets.some((t) => t.id === block.id)) return block;
              if (!isComunicadoVisualBoxBlock(block)) return block;
              const runs = authoringRuns(block);
              const nextRuns =
                partial && block.id === partial.blockId
                  ? transformContentRunsCase(runs, mode, {
                      start: partial.start,
                      end: partial.end,
                    })
                  : transformContentRunsCase(runs, mode);
              return {
                ...block,
                content: plainTextFromContentRuns(nextRuns),
                contentRuns: nextRuns,
              } as ComunicadoBlock;
            });
            updateBlocks(nextBlocks);
          },
        }).then((canonical) => {
          if (canonical) return;
          // Network null: keep optimistic local already applied via updateBlocks.
        });
        return;
      }

      const nextBlocks = (configRef.current.blocks ?? []).map((block) => {
        if (!targets.some((t) => t.id === block.id)) return block;
        if (!isComunicadoVisualBoxBlock(block)) return block;
        const runs = authoringRuns(block);
        const nextRuns =
          partial && block.id === partial.blockId
            ? transformContentRunsCase(runs, mode, {
                start: partial.start,
                end: partial.end,
              })
            : transformContentRunsCase(runs, mode);
        return {
          ...block,
          content: plainTextFromContentRuns(nextRuns),
          contentRuns: nextRuns,
        } as ComunicadoBlock;
      });
      updateBlocks(nextBlocks);
    },
    [
      commitWithHistory,
      configRef,
      lastPartialTextEditSelection,
      playlistId,
      selected,
      selectedBlocks,
      slideId,
      updateBlocks,
    ],
  );

  const bumpSelectedFontSize = useCallback(
    (deltaSteps: number) => {
      const targets =
        selectedBlocks.length > 0
          ? selectedBlocks.filter((b) => isComunicadoVisualBoxBlock(b))
          : selected && isComunicadoVisualBoxBlock(selected)
            ? [selected]
            : [];
      if (targets.length === 0) return;
      if (!playlistId || !slideId) {
        updateSelectedTextFormatStyle(
          { fontSizeAuto: false },
          {
            fontSizeMode: "delta",
            fontSizeDelta: deltaSteps * 2,
          },
        );
        return;
      }
      void commitOpsAndApplyAck({
        playlistId,
        slideId,
        ops: targets.map((block) => ({
          op: "bump_font_size",
          blockId: block.id,
          deltaSteps,
        })),
        gate: mutationGateRef.current,
        applyAck: (canonical) => {
          commitWithHistory(canonical);
        },
      }).then((canonical) => {
        if (canonical) return;
        updateSelectedTextFormatStyle(
          { fontSizeAuto: false },
          {
            fontSizeMode: "delta",
            fontSizeDelta: deltaSteps * 2,
          },
        );
      });
    },
    [
      commitWithHistory,
      playlistId,
      selected,
      selectedBlocks,
      slideId,
      updateSelectedTextFormatStyle,
    ],
  );

  const duplicateSelected = useCallback(async () => {
    const ids = getActionSelectedIds();
    const idSet = new Set(ids);
    const sources =
      idSet.size > 0
        ? (configRef.current.blocks ?? []).filter((block) => idSet.has(block.id))
        : selectedBlocks.length > 0
          ? selectedBlocks
          : selected
            ? [selected]
            : [];
    if (sources.length === 0) return;

    const sourceIds = sources.map((s) => s.id);

    // Prefer backend identity mint when no data-source clone policy is needed.
    const needsDataPolicy = sources.some(
      (s) => isDataSourceBlockType(s.type) || ("dataSourceId" in s && Boolean(s.dataSourceId)),
    );
    if (playlistId && slideId && !needsDataPolicy) {
      try {
        const canonical = await commitDuplicateBlocks({
          playlistId,
          slideId,
          blockIds: sourceIds,
        });
        if (canonical) {
          const before = new Set((configRef.current.blocks ?? []).map((b) => b.id));
          commitWithHistory(canonical);
          const pastedIds = (canonical.blocks ?? [])
            .map((b) => b.id)
            .filter((id) => !before.has(id));
          if (pastedIds.length > 0) selectBlocksByIds(pastedIds);
          return;
        }
      } catch {
        /* fall through to local duplicate */
      }
    }

    const existing = configRef.current.blocks ?? [];
    const enriched = enrichClipboardWithLinkedDataSources(sources, existing);
    let plan = resolveBlockPasteDataPolicy({
      incoming: enriched,
      targetBlocks: existing,
    });
    if (plan.requiresUserChoice) {
      if (!chooseDataSourceDuplicatePolicy) {
        plan = { policy: "clone_source", requiresUserChoice: false };
      } else {
        const choice = await chooseDataSourceDuplicatePolicy();
        if (!choice) return;
        plan = resolveBlockPasteDataPolicy({
          incoming: enriched,
          targetBlocks: existing,
          userPolicy: choice,
        });
      }
    }

    const { blocks, pastedIds } = duplicateBlocksWithDataPolicy(
      existing,
      enriched,
      plan.policy,
    );
    updateBlocks(blocks);
    selectBlocksByIds(pastedIds);
    if (playlistId && slideId) {
      const pasted = blocks.filter((b) => pastedIds.includes(b.id));
      void ackUpsertBlocksWithGeneration({
        playlistId,
        slideId,
        blocks: pasted as unknown as Record<string, unknown>[],
        gate: mutationGateRef.current,
        applyAck: (canonical) => {
          commitWithHistory(canonical);
        },
      });
    }
  }, [
    chooseDataSourceDuplicatePolicy,
    commitWithHistory,
    configRef,
    getActionSelectedIds,
    playlistId,
    selectBlocksByIds,
    selected,
    selectedBlocks,
    slideId,
    updateBlocks,
  ]);

  const replaceSelectedDataRoute = useCallback(
    (block: ComunicadoBlock) => {
      if (!selected || !("dataBinding" in selected) || !("dataBinding" in block)) return;
      const selectedIsData =
        isDataBlockType(selected.type) || isDataSourceBlockType(selected.type);
      if (!selectedIsData) return;

      if (isDataSourceBlockType(selected.type)) {
        const nextBinding = { ...selected.dataBinding };
        nextBinding.operationId = block.dataBinding.operationId;
        nextBinding.label = block.dataBinding.label;
        nextBinding.params = { ...(block.dataBinding.params ?? {}) };
        if (block.dataBinding.refreshSec != null) {
          nextBinding.refreshSec = block.dataBinding.refreshSec;
        } else {
          delete nextBinding.refreshSec;
        }
        delete nextBinding.selectedValueFields;
        delete nextBinding.valueField;
        updateSelected({ dataBinding: nextBinding } as Partial<ComunicadoBlock>);
      } else if (isDataBlockType(block.type)) {
        updateSelected({
          type: block.type,
          dataBinding: {
            ...selected.dataBinding,
            operationId: block.dataBinding.operationId,
            label: block.dataBinding.label,
            displayMode: block.dataBinding.displayMode,
            params: { ...(block.dataBinding.params ?? {}) },
          },
        } as Partial<ComunicadoBlock>);
      } else {
        return;
      }
      setSelectedId(selected.id);
    },
    [selected, setSelectedId, updateSelected],
  );

  const removeSelected = useCallback(() => {
    const ids = getActionSelectedIds();
    const chartBlock =
      selected?.type === "chart_view" ? selected : selectedBlocks.find((b) => b.type === "chart_view");
    if (
      selectedChartPart &&
      chartBlock &&
      chartBlock.type === "chart_view" &&
      ids.includes(chartBlock.id) &&
      chartPartAllowsDelete(selectedChartPart)
    ) {
      const result = deleteChartPart(chartBlock.chartParts, selectedChartPart, chartBlock.chartOptions);
      updateBlock(chartBlock.id, {
        chartParts: result.parts,
        chartOptions: result.options,
      } as Partial<ComunicadoBlock>);
      setSelectedChartPart(null);
      setEditingChartPart(null);
      setSelectedTablePart(null);
      return;
    }

    const tableBlock =
      selected?.type === "table_view" ? selected : selectedBlocks.find((b) => b.type === "table_view");
    if (
      selectedTablePart &&
      tableBlock &&
      tableBlock.type === "table_view" &&
      ids.includes(tableBlock.id) &&
      tablePartAllowsDelete(selectedTablePart)
    ) {
      const result = deleteTablePart(tableBlock.tableParts, selectedTablePart, tableBlock.tableOptions);
      updateBlock(tableBlock.id, {
        tableParts: result.parts,
        tableOptions: result.options,
      } as Partial<ComunicadoBlock>);
      setSelectedTablePart(null);
      return;
    }

    const kpiBlock =
      selected?.type === "kpi_view" ? selected : selectedBlocks.find((b) => b.type === "kpi_view");
    if (
      selectedKpiPart &&
      kpiBlock &&
      kpiBlock.type === "kpi_view" &&
      ids.includes(kpiBlock.id) &&
      kpiPartAllowsDelete(selectedKpiPart)
    ) {
      const result = deleteKpiPart(kpiBlock.kpiParts, selectedKpiPart, kpiBlock.kpiOptions);
      updateBlock(kpiBlock.id, {
        kpiParts: result.parts,
        kpiOptions: mergeComunicadoKpiOptions(result.options),
      } as Partial<ComunicadoBlock>);
      setSelectedKpiPart(null);
      setEditingKpiPart(null);
      return;
    }

    if (ids.length === 0) return;
    const removeSet = new Set(ids);
    const currentBlocks = configRef.current.blocks ?? [];
    const removedInputs = currentBlocks.filter(
      (block): block is ComunicadoInputBlock =>
        removeSet.has(block.id) && isComunicadoInputBlock(block),
    );
    const refreshSourceIds = resolveRemovedInputRefreshSourceIds(removedInputs, currentBlocks);
    const filtered = currentBlocks.filter((block) => !removeSet.has(block.id));
    const nextBlocks = pruneOrphanConnectors(filtered);
    // Excluir não auto-seleciona outro bloco — deixa o palco sem seleção.
    selectBlocksByIds([]);

    if (removedInputs.length > 0) {
      const synced = syncAllConnectors(nextBlocks);
      const nextFilters = pruneSlideDataFiltersAfterInputRemoval(
        synced,
        configRef.current.dataFilters,
        removedInputs,
      );
      commitWithHistory({
        ...configRef.current,
        blocks: synced,
        dataFilters: nextFilters,
        version: Math.max(configRef.current.version ?? 3, 4),
      });
      if (refreshSourceIds.length > 0) {
        onInputBlocksRemoved?.({ sourceIds: refreshSourceIds });
      }
      return;
    }

    updateBlocks(nextBlocks);
  }, [
    commitWithHistory,
    configRef,
    getActionSelectedIds,
    onInputBlocksRemoved,
    selectBlocksByIds,
    selected,
    selectedBlocks,
    selectedChartPart,
    selectedKpiPart,
    selectedTablePart,
    setEditingChartPart,
    setEditingKpiPart,
    setSelectedChartPart,
    setSelectedKpiPart,
    setSelectedTablePart,
    updateBlock,
    updateBlocks,
  ]);
  removeSelectedRef.current = removeSelected;

  const moveLayer = useCallback(
    (direction: "up" | "down") => {
      if (!selected) return;
      const currentZ = selected.style?.zIndex ?? 1;
      updateSelectedStyle({ zIndex: Math.max(1, currentZ + (direction === "up" ? 1 : -1)) });
    },
    [selected, updateSelectedStyle],
  );

  const applyLayerOrder = useCallback(
    (
      transform: (blocks: ComunicadoBlock[], selectedIds: string[]) => ComunicadoBlock[],
      command: "bring-to-front" | "send-to-back" | "bring-forward" | "send-backward",
    ) => {
      const ids = getActionSelectedIds();
      if (ids.length === 0) return;
      const applyLocal = () => {
        updateBlocks(transform(configRef.current.blocks ?? [], ids));
      };
      if (!playlistId || !slideId) {
        applyLocal();
        return;
      }
      void commitReorderBlockZ({ playlistId, slideId, blockIds: ids, command })
        .then((canonical) => {
          if (!canonical) {
            applyLocal();
            return;
          }
          commitWithHistory(canonical);
        })
        .catch(() => {
          applyLocal();
        });
    },
    [commitWithHistory, configRef, getActionSelectedIds, playlistId, slideId, updateBlocks],
  );

  const bringToFrontSelected = useCallback(() => {
    applyLayerOrder(bringToFront, "bring-to-front");
  }, [applyLayerOrder]);

  const sendToBackSelected = useCallback(() => {
    applyLayerOrder(sendToBack, "send-to-back");
  }, [applyLayerOrder]);

  const bringForwardSelected = useCallback(() => {
    applyLayerOrder(bringForward, "bring-forward");
  }, [applyLayerOrder]);

  const sendBackwardSelected = useCallback(() => {
    applyLayerOrder(sendBackward, "send-backward");
  }, [applyLayerOrder]);

  const reorderBlockLayer = useCallback(
    (movedIds: string[], targetId: string, edge?: "before" | "after") => {
      const next = reorderLayerIds(configRef.current.blocks ?? [], movedIds, targetId, edge);
      updateBlocks(next);
      const idSet = new Set(movedIds);
      ackBlocksMutation(next.filter((b) => idSet.has(b.id)));
    },
    [ackBlocksMutation, configRef, updateBlocks],
  );

  const nudgeSelected = useCallback(
    (dx: number, dy: number) => {
      const chartBlock =
        selected?.type === "chart_view" ? selected : selectedBlocks.find((b) => b.type === "chart_view");
      if (
        selectedChartPart &&
        chartBlock &&
        chartBlock.type === "chart_view" &&
        selectedIds.includes(chartBlock.id) &&
        chartPartAllowsMove(selectedChartPart)
      ) {
        const nextParts = nudgeChartPartFrame(chartBlock.chartParts, selectedChartPart, dx, dy);
        updateBlock(chartBlock.id, { chartParts: nextParts } as Partial<ComunicadoBlock>);
        return;
      }

      const targets = selectedBlocks.length > 0 ? selectedBlocks : selected ? [selected] : [];
      if (targets.length === 0) return;
      const idSet = new Set(targets.map((block) => block.id));
      const moved = (configRef.current.blocks ?? []).map((block) => {
        if (!idSet.has(block.id)) return block;
        /* Linha: mover vertices (frame sozinho não muda o desenho). */
        if (block.type === "shape" && isLineShapeKind(block.shape)) {
          return translateLineEndpoints(block, dx, dy);
        }
        return {
          ...block,
          frame: {
            ...block.frame,
            x: Math.max(0, Math.min(100 - block.frame.w, block.frame.x + dx)),
            y: Math.max(0, Math.min(100 - block.frame.h, block.frame.y + dy)),
          },
        };
      });
      updateBlocks(reconcileConnectorsAfterDrag(moved, idSet));
      ackBlocksMutation(moved.filter((b) => idSet.has(b.id)));
    },
    [
      ackBlocksMutation,
      configRef,
      selected,
      selectedBlocks,
      selectedChartPart,
      selectedIds,
      updateBlock,
      updateBlocks,
    ],
  );

  const applySlideTemplate = useCallback(
    (nativeConfig: Record<string, unknown>) => {
      const parsed = parseComunicadoConfig(nativeConfig);
      const blocksWithIds = (parsed.blocks ?? []).map((block) => ({
        ...block,
        id: newBlockId(),
      }));
      commitWithHistory({
        ...configRef.current,
        version: Math.max(parsed.version ?? 4, 4),
        background: parsed.background ?? configRef.current.background,
        dataFilters: parsed.dataFilters ?? configRef.current.dataFilters,
        blocks: blocksWithIds,
      });
      selectBlocksByIds(blocksWithIds[0]?.id ? [blocksWithIds[0].id] : []);
    },
    [commitWithHistory, configRef, selectBlocksByIds],
  );

  /** Draft do Copiloto: aplica nativeConfig do BFF sem remintar ids. */
  const replaceSlideNativeConfig = useCallback(
    (nativeConfig: Record<string, unknown>) => {
      const parsed = parseComunicadoConfig(nativeConfig);
      const nextBlocks = parsed.blocks ?? [];
      const prevSelected = getActionSelectedIds();
      commitWithHistory({
        ...configRef.current,
        version: Math.max(parsed.version ?? configRef.current.version ?? 4, 4),
        headline: parsed.headline ?? configRef.current.headline,
        subtitle: parsed.subtitle ?? configRef.current.subtitle,
        background: parsed.background ?? configRef.current.background,
        dataFilters: parsed.dataFilters ?? configRef.current.dataFilters,
        groupTransforms: parsed.groupTransforms ?? configRef.current.groupTransforms,
        speakerNotes:
          parsed.speakerNotes !== undefined
            ? parsed.speakerNotes
            : configRef.current.speakerNotes,
        customFonts: parsed.customFonts ?? configRef.current.customFonts,
        blocks: nextBlocks,
      });
      const keep = prevSelected.filter((id) => nextBlocks.some((b) => b.id === id));
      selectBlocksByIds(keep);
    },
    [commitWithHistory, configRef, getActionSelectedIds, selectBlocksByIds],
  );

  const applySlideTheme = useCallback(
    (theme: ComunicadoSlideTheme) => {
      const next = applyComunicadoSlideTheme(configRef.current, theme);
      commitWithHistory(next);
      ackBlocksMutation(next.blocks ?? []);
    },
    [ackBlocksMutation, commitWithHistory, configRef],
  );

  const alignSelected = useCallback(
    (command: LayoutAlignCommand) => {
      const ids = getActionSelectedIds();
      if (ids.length === 0) return;
      const applyLocal = () => {
        const aligned = alignComunicadoBlocks(configRef.current.blocks ?? [], ids, command);
        updateBlocks(reconcileConnectorsAfterDrag(aligned, new Set(ids)));
      };
      if (!playlistId || !slideId) {
        applyLocal();
        return;
      }
      void commitAlignBlocks({ playlistId, slideId, blockIds: ids, command })
        .then((canonical) => {
          if (!canonical) {
            applyLocal();
            return;
          }
          commitWithHistory(canonical);
        })
        .catch(() => {
          applyLocal();
        });
    },
    [commitWithHistory, configRef, getActionSelectedIds, playlistId, slideId, updateBlocks],
  );

  const sameSizeSelected = useCallback(
    (axis: SameSizeAxis) => {
      const ids = getActionSelectedIds();
      if (ids.length === 0) return;
      const resized = resizeComunicadoBlocksSameSize(configRef.current.blocks ?? [], ids, axis);
      updateBlocks(reconcileConnectorsAfterDrag(resized, new Set(ids)));
      const idSet = new Set(ids);
      ackBlocksMutation(resized.filter((b) => idSet.has(b.id)));
    },
    [ackBlocksMutation, configRef, getActionSelectedIds, updateBlocks],
  );

  const rotateSelected = useCallback(
    (deltaDeg: number) => {
      const ids = getActionSelectedIds();
      if (ids.length === 0) return;
      const idSet = new Set(ids);
      const current = configRef.current.blocks ?? [];

      if (ids.length === 1) {
        const next = current.map((block) =>
          idSet.has(block.id)
            ? ({ ...block, style: rotateBlockStyle(block.style, deltaDeg) } as ComunicadoBlock)
            : block,
        );
        updateBlocks(next);
        ackBlocksMutation(next.filter((b) => idSet.has(b.id)));
        return;
      }

      const members = current
        .filter((block) => idSet.has(block.id))
        .map((block) => ({
          id: block.id,
          frame: { ...block.frame },
          rotation: block.style?.rotation ?? 0,
        }));
      const selectedGroupIds = new Set(
        current
          .filter((block) => idSet.has(block.id))
          .map((block) => block.groupId)
          .filter((id): id is string => Boolean(id)),
      );
      const groupId = selectedGroupIds.size === 1 ? [...selectedGroupIds][0] : undefined;
      const groupRotation = groupId
        ? configRef.current.groupTransforms?.[groupId]?.rotation
        : undefined;
      const updates = applyGroupRotationOnce({
        members,
        deltaDeg,
        slideAspect: getSlideAspectRatioRef.current(),
        groupRotation,
      });
      const next = current.map((block) => {
        const update = updates.get(block.id);
        if (!update) return block;
        return {
          ...block,
          frame: update.frame,
          style: { ...block.style, rotation: update.rotation },
        } as ComunicadoBlock;
      });
      updateBlocks(
        next,
        groupId
          ? {
              groupTransforms: {
                ...(configRef.current.groupTransforms ?? {}),
                [groupId]: {
                  rotation: clampRotationDeg((groupRotation ?? 0) + deltaDeg),
                },
              },
            }
          : undefined,
      );
      ackBlocksMutation(next.filter((b) => idSet.has(b.id)));
    },
    [ackBlocksMutation, configRef, getActionSelectedIds, updateBlocks],
  );

  const flipSelectedHorizontal = useCallback(() => {
    const ids = getActionSelectedIds();
    if (ids.length === 0) return;
    const idSet = new Set(ids);
    const next = (configRef.current.blocks ?? []).map((block) =>
      idSet.has(block.id)
        ? ({ ...block, style: flipHorizontalStyle(block.style) } as ComunicadoBlock)
        : block,
    );
    updateBlocks(next);
    ackBlocksMutation(next.filter((b) => idSet.has(b.id)));
  }, [ackBlocksMutation, configRef, getActionSelectedIds, updateBlocks]);

  const flipSelectedVertical = useCallback(() => {
    const ids = getActionSelectedIds();
    if (ids.length === 0) return;
    const idSet = new Set(ids);
    const next = (configRef.current.blocks ?? []).map((block) =>
      idSet.has(block.id)
        ? ({ ...block, style: flipVerticalStyle(block.style) } as ComunicadoBlock)
        : block,
    );
    updateBlocks(next);
    ackBlocksMutation(next.filter((b) => idSet.has(b.id)));
  }, [ackBlocksMutation, configRef, getActionSelectedIds, updateBlocks]);

  const setBlocksHidden = useCallback(
    (blockIds: string[], hidden: boolean) => {
      if (blockIds.length === 0) return;
      const idSet = new Set(blockIds);
      const next = (configRef.current.blocks ?? []).map((block) =>
        idSet.has(block.id) ? ({ ...block, hidden } as ComunicadoBlock) : block,
      );
      updateBlocks(next);
      ackBlocksMutation(next.filter((b) => idSet.has(b.id)));
    },
    [ackBlocksMutation, configRef, updateBlocks],
  );

  const toggleBlockHidden = useCallback(
    (blockId: string) => {
      const block = (configRef.current.blocks ?? []).find((item) => item.id === blockId);
      if (!block) return;
      setBlocksHidden([blockId], block.hidden !== true);
    },
    [configRef, setBlocksHidden],
  );

  const showAllBlocks = useCallback(() => {
    const ids = (configRef.current.blocks ?? [])
      .filter((block) => block.hidden === true)
      .map((block) => block.id);
    setBlocksHidden(ids, false);
  }, [configRef, setBlocksHidden]);

  const hideAllBlocks = useCallback(() => {
    const ids = (configRef.current.blocks ?? []).map((block) => block.id);
    setBlocksHidden(ids, true);
  }, [configRef, setBlocksHidden]);

  const focusFrameRotationField = useCallback(() => {
    if (requestRibbonTab) requestRibbonTab("element");
    else setRibbonTabRequest("element");
    window.requestAnimationFrame(() => {
      const el = document.getElementById("td-ribbon-frame-rotation");
      if (el instanceof HTMLElement) {
        el.scrollIntoView({ block: "nearest", behavior: "smooth" });
        el.focus();
      }
    });
  }, [requestRibbonTab, setRibbonTabRequest]);

  const setBackground = useCallback(
    (background: ComunicadoBackground) => {
      commitWithHistory({ ...configRef.current, background });
      if (!playlistId || !slideId) return;
      void commitPatchNativeConfig({
        playlistId,
        slideId,
        patch: { background },
      })
        .then((canonical) => {
          if (canonical) commitWithHistory(canonical);
        })
        .catch(() => undefined);
    },
    [commitWithHistory, configRef, playlistId, slideId],
  );

  const setBackgroundFill = useCallback(
    (fill: import("@delpi/plugin-ui/index").DelpiFill) => {
      setBackground(patchBackgroundUnderlay(configRef.current.background, fill));
    },
    [configRef, setBackground],
  );

  const setBackgroundColor = useCallback(
    (color: string) => {
      setBackgroundFill({ kind: "solid", color });
    },
    [setBackgroundFill],
  );

  const setBackgroundGradient = useCallback(
    (from: string, to: string, angle = 180) => {
      setBackgroundFill({
        kind: "gradient",
        angle,
        stops: [
          { color: from, position: 0 },
          { color: to, position: 100 },
        ],
      });
    },
    [setBackgroundFill],
  );

  const bindSelectedVisualBoxToData = useCallback(() => {
    if (!selected || !isComunicadoVisualBoxBlock(selected)) return;
    const sourceId = resolvePreferredDataSourceId(configRef.current.blocks ?? [], selectedId);
    if (!sourceId) {
      setDataPanelIntent("catalog");
      setDataCatalogMode("insert");
      setDataCatalogModalOpen(true);
      return;
    }
    const linked = linkViewToSource(selected, sourceId);
    updateSelected(linked as Partial<ComunicadoBlock>);
    setDataPanelIntent("binding");
    setDataPanelOpen(true);
  }, [
    configRef,
    linkViewToSource,
    selected,
    selectedId,
    setDataCatalogModalOpen,
    setDataCatalogMode,
    setDataPanelIntent,
    setDataPanelOpen,
    updateSelected,
  ]);

  const insertTextDataFieldBlock = useCallback(() => {
    if (selected && isComunicadoVisualBoxBlock(selected)) {
      bindSelectedVisualBoxToData();
      return;
    }
    let block = createBlock("text", "Texto");
    block.style = { ...block.style, zIndex: nextZIndex(configRef.current.blocks ?? []) };
    const sourceId = resolvePreferredDataSourceId(configRef.current.blocks ?? [], selectedId);
    if (sourceId) {
      block = linkViewToSource(block, sourceId) as typeof block;
      setDataPanelIntent("binding");
      setDataPanelOpen(true);
    } else {
      setDataPanelIntent("catalog");
      setDataCatalogMode("insert");
      setDataCatalogModalOpen(true);
    }
    block = placeInserted(block);
    commitAndSelectInserted([...(configRef.current.blocks ?? []), block], [block.id]);
  }, [
    bindSelectedVisualBoxToData,
    commitAndSelectInserted,
    configRef,
    linkViewToSource,
    placeInserted,
    selected,
    selectedId,
    setDataCatalogModalOpen,
    setDataCatalogMode,
    setDataPanelIntent,
    setDataPanelOpen,
  ]);

  return {
    updateBlocks,
    addBlock,
    addDataBlock,
    addDataSourceBlock,
    addChartViewBlock,
    addCanvasTableBlock,
    addInputBlock,
    addTableViewBlock,
    addKpiViewBlock,
    openDataPanel,
    openDataCatalog,
    setDataFilters,
    patchInputBlock,
    addShape,
    addPreparedShapeBlock,
    addIconBlock,
    groupSelected,
    ungroupSelected,
    regroupSelected,
    lastUngroupedIds,
    connectSelected,
    updateSelected,
    updateBlock,
    commitChartPartContent,
    commitKpiPartContent,
    updateBlockContent,
    updateBlockTextFields,
    updateBlockLink,
    updateSelectedStyle,
    updateSelectedTextFormatStyle,
    transformSelectedTextCase,
    bumpSelectedFontSize,
    duplicateSelected,
    replaceSelectedDataRoute,
    removeSelected,
    moveLayer,
    bringToFront: bringToFrontSelected,
    sendToBack: sendToBackSelected,
    bringForward: bringForwardSelected,
    sendBackward: sendBackwardSelected,
    reorderBlockLayer,
    nudgeSelected,
    applySlideTemplate,
    replaceSlideNativeConfig,
    applySlideTheme,
    alignSelected,
    sameSizeSelected,
    rotateSelected,
    flipSelectedHorizontal,
    flipSelectedVertical,
    setBlocksHidden,
    toggleBlockHidden,
    showAllBlocks,
    hideAllBlocks,
    focusFrameRotationField,
    setBackgroundColor,
    setBackgroundFill,
    setBackgroundGradient,
    setBackground,
    bindSelectedVisualBoxToData,
    insertTextDataFieldBlock,
  };
}
