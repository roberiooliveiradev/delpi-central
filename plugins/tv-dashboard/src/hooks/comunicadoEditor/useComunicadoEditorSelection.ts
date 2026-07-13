import {
  useCallback,
  useMemo,
  useRef,
  useState,
  type MutableRefObject,
} from "react";

import {
  applyNamedStyleOnAllLines,
  defaultNamedStyleForBlockType,
  resolveNamedStyleSelectionForBlock,
  resolveTextBlockDisplayRuns,
  selectionListTypeState,
  selectionNamedStyleState,
  selectionRunStyleState,
  syncTextBlockFromRuns,
  toggleListTypeOnAllLines,
  type ComunicadoBlock,
  type ComunicadoConfig,
  type ComunicadoChartPartRef,
  type ComunicadoContentRun,
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
};

/**
 * Seleção de blocos / partes (chart, table, KPI) / edição de texto + ribbon tab request.
 */
export function useComunicadoEditorSelection({
  configRef,
  blocks,
  updateBlockTextFieldsRef,
}: Options) {
  /** Sem auto-seleção: Gerenciar / F5 abrem na Página Inicial, não em Elemento. */
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [editingTextId, setEditingTextId] = useState<string | null>(null);
  const [selectedChartPart, setSelectedChartPart] = useState<ComunicadoChartPartRef | null>(null);
  const [editingChartPart, setEditingChartPart] = useState<ComunicadoChartPartRef | null>(null);
  const [selectedTablePart, setSelectedTablePart] = useState<ComunicadoTablePartRef | null>(null);
  const [selectedKpiPart, setSelectedKpiPart] = useState<ComunicadoKpiPartRef | null>(null);
  const [editingKpiPart, setEditingKpiPart] = useState<ComunicadoKpiPartRef | null>(null);
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
  const [selectionPanelTab, setSelectionPanelTabState] = useState<SelectionPanelTab>("element");

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
    setSelectedKpiPart(null);
    setEditingKpiPart(null);
  }, []);

  const clearTextEditUi = useCallback(() => {
    setTextEditSelection(null);
    setTextEditSelectionStyle(null);
    setTextEditListSelection(null);
    setTextEditNamedStyleSelection(null);
  }, []);

  const selectedId = selectedIds[selectedIds.length - 1] ?? null;

  const setSelectedId = useCallback(
    (id: string | null) => {
      if (editingTextIdRef.current && editingTextIdRef.current !== id) {
        flushActiveTextEdit(editingTextIdRef.current);
      }
      setSelectedIds(id ? [id] : []);
      setEditingTextId((current) => (id === current ? current : null));
      clearPartSelections();
      if (!id) clearTextEditUi();
    },
    [clearPartSelections, clearTextEditUi, flushActiveTextEdit],
  );

  const selectBlocksByIds = useCallback(
    (blockIds: string[]) => {
      flushActiveTextEdit();
      const unique = [...new Set(blockIds.filter(Boolean))];
      setSelectedIds(unique);
      setEditingTextId(null);
      clearPartSelections();
    },
    [clearPartSelections, flushActiveTextEdit],
  );

  const selectBlock = useCallback(
    (blockId: string, options?: { additive?: boolean }) => {
      flushActiveTextEdit();
      let selectedBlockType: string | undefined;
      if (options?.additive) {
        setSelectedIds((current) => {
          const set = new Set(current);
          if (set.has(blockId)) set.delete(blockId);
          else set.add(blockId);
          return [...set];
        });
      } else {
        const block = configRef.current.blocks?.find((item) => item.id === blockId);
        selectedBlockType = block?.type;
        if (block?.groupId) {
          const memberIds =
            configRef.current.blocks
              ?.filter((item) => item.groupId === block.groupId)
              .map((item) => item.id) ?? [blockId];
          setSelectedIds(memberIds);
        } else {
          setSelectedIds([blockId]);
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
        selectedBlockType === "kpi_view"
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
  }, []);

  const selectTablePart = useCallback(
    (blockId: string, part: ComunicadoTablePartRef) => {
      flushActiveTextEdit();
      setSelectedIds([blockId]);
      setEditingTextId(null);
      setSelectedChartPart(null);
      setEditingChartPart(null);
      setSelectedKpiPart(null);
      setEditingKpiPart(null);
      setSelectedTablePart(part);
      requestRibbonTab("element");
    },
    [flushActiveTextEdit, requestRibbonTab],
  );

  const clearTablePartSelection = useCallback(() => {
    setSelectedTablePart(null);
  }, []);

  const selectKpiPart = useCallback(
    (blockId: string, part: ComunicadoKpiPartRef) => {
      flushActiveTextEdit();
      setSelectedIds([blockId]);
      setEditingTextId(null);
      setSelectedChartPart(null);
      setEditingChartPart(null);
      setSelectedTablePart(null);
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

  const beginEditChartPart = useCallback(
    (blockId: string, part: ComunicadoChartPartRef) => {
      flushActiveTextEdit();
      setSelectedIds([blockId]);
      setEditingTextId(null);
      setSelectedChartPart(part);
      setEditingChartPart(part);
      setSelectedKpiPart(null);
      setEditingKpiPart(null);
    },
    [flushActiveTextEdit],
  );

  const cancelEditChartPart = useCallback(() => {
    setEditingChartPart(null);
  }, []);

  const beginEditKpiPart = useCallback(
    (blockId: string, part: ComunicadoKpiPartRef) => {
      flushActiveTextEdit();
      setSelectedIds([blockId]);
      setEditingTextId(null);
      setSelectedChartPart(null);
      setEditingChartPart(null);
      setSelectedTablePart(null);
      setSelectedKpiPart(part);
      setEditingKpiPart(part);
    },
    [flushActiveTextEdit],
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
    const target =
      editingTextId != null
        ? configRef.current.blocks?.find((block) => block.id === editingTextId)
        : selected && (selected.type === "heading" || selected.type === "text")
          ? selected
          : null;
    if (!target || (target.type !== "heading" && target.type !== "text")) return;

    if (editingTextId === target.id) {
      const bridge = textEditorBridgesRef.current.get(editingTextId);
      bridge?.applyListToggle(listType);
      return;
    }

    const runs = resolveTextBlockDisplayRuns(target);
    const nextRuns = toggleListTypeOnAllLines(runs, listType);
    updateBlockTextFieldsRef.current(target.id, syncTextBlockFromRuns(nextRuns));
  }, [configRef, editingTextId, selected, updateBlockTextFieldsRef]);

  const applySelectedNamedTextStyle = useCallback((namedStyle: ComunicadoNamedTextStyle) => {
    const target =
      editingTextId != null
        ? configRef.current.blocks?.find((block) => block.id === editingTextId)
        : selected && (selected.type === "heading" || selected.type === "text")
          ? selected
          : null;
    if (!target || (target.type !== "heading" && target.type !== "text")) return;

    if (editingTextId === target.id) {
      const bridge = textEditorBridgesRef.current.get(editingTextId);
      bridge?.applyNamedStyleToggle(namedStyle);
      return;
    }

    const runs = resolveTextBlockDisplayRuns(target);
    const nextRuns = applyNamedStyleOnAllLines(runs, namedStyle);
    updateBlockTextFieldsRef.current(target.id, syncTextBlockFromRuns(nextRuns));
  }, [configRef, editingTextId, selected, updateBlockTextFieldsRef]);

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
    setSelectedTablePart,
    selectTablePart,
    clearTablePartSelection,
    selectedKpiPart,
    setSelectedKpiPart,
    selectKpiPart,
    clearKpiPartSelection,
    editingKpiPart,
    setEditingKpiPart,
    beginEditKpiPart,
    cancelEditKpiPart,
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
    ribbonTabRequest,
    setRibbonTabRequest,
    requestRibbonTab,
    clearRibbonTabRequest,
    selectionPanelTab,
    setSelectionPanelTab,
    resetSelectionForSlide,
    flushActiveTextEdit,
  };
}
