import {
  useCallback,
  useState,
  type Dispatch,
  type MutableRefObject,
  type RefObject,
  type SetStateAction,
} from "react";

import {
  chartOptionsToParts,
  chartPartAllowsDelete,
  chartPartAllowsMove,
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
  isDataBlockType,
  isDataSourceBlockType,
  isDataViewBlockType,
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
  resolveBlockPasteDataPolicy,
  type ComunicadoBlock,
  type ComunicadoChartPartRef,
  type ComunicadoChartType,
  type ComunicadoConfig,
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
import { applyComunicadoBlockStylePatch } from "../../utils/applyComunicadoBlockStylePatch";
import { DATE_RANGE_PRESET_PARAM, PERIOD_DAYS_PARAM } from "../../utils/dateRangePresets";
import { renameKpiMetricFieldLabel } from "../../utils/renameKpiMetricFieldLabel";
import {
  bringForward,
  bringToFront,
  sendBackward,
  sendToBack,
} from "../../utils/comunicadoLayerOrder";
import { groupBlocks, ungroupBlocks, expandSelectionWithGroups } from "../../utils/comunicadoGrouping";
import {
  applyGroupRotationDelta,
  resolveFramesGroupCenter,
} from "../../utils/multiFrameTransform";
import {
  flipHorizontalStyle,
  flipVerticalStyle,
  rotateBlockStyle,
} from "../../utils/comunicadoTransform";
import { placeBlockInViewportCenter } from "../../utils/placeBlockInViewport";
import {
  isChartTextFormatPart,
  isKpiTextFormatPart,
  type TextFormatStyleSnapshot,
} from "../../utils/selectedTextFormatTarget";

type Options = {
  canvasRef?: RefObject<HTMLElement | null>;
  canvasWrapRef?: RefObject<HTMLElement | null>;
  configRef: MutableRefObject<ComunicadoConfig>;
  commitWithHistory: (next: ComunicadoConfig) => void;
  selectedIds: string[];
  selectedId: string | null;
  selected: ComunicadoBlock | null;
  selectedBlocks: ComunicadoBlock[];
  selectedChartPart: ComunicadoChartPartRef | null;
  selectedTablePart: ComunicadoTablePartRef | null;
  selectedKpiPart: ComunicadoKpiPartRef | null;
  selectedInputPart: ComunicadoInputPartRef | null;
  editingChartPart: ComunicadoChartPartRef | null;
  editingKpiPart: ComunicadoKpiPartRef | null;
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
};

/**
 * Mutações de blocos (add/update/remove/group/layer/nudge/align/theme) via histórico.
 */
export function useComunicadoEditorBlocks({
  configRef,
  commitWithHistory,
  selectedIds,
  selectedId,
  selected,
  selectedBlocks,
  selectedChartPart,
  selectedTablePart,
  selectedKpiPart,
  selectedInputPart,
  editingChartPart,
  editingKpiPart,
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
}: Options) {
  const [lastUngroupedIds, setLastUngroupedIds] = useState<string[]>([]);

  const placeInserted = useCallback(
    <T extends ComunicadoBlock>(block: T): T =>
      placeBlockInViewportCenter(block, canvasRef?.current, canvasWrapRef?.current),
    [canvasRef, canvasWrapRef],
  );

  const updateBlocks = useCallback(
    (nextBlocks: ComunicadoBlock[]) => {
      const withConnectors = syncAllConnectors(pruneOrphanConnectors(nextBlocks));
      commitWithHistory({ ...configRef.current, blocks: withConnectors });
    },
    [commitWithHistory, configRef],
  );

  const connectSelected = useCallback(() => {
    if (selectedIds.length !== 2) return;
    const blocks = configRef.current.blocks ?? [];
    const [idA, idB] = selectedIds;
    const a = blocks.find((block) => block.id === idA);
    const b = blocks.find((block) => block.id === idB);
    if (!a || !b || !canConnectBlocks(a, b)) return;
    const connector = createConnectorBlock(a, b, { zIndex: nextZIndex(blocks) });
    updateBlocks([...blocks, connector]);
    selectBlocksByIds([connector.id]);
  }, [configRef, selectBlocksByIds, selectedIds, updateBlocks]);

  const addBlock = useCallback(
    (type: ComunicadoBlock["type"]) => {
      let block = createBlock(
        type,
        type === "heading" ? "Novo título" : type === "text" ? "Texto" : "",
      );
      block.style = { ...block.style, zIndex: nextZIndex(configRef.current.blocks ?? []) };
      block = placeInserted(block);
      setSelectedId(block.id);
      updateBlocks([...(configRef.current.blocks ?? []), block]);
    },
    [configRef, placeInserted, setSelectedId, updateBlocks],
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
      setSelectedId(withZ.id);
      updateBlocks([...(configRef.current.blocks ?? []), withZ]);
    },
    [configRef, placeInserted, setLastDataDisplayMode, setSelectedId, updateBlocks],
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
      setSelectedId(block.id);
      updateBlocks([...(configRef.current.blocks ?? []), block]);
    },
    [configRef, linkViewToSource, placeInserted, selectedId, setSelectedId, updateBlocks],
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
      setSelectedId(block.id);
      updateBlocks([...(configRef.current.blocks ?? []), block]);
    },
    [configRef, linkViewToSource, placeInserted, selectedId, setSelectedId, updateBlocks],
  );

  const addCanvasTableBlock = useCallback(
    (rows = 3, cols = 3) => {
      let block = createCanvasTableBlock(rows, cols);
      block.style = { ...block.style, zIndex: nextZIndex(configRef.current.blocks ?? []) };
      block = placeInserted(block);
      setSelectedId(block.id);
      updateBlocks([...(configRef.current.blocks ?? []), block]);
    },
    [configRef, placeInserted, setSelectedId, updateBlocks],
  );

  const addInputBlock = useCallback(() => {
    let block = createInputBlock({ targetScope: "slide", paramKey: "" });
    block.style = { ...block.style, zIndex: nextZIndex(configRef.current.blocks ?? []) };
    block = placeInserted(block);
    setSelectedId(block.id);
    updateBlocks([...(configRef.current.blocks ?? []), block]);
  }, [configRef, placeInserted, setSelectedId, updateBlocks]);

  const addKpiViewBlock = useCallback(() => {
    let block = createKpiViewBlock();
    const sourceId = resolvePreferredDataSourceId(configRef.current.blocks ?? [], selectedId);
    if (sourceId) {
      block = linkViewToSource(block, sourceId);
    }
    block.style = { ...block.style, zIndex: nextZIndex(configRef.current.blocks ?? []) };
    block = placeInserted(block);
    setSelectedId(block.id);
    updateBlocks([...(configRef.current.blocks ?? []), block]);
  }, [configRef, linkViewToSource, placeInserted, selectedId, setSelectedId, updateBlocks]);

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
        setSelectedId(viewBlock.id);
        updateBlocks(nextBlocks);
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
      setSelectedId(withZ.id);
      updateBlocks(nextBlocks);
    },
    [
      configRef,
      linkViewToSource,
      placeInserted,
      selectedId,
      setDataPanelOpen,
      setLastDataDisplayMode,
      setSelectedId,
      updateBlocks,
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
      block = placeInserted(block);
      setSelectedId(block.id);
      setShapeMenuOpen(false);
      setRibbonTabRequest("element");
      updateBlocks([...(configRef.current.blocks ?? []), block]);
    },
    [configRef, placeInserted, setRibbonTabRequest, setSelectedId, setShapeMenuOpen, updateBlocks],
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
      setSelectedId(next.id);
      setRibbonTabRequest("element");
      updateBlocks([...(configRef.current.blocks ?? []), next]);
    },
    [configRef, setRibbonTabRequest, setSelectedId, updateBlocks],
  );

  const addIconBlock = useCallback(
    (iconName: string) => {
      let block = createIconBlock(iconName);
      block.style = { ...block.style, zIndex: nextZIndex(configRef.current.blocks ?? []) };
      block = placeInserted(block);
      setSelectedId(block.id);
      updateBlocks([...(configRef.current.blocks ?? []), block]);
    },
    [configRef, placeInserted, setSelectedId, updateBlocks],
  );

  const groupSelected = useCallback(() => {
    if (selectedIds.length < 2) return;
    updateBlocks(groupBlocks(configRef.current.blocks ?? [], selectedIds));
    setLastUngroupedIds([]);
  }, [configRef, selectedIds, updateBlocks]);

  const ungroupSelected = useCallback(() => {
    if (selectedIds.length === 0) return;
    const current = configRef.current.blocks ?? [];
    const expanded = expandSelectionWithGroups(current, selectedIds);
    const members = expanded.filter((id) => Boolean(current.find((block) => block.id === id)?.groupId));
    if (members.length >= 2) setLastUngroupedIds(members);
    updateBlocks(ungroupBlocks(current, expanded));
  }, [configRef, selectedIds, updateBlocks]);

  const regroupSelected = useCallback(() => {
    const current = configRef.current.blocks ?? [];
    const present = new Set(current.map((block) => block.id));
    const ids = lastUngroupedIds.filter((id) => present.has(id));
    if (ids.length < 2) return;
    updateBlocks(groupBlocks(current, ids));
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
    },
    [configRef, selectedIds, updateBlocks],
  );

  const updateBlock = useCallback(
    (blockId: string, patch: Partial<ComunicadoBlock>) => {
      const nextBlocks = (configRef.current.blocks ?? []).map((block) =>
        block.id === blockId ? ({ ...block, ...patch } as ComunicadoBlock) : block,
      );
      updateBlocks(nextBlocks);
    },
    [configRef, updateBlocks],
  );

  const commitChartPartContent = useCallback(
    (content: string) => {
      const part = editingChartPart;
      const blockId = selectedIds[selectedIds.length - 1] ?? null;
      setEditingChartPart(null);
      if (!part || !blockId) return;
      const block = configRef.current.blocks?.find((item) => item.id === blockId);
      if (!block || block.type !== "chart_view") return;

      const nextParts = upsertChartPartState(block.chartParts, part, {
        content,
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
      const syncedParts = chartOptionsToParts(nextOptions);
      updateBlock(blockId, {
        chartParts: { ...nextParts, ...syncedParts },
        chartOptions: nextOptions,
      } as Partial<ComunicadoBlock>);
    },
    [configRef, editingChartPart, selectedIds, setEditingChartPart, updateBlock],
  );

  const commitKpiPartContent = useCallback(
    (content: string) => {
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
    (patch: NonNullable<ComunicadoBlock["style"]>) => {
      const targets = selectedBlocks.length > 0 ? selectedBlocks : selected ? [selected] : [];
      if (targets.length === 0) return;
      const idSet = new Set(targets.map((block) => block.id));
      const nextBlocks = (configRef.current.blocks ?? []).map((block) =>
        idSet.has(block.id)
          ? applyComunicadoBlockStylePatch(block, patch, {
              selectedInputPart: block.type === "input" ? selectedInputPart : null,
            })
          : block,
      );
      updateBlocks(nextBlocks);
    },
    [configRef, selected, selectedBlocks, selectedInputPart, updateBlocks],
  );

  /** Tipografia da ribbon Formatar — bloco text/heading ou parte textual KPI/chart. */
  const updateSelectedTextFormatStyle = useCallback(
    (patch: TextFormatStyleSnapshot) => {
      if (!selected) return;

      if (selected.type === "kpi_view" && isKpiTextFormatPart(selectedKpiPart) && selectedKpiPart) {
        const prev = getKpiPartState(selected.kpiParts, selectedKpiPart)?.style;
        const nextFontSize =
          patch.fontSizeAuto === true
            ? undefined
            : patch.fontSize != null
              ? patch.fontSize
              : prev?.fontSize;
        const nextTypographyMode =
          patch.fontSizeAuto === true
            ? ("auto" as const)
            : patch.fontSize != null
              ? ("fixed" as const)
              : prev?.typographyMode;
        const nextParts = upsertKpiPartState(selected.kpiParts, selectedKpiPart, {
          style: {
            ...prev,
            fontFamily: patch.fontFamily ?? prev?.fontFamily,
            fontSize: nextFontSize,
            typographyMode: nextTypographyMode,
            fontWeight: patch.fontWeight ?? prev?.fontWeight,
            fontStyle: patch.fontStyle ?? prev?.fontStyle,
            color: patch.color ?? prev?.color,
            textDecoration: patch.textDecoration ?? prev?.textDecoration,
            textShadow: patch.textShadow ?? prev?.textShadow,
            textStrokeColor: patch.textStrokeColor ?? prev?.textStrokeColor,
            textStrokeWidth: patch.textStrokeWidth ?? prev?.textStrokeWidth,
            textReflection: patch.textReflection ?? prev?.textReflection,
            textAlign:
              patch.textAlign === "left" ||
              patch.textAlign === "center" ||
              patch.textAlign === "right" ||
              patch.textAlign === "justify"
                ? patch.textAlign
                : prev?.textAlign,
            verticalAlign:
              patch.verticalAlign === "top" ||
              patch.verticalAlign === "middle" ||
              patch.verticalAlign === "bottom"
                ? patch.verticalAlign
                : prev?.verticalAlign,
          },
        });
        const options = mergeComunicadoKpiOptions({
          ...selected.kpiOptions,
          ...partsToKpiOptions(nextParts),
        });
        if (selectedKpiPart.kind === "value" && patch.color) {
          options.valueColor = patch.color;
        }
        updateSelected({
          kpiParts: mergeKpiPartsWithOptions(nextParts, options),
          kpiOptions: options,
        } as Partial<ComunicadoBlock>);
        return;
      }

      if (
        selected.type === "chart_view" &&
        isChartTextFormatPart(selectedChartPart) &&
        selectedChartPart
      ) {
        const prev = getChartPartState(selected.chartParts, selectedChartPart)?.style;
        const nextParts = upsertChartPartState(selected.chartParts, selectedChartPart, {
          style: {
            ...prev,
            fontFamily: patch.fontFamily ?? prev?.fontFamily,
            fontSize: patch.fontSize ?? prev?.fontSize,
            fontWeight:
              patch.fontWeight === "bold" || patch.fontWeight === "normal"
                ? patch.fontWeight
                : prev?.fontWeight,
            fontStyle:
              patch.fontStyle === "italic" || patch.fontStyle === "normal"
                ? patch.fontStyle
                : prev?.fontStyle,
            color: patch.color ?? prev?.color,
            textShadow: patch.textShadow ?? prev?.textShadow,
            textStrokeColor: patch.textStrokeColor ?? prev?.textStrokeColor,
            textStrokeWidth: patch.textStrokeWidth ?? prev?.textStrokeWidth,
            textReflection: patch.textReflection ?? prev?.textReflection,
            textAlign:
              patch.textAlign === "left" ||
              patch.textAlign === "center" ||
              patch.textAlign === "right" ||
              patch.textAlign === "justify"
                ? patch.textAlign
                : prev?.textAlign,
            verticalAlign:
              patch.verticalAlign === "top" ||
              patch.verticalAlign === "middle" ||
              patch.verticalAlign === "bottom"
                ? patch.verticalAlign
                : prev?.verticalAlign,
          },
        });
        updateSelected({ chartParts: nextParts } as Partial<ComunicadoBlock>);
        return;
      }

      updateSelectedStyle(patch as NonNullable<ComunicadoBlock["style"]>);
    },
    [
      selected,
      selectedChartPart,
      selectedKpiPart,
      updateSelected,
      updateSelectedStyle,
    ],
  );

  const duplicateSelected = useCallback(async () => {
    const sources = selectedBlocks.length > 0 ? selectedBlocks : selected ? [selected] : [];
    if (sources.length === 0) return;

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
    // Commit antes da seleção: selectBlocksByIds resolve contra configRef.
    updateBlocks(blocks);
    selectBlocksByIds(pastedIds);
  }, [
    chooseDataSourceDuplicatePolicy,
    configRef,
    selectBlocksByIds,
    selected,
    selectedBlocks,
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
    const chartBlock =
      selected?.type === "chart_view" ? selected : selectedBlocks.find((b) => b.type === "chart_view");
    if (
      selectedChartPart &&
      chartBlock &&
      chartBlock.type === "chart_view" &&
      selectedIds.includes(chartBlock.id) &&
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
      selectedIds.includes(tableBlock.id) &&
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
      selectedIds.includes(kpiBlock.id) &&
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

    if (selectedIds.length === 0) return;
    const removeSet = new Set(selectedIds);
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
    onInputBlocksRemoved,
    selectBlocksByIds,
    selected,
    selectedBlocks,
    selectedChartPart,
    selectedIds,
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
    (transform: (blocks: ComunicadoBlock[], selectedIds: string[]) => ComunicadoBlock[]) => {
      if (selectedIds.length === 0) return;
      const nextBlocks = transform(configRef.current.blocks ?? [], selectedIds);
      updateBlocks(nextBlocks);
    },
    [configRef, selectedIds, updateBlocks],
  );

  const bringToFrontSelected = useCallback(() => {
    applyLayerOrder(bringToFront);
  }, [applyLayerOrder]);

  const sendToBackSelected = useCallback(() => {
    applyLayerOrder(sendToBack);
  }, [applyLayerOrder]);

  const bringForwardSelected = useCallback(() => {
    applyLayerOrder(bringForward);
  }, [applyLayerOrder]);

  const sendBackwardSelected = useCallback(() => {
    applyLayerOrder(sendBackward);
  }, [applyLayerOrder]);

  const reorderBlockLayer = useCallback(
    (blockId: string, targetIndex: number) => {
      const sorted = sortBlocksByZIndex(configRef.current.blocks ?? []);
      const fromIndex = sorted.findIndex((block) => block.id === blockId);
      if (fromIndex < 0 || fromIndex === targetIndex) return;
      const reordered = [...sorted];
      const [moved] = reordered.splice(fromIndex, 1);
      reordered.splice(targetIndex, 0, moved);
      const nextBlocks = reordered.map((block, index) => ({
        ...block,
        style: { ...block.style, zIndex: index + 1 },
      }));
      updateBlocks(nextBlocks);
    },
    [configRef, updateBlocks],
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
    },
    [configRef, selected, selectedBlocks, selectedChartPart, selectedIds, updateBlock, updateBlocks],
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

  const applySlideTheme = useCallback(
    (theme: ComunicadoSlideTheme) => {
      commitWithHistory(applyComunicadoSlideTheme(configRef.current, theme));
    },
    [commitWithHistory, configRef],
  );

  const alignSelected = useCallback(
    (command: LayoutAlignCommand) => {
      if (selectedIds.length === 0) return;
      const aligned = alignComunicadoBlocks(configRef.current.blocks ?? [], selectedIds, command);
      updateBlocks(reconcileConnectorsAfterDrag(aligned, new Set(selectedIds)));
    },
    [configRef, selectedIds, updateBlocks],
  );

  const rotateSelected = useCallback(
    (deltaDeg: number) => {
      if (selectedIds.length === 0) return;
      const idSet = new Set(selectedIds);
      const current = configRef.current.blocks ?? [];

      if (selectedIds.length === 1) {
        updateBlocks(
          current.map((block) =>
            idSet.has(block.id)
              ? ({ ...block, style: rotateBlockStyle(block.style, deltaDeg) } as ComunicadoBlock)
              : block,
          ),
        );
        return;
      }

      const startFrames = new Map<string, ComunicadoBlock["frame"]>();
      const startRotations = new Map<string, number>();
      for (const block of current) {
        if (!idSet.has(block.id)) continue;
        startFrames.set(block.id, { ...block.frame });
        startRotations.set(block.id, block.style?.rotation ?? 0);
      }
      const updates = applyGroupRotationDelta({
        startFrames,
        startRotations,
        center: resolveFramesGroupCenter(startFrames.values()),
        deltaDeg,
      });
      updateBlocks(
        current.map((block) => {
          const update = updates.get(block.id);
          if (!update) return block;
          return {
            ...block,
            frame: update.frame,
            style: { ...block.style, rotation: update.rotation },
          } as ComunicadoBlock;
        }),
      );
    },
    [configRef, selectedIds, updateBlocks],
  );

  const flipSelectedHorizontal = useCallback(() => {
    if (selectedIds.length === 0) return;
    const idSet = new Set(selectedIds);
    updateBlocks(
      (configRef.current.blocks ?? []).map((block) =>
        idSet.has(block.id)
          ? ({ ...block, style: flipHorizontalStyle(block.style) } as ComunicadoBlock)
          : block,
      ),
    );
  }, [configRef, selectedIds, updateBlocks]);

  const flipSelectedVertical = useCallback(() => {
    if (selectedIds.length === 0) return;
    const idSet = new Set(selectedIds);
    updateBlocks(
      (configRef.current.blocks ?? []).map((block) =>
        idSet.has(block.id)
          ? ({ ...block, style: flipVerticalStyle(block.style) } as ComunicadoBlock)
          : block,
      ),
    );
  }, [configRef, selectedIds, updateBlocks]);

  const setBlocksHidden = useCallback(
    (blockIds: string[], hidden: boolean) => {
      if (blockIds.length === 0) return;
      const idSet = new Set(blockIds);
      updateBlocks(
        (configRef.current.blocks ?? []).map((block) =>
          idSet.has(block.id) ? ({ ...block, hidden } as ComunicadoBlock) : block,
        ),
      );
    },
    [configRef, updateBlocks],
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

  const setBackgroundColor = useCallback(
    (color: string) => {
      commitWithHistory({ ...configRef.current, background: { type: "color", value: color } });
    },
    [commitWithHistory, configRef],
  );

  const setBackgroundGradient = useCallback(
    (from: string, to: string, angle = 180) => {
      commitWithHistory({
        ...configRef.current,
        background: { type: "gradient", from, to, angle },
      });
    },
    [commitWithHistory, configRef],
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
    setSelectedId(block.id);
    updateBlocks([...(configRef.current.blocks ?? []), block]);
  }, [
    bindSelectedVisualBoxToData,
    configRef,
    linkViewToSource,
    placeInserted,
    selected,
    selectedId,
    setDataCatalogModalOpen,
    setDataCatalogMode,
    setDataPanelIntent,
    setDataPanelOpen,
    setSelectedId,
    updateBlocks,
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
    applySlideTheme,
    alignSelected,
    rotateSelected,
    flipSelectedHorizontal,
    flipSelectedVertical,
    setBlocksHidden,
    toggleBlockHidden,
    showAllBlocks,
    hideAllBlocks,
    focusFrameRotationField,
    setBackgroundColor,
    setBackgroundGradient,
    bindSelectedVisualBoxToData,
    insertTextDataFieldBlock,
  };
}
