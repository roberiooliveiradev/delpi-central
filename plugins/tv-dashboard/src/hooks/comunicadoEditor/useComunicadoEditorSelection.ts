import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type MutableRefObject,
  type SetStateAction,
} from "react";

import {
  applyNamedStyleOnAllLines,
  defaultNamedStyleForBlockType,
  filterStageSelectableIds,
  isComunicadoVisualBoxBlock,
  isTablePartRefEqual,
  resolveNamedStyleSelectionForBlock,
  resolveStageSelectionTargetId,
  resolveTextBlockDisplayRuns,
  selectionListTypeState,
  selectionNamedStyleState,
  selectionRunStyleState,
  suggestDefaultTextProjection,
  syncTextBlockFromRuns,
  toggleListTypeOnAllLines,
  visualBoxEnsureRichTextBlock,
  type ComunicadoBlock,
  type ComunicadoConfig,
  type ComunicadoChartPartRef,
  type ComunicadoContentRun,
  type ComunicadoInputPartRef,
  type ComunicadoKpiPartRef,
  type ComunicadoListType,
  type ComunicadoNamedTextStyle,
  type ComunicadoTablePartRef,
  type ComunicadoTextBlock,
  type ContentRunStyleToggleKey,
} from "@delpi/tv-dashboard-presentation";

import type {
  ComunicadoEditorContextValue,
  ComunicadoRibbonTabRequest,
  SelectionPanelTab,
  TextEditorBridge,
  TextEditSelection,
} from "../../components/comunicadoEditorContextCore";
import {
  isSelectionPanelTab,
  normalizeSelectionRibbonTab,
} from "../../utils/normalizeSelectionRibbonTab";

type Options = {
  configRef: MutableRefObject<ComunicadoConfig>;
  blocks: ComunicadoBlock[];
  /** Evita ciclo com o hook de blocks — preenchido pelo Provider após criar `updateBlockTextFields`. */
  updateBlockTextFieldsRef: MutableRefObject<
    (blockId: string, fields: Pick<ComunicadoTextBlock, "content" | "contentRuns">) => void
  >;
  /** Substitui bloco inteiro (ex.: forma → texto rico ao aplicar lista). */
  updateBlocksRef: MutableRefObject<(next: ComunicadoBlock[]) => void>;
};

/**
 * Seleção de blocos / partes (chart, table, KPI) / edição de texto + ribbon tab request.
 */
export function useComunicadoEditorSelection({
  configRef,
  blocks,
  updateBlockTextFieldsRef,
  updateBlocksRef,
}: Options) {
  /** Sem auto-seleção: Gerenciar / F5 abrem no palco sem forçar Elemento. */
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [editingTextId, setEditingTextId] = useState<string | null>(null);
  const [selectedChartPart, setSelectedChartPart] = useState<ComunicadoChartPartRef | null>(null);
  const [editingChartPart, setEditingChartPart] = useState<ComunicadoChartPartRef | null>(null);
  const [editingTablePart, setEditingTablePart] = useState<ComunicadoTablePartRef | null>(null);
  /** Multi-seleção de partes da tabela (colunas) — o último item é a parte primária. */
  const [selectedTableParts, setSelectedTableParts] = useState<ComunicadoTablePartRef[]>([]);
  const selectedTablePart = selectedTableParts[selectedTableParts.length - 1] ?? null;
  const setSelectedTablePart = useCallback(
    (value: SetStateAction<ComunicadoTablePartRef | null>) => {
      setSelectedTableParts((current) => {
        const primary = current[current.length - 1] ?? null;
        const next = typeof value === "function" ? value(primary) : value;
        return next ? [next] : [];
      });
    },
    [],
  );
  const [selectedKpiPart, setSelectedKpiPart] = useState<ComunicadoKpiPartRef | null>(null);
  const [editingKpiPart, setEditingKpiPart] = useState<ComunicadoKpiPartRef | null>(null);
  const [selectedInputPart, setSelectedInputPart] = useState<ComunicadoInputPartRef | null>(null);
  const [textEditSelection, setTextEditSelection] = useState<TextEditSelection | null>(null);
  const [textEditSelectionStyle, setTextEditSelectionStyle] = useState<
    ComunicadoEditorContextValue["textEditSelectionStyle"]
  >(null);
  const [textEditListSelection, setTextEditListSelection] = useState<
    ComunicadoEditorContextValue["textEditListSelection"]
  >(null);
  const [textEditNamedStyleSelection, setTextEditNamedStyleSelection] = useState<
    ComunicadoEditorContextValue["textEditNamedStyleSelection"]
  >(null);
  const [ribbonTabRequest, setRibbonTabRequest] = useState<ComunicadoRibbonTabRequest | null>(null);
  const [selectionPanelTab, setSelectionPanelTabState] = useState<SelectionPanelTab>("layers");

  const setSelectionPanelTab = useCallback((tab: SelectionPanelTab) => {
    setSelectionPanelTabState(tab);
  }, []);

  const requestRibbonTab = useCallback((tab: ComunicadoRibbonTabRequest) => {
    const normalized = normalizeSelectionRibbonTab(tab);
    setRibbonTabRequest(normalized);
    if (isSelectionPanelTab(normalized)) {
      setSelectionPanelTabState(normalized);
    }
  }, []);

  const openLayersPanel = useCallback(() => {
    setSelectionPanelTabState("layers");
    /* Não setRibbonTabRequest("layers"): Camadas só abre o painel lateral.
     * Pedir a aba na top bar esconde o ribbon (parece «colapsado»). */
  }, []);

  const clearRibbonTabRequest = useCallback(() => {
    setRibbonTabRequest(null);
  }, []);

  const textEditorBridgesRef = useRef<Map<string, TextEditorBridge>>(new Map());
  const editingTextIdRef = useRef<string | null>(editingTextId);
  editingTextIdRef.current = editingTextId;

  const flushActiveTextEdit = useCallback((blockId?: string | null) => {
    const activeId = blockId ?? editingTextIdRef.current;
    if (!activeId) return;
    textEditorBridgesRef.current.get(activeId)?.commitPending?.();
  }, []);

  const clearPartSelections = useCallback(() => {
    setSelectedChartPart(null);
    setEditingChartPart(null);
    setSelectedTablePart(null);
    setEditingTablePart(null);
    setSelectedKpiPart(null);
    setEditingKpiPart(null);
    setSelectedInputPart(null);
  }, [setSelectedTablePart]);

  const clearTextEditUi = useCallback(() => {
    setTextEditSelection(null);
    setTextEditSelectionStyle(null);
    setTextEditListSelection(null);
    setTextEditNamedStyleSelection(null);
  }, []);

  const selectedId = selectedIds[selectedIds.length - 1] ?? null;

  /** Fonte vinculada some do palco — redireciona seleção para o visual ligado. */
  useEffect(() => {
    setSelectedIds((current) => {
      if (current.length === 0) return current;
      const next = [
        ...new Set(
          current
            .map((id) => resolveStageSelectionTargetId(id, blocks))
            .filter((id): id is string => Boolean(id)),
        ),
      ];
      if (next.length === current.length && next.every((id, index) => id === current[index])) {
        return current;
      }
      return next;
    });
  }, [blocks]);

  const setSelectedId = useCallback(
    (id: string | null) => {
      if (editingTextIdRef.current && editingTextIdRef.current !== id) {
        flushActiveTextEdit(editingTextIdRef.current);
      }
      const blocksNow = configRef.current.blocks ?? [];
      const target = id ? resolveStageSelectionTargetId(id, blocksNow) : null;
      setSelectedIds(target ? [target] : []);
      setEditingTextId((current) => (target === current ? current : null));
      clearPartSelections();
      if (!target) clearTextEditUi();
    },
    [clearPartSelections, clearTextEditUi, configRef, flushActiveTextEdit],
  );

  const selectBlocksByIds = useCallback(
    (blockIds: string[]) => {
      flushActiveTextEdit();
      const blocksNow = configRef.current.blocks ?? [];
      const unique = [
        ...new Set(
          blockIds
            .filter(Boolean)
            .map((id) => resolveStageSelectionTargetId(id, blocksNow))
            .filter((id): id is string => Boolean(id)),
        ),
      ];
      setSelectedIds(unique);
      setEditingTextId(null);
      clearPartSelections();
    },
    [clearPartSelections, configRef, flushActiveTextEdit],
  );

  const selectBlock = useCallback(
    (
      blockId: string,
      options?: { additive?: boolean; subtract?: boolean; expandGroup?: boolean },
    ) => {
      flushActiveTextEdit();
      const blocksNow = configRef.current.blocks ?? [];
      const targetId = resolveStageSelectionTargetId(blockId, blocksNow);
      if (!targetId) {
        if (!options?.additive && !options?.subtract) {
          setSelectedIds([]);
          setEditingTextId(null);
          clearPartSelections();
        }
        return;
      }
      let selectedBlockType: string | undefined;
      if (options?.subtract) {
        setSelectedIds((current) => {
          const remove = new Set<string>([targetId]);
          const block = blocksNow.find((item) => item.id === targetId);
          if (block?.groupId) {
            const memberIds = blocksNow
              .filter((item) => item.groupId === block.groupId)
              .map((item) => item.id);
            if (memberIds.length > 1 && memberIds.every((id) => current.includes(id))) {
              for (const id of memberIds) remove.add(id);
            }
          }
          return filterStageSelectableIds(
            current.filter((id) => !remove.has(id)),
            blocksNow,
          );
        });
        setEditingTextId(null);
        clearPartSelections();
        return;
      }
      if (options?.additive) {
        setSelectedIds((current) => {
          const set = new Set(current);
          if (set.has(targetId)) set.delete(targetId);
          else set.add(targetId);
          return filterStageSelectableIds([...set], blocksNow);
        });
      } else {
        const block = blocksNow.find((item) => item.id === targetId);
        selectedBlockType = block?.type;
        const expandGroup = options?.expandGroup !== false;
        if (expandGroup && block?.groupId) {
          const memberIds = blocksNow
            .filter((item) => item.groupId === block.groupId)
            .map((item) => item.id);
          setSelectedIds(filterStageSelectableIds(memberIds, blocksNow));
        } else {
          setSelectedIds([targetId]);
        }
      }
      setEditingTextId(null);
      clearPartSelections();
      if (selectedBlockType === "chart_view") {
        requestRibbonTab("element");
      } else if (selectedBlockType === "table_view") {
        requestRibbonTab("element");
      } else if (
        selectedBlockType === "shape" ||
        selectedBlockType === "heading" ||
        selectedBlockType === "text" ||
        selectedBlockType === "image" ||
        selectedBlockType === "video" ||
        selectedBlockType === "kpi_view" ||
        selectedBlockType === "input"
      ) {
        requestRibbonTab("element");
      } else if (
        selectedBlockType === "data_source" ||
        selectedBlockType?.startsWith("data_")
      ) {
        requestRibbonTab("data");
      }
    },
    [clearPartSelections, configRef, flushActiveTextEdit, requestRibbonTab],
  );

  const clearSelection = useCallback(() => {
    flushActiveTextEdit();
    setSelectedIds([]);
    setEditingTextId(null);
    clearPartSelections();
  }, [clearPartSelections, flushActiveTextEdit]);

  const selectChartPart = useCallback(
    (blockId: string, part: ComunicadoChartPartRef) => {
      flushActiveTextEdit();
      setSelectedIds([blockId]);
      setEditingTextId(null);
      setSelectedTablePart(null);
      setSelectedKpiPart(null);
      setEditingKpiPart(null);
      setSelectedInputPart(null);
      setSelectedChartPart(part);
      setEditingChartPart(null);
      requestRibbonTab("element");
    },
    [flushActiveTextEdit, requestRibbonTab],
  );

  const clearChartPartSelection = useCallback(() => {
    setSelectedChartPart(null);
    setEditingChartPart(null);
    setSelectedTablePart(null);
    setSelectedKpiPart(null);
    setEditingKpiPart(null);
    setSelectedInputPart(null);
  }, []);

  const selectTablePart = useCallback(
    (
      blockId: string,
      part: ComunicadoTablePartRef,
      options?: { additive?: boolean; range?: boolean },
    ) => {
      flushActiveTextEdit();
      setSelectedIds([blockId]);
      setEditingTextId(null);
      setSelectedChartPart(null);
      setEditingChartPart(null);
      setSelectedTablePart(null);
      setEditingTablePart(null);
      setSelectedKpiPart(null);
      setEditingKpiPart(null);
      setSelectedInputPart(null);
      setSelectedTableParts((current) => {
        /* Multi-seleção só entre colunas (headerCell) — Excel-like. */
        if (part.kind === "headerCell" && (options?.additive || options?.range)) {
          const headerCells = current.filter(
            (item): item is Extract<ComunicadoTablePartRef, { kind: "headerCell" }> =>
              item.kind === "headerCell",
          );
          if (options.range && headerCells.length > 0) {
            const anchor = headerCells[headerCells.length - 1];
            const start = Math.min(anchor.colIndex, part.colIndex);
            const end = Math.max(anchor.colIndex, part.colIndex);
            const range: ComunicadoTablePartRef[] = [];
            for (let colIndex = start; colIndex <= end; colIndex += 1) {
              if (colIndex !== part.colIndex) range.push({ kind: "headerCell", colIndex });
            }
            return [...range, part];
          }
          if (options.additive && headerCells.length > 0) {
            const already = headerCells.some((item) => isTablePartRefEqual(item, part));
            if (already) return headerCells.filter((item) => !isTablePartRefEqual(item, part));
            return [...headerCells, part];
          }
        }
        return [part];
      });
      requestRibbonTab("element");
    },
    [flushActiveTextEdit, requestRibbonTab],
  );

  const clearTablePartSelection = useCallback(() => {
    setSelectedTableParts([]);
    setEditingTablePart(null);
  }, []);

  const selectKpiPart = useCallback(
    (blockId: string, part: ComunicadoKpiPartRef) => {
      flushActiveTextEdit();
      setSelectedIds([blockId]);
      setEditingTextId(null);
      setSelectedChartPart(null);
      setEditingChartPart(null);
      setSelectedTablePart(null);
      setSelectedInputPart(null);
      setSelectedKpiPart(part);
      setEditingKpiPart(null);
      requestRibbonTab("element");
    },
    [flushActiveTextEdit, requestRibbonTab],
  );

  const clearKpiPartSelection = useCallback(() => {
    setSelectedKpiPart(null);
    setEditingKpiPart(null);
  }, []);

  const selectInputPart = useCallback(
    (blockId: string, part: ComunicadoInputPartRef) => {
      flushActiveTextEdit();
      setSelectedIds([blockId]);
      setEditingTextId(null);
      setSelectedChartPart(null);
      setEditingChartPart(null);
      setSelectedTablePart(null);
      setSelectedKpiPart(null);
      setEditingKpiPart(null);
      setSelectedInputPart(part);
      requestRibbonTab("element");
    },
    [flushActiveTextEdit, requestRibbonTab],
  );

  const clearInputPartSelection = useCallback(() => {
    setSelectedInputPart(null);
  }, []);

  const beginEditChartPart = useCallback(
    (blockId: string, part: ComunicadoChartPartRef) => {
      flushActiveTextEdit();
      setSelectedIds([blockId]);
      setEditingTextId(null);
      setSelectedChartPart(part);
      setEditingChartPart(part);
      setSelectedTablePart(null);
      setEditingTablePart(null);
      setSelectedKpiPart(null);
      setEditingKpiPart(null);
    },
    [flushActiveTextEdit, setSelectedTablePart],
  );

  const cancelEditChartPart = useCallback(() => {
    setEditingChartPart(null);
  }, []);

  const beginEditTablePart = useCallback(
    (blockId: string, part: ComunicadoTablePartRef) => {
      flushActiveTextEdit();
      setSelectedIds([blockId]);
      setEditingTextId(null);
      setSelectedChartPart(null);
      setEditingChartPart(null);
      setSelectedKpiPart(null);
      setEditingKpiPart(null);
      setSelectedTableParts([part]);
      setEditingTablePart(part);
    },
    [flushActiveTextEdit],
  );

  const cancelEditTablePart = useCallback(() => {
    setEditingTablePart(null);
  }, []);

  const beginEditKpiPart = useCallback(
    (blockId: string, part: ComunicadoKpiPartRef) => {
      flushActiveTextEdit();
      setSelectedIds([blockId]);
      setEditingTextId(null);
      setSelectedChartPart(null);
      setEditingChartPart(null);
      setSelectedTablePart(null);
      setEditingTablePart(null);
      setSelectedKpiPart(part);
      setEditingKpiPart(part);
    },
    [flushActiveTextEdit, setSelectedTablePart],
  );

  const cancelEditKpiPart = useCallback(() => {
    setEditingKpiPart(null);
  }, []);

  const isBlockSelected = useCallback(
    (blockId: string) => selectedIds.includes(blockId),
    [selectedIds],
  );

  const selected = useMemo(
    () => (selectedId ? blocks.find((block) => block.id === selectedId) ?? null : null),
    [blocks, selectedId],
  );

  const selectedBlocks = useMemo(
    () => blocks.filter((block) => selectedIds.includes(block.id)),
    [blocks, selectedIds],
  );

  const setEditingTextIdWithSelection = useCallback(
    (id: string | null) => {
      if (editingTextIdRef.current && editingTextIdRef.current !== id) {
        flushActiveTextEdit(editingTextIdRef.current);
      }
      setEditingTextId(id);
      if (!id) clearTextEditUi();
    },
    [clearTextEditUi, flushActiveTextEdit],
  );

  const registerTextEditorBridge = useCallback((blockId: string, bridge: TextEditorBridge | null) => {
    if (bridge) textEditorBridgesRef.current.set(blockId, bridge);
    else textEditorBridgesRef.current.delete(blockId);
  }, []);

  const reportTextEditSelection = useCallback((
    selection: TextEditSelection | null,
    runs?: ComunicadoContentRun[],
  ) => {
    setTextEditSelection(selection);
    if (!selection) {
      setTextEditSelectionStyle(null);
      setTextEditListSelection(null);
      setTextEditNamedStyleSelection(null);
      return;
    }

    const resolvedBlock = configRef.current.blocks?.find((item) => item.id === selection.blockId);
    const resolvedRuns = (() => {
      if (runs) return runs;
      if (!resolvedBlock || (resolvedBlock.type !== "heading" && resolvedBlock.type !== "text")) {
        return null;
      }
      return resolveTextBlockDisplayRuns(resolvedBlock);
    })();

    if (!resolvedRuns || !resolvedBlock || (resolvedBlock.type !== "heading" && resolvedBlock.type !== "text")) {
      setTextEditSelectionStyle(null);
      setTextEditListSelection(null);
      setTextEditNamedStyleSelection(null);
      return;
    }

    if (selection.start >= selection.end) {
      setTextEditSelectionStyle(null);
      setTextEditListSelection(
        selectionListTypeState(resolvedRuns, selection.start, selection.start),
      );
      setTextEditNamedStyleSelection(
        resolveNamedStyleSelectionForBlock(resolvedBlock, selection.start, selection.start),
      );
      return;
    }

    setTextEditSelectionStyle(
      selectionRunStyleState(resolvedRuns, selection.start, selection.end),
    );
    setTextEditListSelection(
      selectionListTypeState(resolvedRuns, selection.start, selection.end),
    );
    setTextEditNamedStyleSelection(
      selectionNamedStyleState(resolvedRuns, selection.start, selection.end) ??
        defaultNamedStyleForBlockType(resolvedBlock.type),
    );
  }, [configRef]);

  const toggleEditingTextRunStyle = useCallback((toggleKey: ContentRunStyleToggleKey) => {
    if (!editingTextId) return;
    const bridge = textEditorBridgesRef.current.get(editingTextId);
    bridge?.applyPartialStyleToggle(toggleKey);
  }, [editingTextId]);

  const toggleSelectedTextListType = useCallback((listType: ComunicadoListType) => {
    let target: ComunicadoBlock | null =
      editingTextId != null
        ? configRef.current.blocks?.find((block) => block.id === editingTextId) ?? null
        : selected && isComunicadoVisualBoxBlock(selected)
          ? selected
          : null;
    if (!target || !isComunicadoVisualBoxBlock(target)) return;

    if (target.type === "shape") {
      const rich = visualBoxEnsureRichTextBlock(target);
      const nextBlocks = (configRef.current.blocks ?? []).map((block) =>
        block.id === rich.id ? rich : block,
      );
      updateBlocksRef.current(nextBlocks);
      target = rich;
    }

    if (target.type !== "heading" && target.type !== "text") return;

    if (editingTextId === target.id) {
      const bridge = textEditorBridgesRef.current.get(editingTextId);
      bridge?.applyListToggle(listType);
      return;
    }

    const runs = resolveTextBlockDisplayRuns(target);
    const nextRuns = toggleListTypeOnAllLines(runs, listType);
    updateBlockTextFieldsRef.current(target.id, syncTextBlockFromRuns(nextRuns));
  }, [configRef, editingTextId, selected, updateBlockTextFieldsRef, updateBlocksRef]);

  const applySelectedNamedTextStyle = useCallback((namedStyle: ComunicadoNamedTextStyle) => {
    let target: ComunicadoBlock | null =
      editingTextId != null
        ? configRef.current.blocks?.find((block) => block.id === editingTextId) ?? null
        : selected && isComunicadoVisualBoxBlock(selected)
          ? selected
          : null;
    if (!target || !isComunicadoVisualBoxBlock(target)) return;

    if (target.type === "shape") {
      const rich = visualBoxEnsureRichTextBlock(target);
      const nextBlocks = (configRef.current.blocks ?? []).map((block) =>
        block.id === rich.id ? rich : block,
      );
      updateBlocksRef.current(nextBlocks);
      target = rich;
    }

    if (target.type !== "heading" && target.type !== "text") return;

    if (editingTextId === target.id) {
      const bridge = textEditorBridgesRef.current.get(editingTextId);
      bridge?.applyNamedStyleToggle(namedStyle);
      return;
    }

    const runs = resolveTextBlockDisplayRuns(target);
    const nextRuns = applyNamedStyleOnAllLines(runs, namedStyle);
    updateBlockTextFieldsRef.current(target.id, syncTextBlockFromRuns(nextRuns));
  }, [configRef, editingTextId, selected, updateBlockTextFieldsRef, updateBlocksRef]);

  const insertDataFieldAtCursor = useCallback(() => {
    if (!editingTextId) return;
    const block = configRef.current.blocks?.find((item) => item.id === editingTextId);
    if (!block || !isComunicadoVisualBoxBlock(block)) return;
    const sourceId = block.dataSourceId?.trim();
    if (!sourceId) return;
    const source = configRef.current.blocks?.find((item) => item.id === sourceId);
    const resolved =
      source && "resolved" in source && source.resolved ? source.resolved : undefined;
    const projection =
      block.textProjection ??
      suggestDefaultTextProjection(resolved) ??
      undefined;
    const field = projection?.field?.trim();
    if (!field) return;
    const bridge = textEditorBridgesRef.current.get(editingTextId);
    bridge?.insertDataRefAtSelection?.({
      field,
      aggregation: projection?.aggregation,
      format: projection?.format,
      label: field,
    });
  }, [configRef, editingTextId]);

  /** Ao trocar de slide: limpa seleção (não auto-seleciona o 1º bloco). */
  const resetSelectionForSlide = useCallback(() => {
    setSelectedIds([]);
    setEditingTextId(null);
    clearPartSelections();
    clearTextEditUi();
  }, [clearPartSelections, clearTextEditUi]);

  return {
    selectedIds,
    setSelectedIds,
    selectedId,
    selected,
    selectedBlocks,
    isBlockSelected,
    selectBlock,
    selectBlocksByIds,
    clearSelection,
    setSelectedId,
    selectedChartPart,
    setSelectedChartPart,
    selectChartPart,
    clearChartPartSelection,
    editingChartPart,
    setEditingChartPart,
    beginEditChartPart,
    cancelEditChartPart,
    selectedTablePart,
    selectedTableParts,
    setSelectedTablePart,
    selectTablePart,
    clearTablePartSelection,
    editingTablePart,
    beginEditTablePart,
    cancelEditTablePart,
    selectedKpiPart,
    setSelectedKpiPart,
    selectKpiPart,
    clearKpiPartSelection,
    editingKpiPart,
    setEditingKpiPart,
    beginEditKpiPart,
    cancelEditKpiPart,
    selectedInputPart,
    setSelectedInputPart,
    selectInputPart,
    clearInputPartSelection,
    editingTextId,
    setEditingTextId: setEditingTextIdWithSelection,
    textEditSelection,
    textEditSelectionStyle,
    textEditListSelection,
    textEditNamedStyleSelection,
    registerTextEditorBridge,
    reportTextEditSelection,
    toggleEditingTextRunStyle,
    toggleSelectedTextListType,
    applySelectedNamedTextStyle,
    insertDataFieldAtCursor,
    ribbonTabRequest,
    setRibbonTabRequest,
    requestRibbonTab,
    clearRibbonTabRequest,
    openLayersPanel,
    selectionPanelTab,
    setSelectionPanelTab,
    resetSelectionForSlide,
    flushActiveTextEdit,
  };
}
