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
  isInputPartRefEqual,
  isKpiPartRefEqual,
  isTablePartRefEqual,
  resolveNamedStyleSelectionForBlock,
  resolveStageSelectionTargetId,
  resolveTextBlockDisplayRuns,
  selectionListTypeState,
  selectionNamedStyleState,
  selectionRunStyleState,
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
  type DynamicContentSpec,
} from "@delpi/tv-dashboard-presentation";
import { applyDynamicContent } from "../../utils/applyDynamicContent";

import type {
  ComunicadoCanvasTableCellSelection,
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
import { toggleCompositePartSelection } from "../../utils/compositePartSelection";

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
  /**
   * Modo filhos do grupo: Shift/Camadas/`expandGroup: false`.
   * Permite selecionar todos os irmãos sem promover ao chrome do grupo fechado.
   */
  const [preferGroupChildrenSelection, setPreferGroupChildrenSelection] = useState(false);
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
  /** Multi-seleção de partes KPI — o último item é a parte primária (como table). */
  const [selectedKpiParts, setSelectedKpiParts] = useState<ComunicadoKpiPartRef[]>([]);
  const selectedKpiPart = selectedKpiParts[selectedKpiParts.length - 1] ?? null;
  const setSelectedKpiPart = useCallback(
    (value: SetStateAction<ComunicadoKpiPartRef | null>) => {
      setSelectedKpiParts((current) => {
        const primary = current[current.length - 1] ?? null;
        const next = typeof value === "function" ? value(primary) : value;
        return next ? [next] : [];
      });
    },
    [],
  );
  /** Grade — célula selecionada (chrome + inspetor). */
  const [selectedCanvasTableCell, setSelectedCanvasTableCell] =
    useState<ComunicadoCanvasTableCellSelection | null>(null);
  const [editingKpiPart, setEditingKpiPart] = useState<ComunicadoKpiPartRef | null>(null);
  /** Multi-seleção de partes do filtro — último = primária. */
  const [selectedInputParts, setSelectedInputParts] = useState<ComunicadoInputPartRef[]>([]);
  const selectedInputPart = selectedInputParts[selectedInputParts.length - 1] ?? null;
  const setSelectedInputPart = useCallback(
    (value: SetStateAction<ComunicadoInputPartRef | null>) => {
      setSelectedInputParts((current) => {
        const primary = current[current.length - 1] ?? null;
        const next = typeof value === "function" ? value(primary) : value;
        return next ? [next] : [];
      });
    },
    [],
  );
  const [textEditSelection, setTextEditSelection] = useState<TextEditSelection | null>(null);
  /**
   * Última seleção parcial enquanto a edição inline está ativa.
   * Sobrevive quando o Range do DOM some (clique na ribbon / blur temporário).
   */
  const [lastPartialTextEditSelection, setLastPartialTextEditSelection] =
    useState<TextEditSelection | null>(null);
  const [textFormatContextMenu, setTextFormatContextMenu] = useState<{
    x: number;
    y: number;
  } | null>(null);
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
    /* Só painel lateral — não pedir aba Camadas na top bar (esconde o ribbon). */
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
    setSelectedCanvasTableCell(null);
  }, [setSelectedInputPart, setSelectedKpiPart, setSelectedTablePart]);

  const clearTextEditUi = useCallback(() => {
    setTextEditSelection(null);
    setLastPartialTextEditSelection(null);
    setTextFormatContextMenu(null);
    setTextEditSelectionStyle(null);
    setTextEditListSelection(null);
    setTextEditNamedStyleSelection(null);
  }, []);

  const openTextFormatContextMenu = useCallback((position: { x: number; y: number }) => {
    setTextFormatContextMenu(position);
  }, []);

  const closeTextFormatContextMenu = useCallback(() => {
    setTextFormatContextMenu(null);
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
      setPreferGroupChildrenSelection(false);
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
      /* Marquee / nó do grupo / Esc → seleção pai fechada quando couber. */
      setPreferGroupChildrenSelection(false);
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
          setPreferGroupChildrenSelection(false);
          setEditingTextId(null);
          clearPartSelections();
        }
        return;
      }
      /*
       * expandGroup === false → modo filhos (Shift/Camadas/isolate).
       * Default true → grupo fechado / bloco solto.
       */
      const preferChildren = options?.expandGroup === false;
      let selectedBlockType: string | undefined;
      if (options?.subtract) {
        setSelectedIds((current) => {
          const remove = new Set<string>([targetId]);
          const block = blocksNow.find((item) => item.id === targetId);
          /*
           * Em modo filhos, Ctrl remove só o membro — não o grupo inteiro.
           * No grupo fechado (preferChildren false), remove todos os membros.
           */
          if (block?.groupId && !preferChildren) {
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
        setPreferGroupChildrenSelection(preferChildren);
        setEditingTextId(null);
        clearPartSelections();
        return;
      }
      setPreferGroupChildrenSelection(preferChildren);
      if (options?.additive) {
        setSelectedIds((current) => {
          const block = blocksNow.find((item) => item.id === targetId);
          const expandGroup = options?.expandGroup !== false;
          const idsToToggle =
            expandGroup && block?.groupId
              ? blocksNow
                  .filter((item) => item.groupId === block.groupId)
                  .map((item) => item.id)
              : [targetId];
          const set = new Set(current);
          const allPresent = idsToToggle.every((id) => set.has(id));
          if (allPresent) {
            for (const id of idsToToggle) set.delete(id);
          } else {
            for (const id of idsToToggle) set.add(id);
          }
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
        selectedBlockType === "canvas_table" ||
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
    setPreferGroupChildrenSelection(false);
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
      setSelectedCanvasTableCell(null);
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
      setEditingTablePart(null);
      setSelectedKpiPart(null);
      setEditingKpiPart(null);
      setSelectedInputPart(null);
      setSelectedCanvasTableCell(null);
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
    (blockId: string, part: ComunicadoKpiPartRef, options?: { additive?: boolean }) => {
      flushActiveTextEdit();
      setSelectedIds([blockId]);
      setEditingTextId(null);
      setSelectedChartPart(null);
      setEditingChartPart(null);
      setSelectedTablePart(null);
      setSelectedInputPart(null);
      setEditingKpiPart(null);
      setSelectedCanvasTableCell(null);
      setSelectedKpiParts((current) =>
        toggleCompositePartSelection({
          blockType: "kpi_view",
          current,
          next: part,
          equal: isKpiPartRefEqual,
          additive: options?.additive,
        }),
      );
      requestRibbonTab("element");
    },
    [flushActiveTextEdit, requestRibbonTab, setSelectedInputPart, setSelectedTablePart],
  );

  const clearKpiPartSelection = useCallback(() => {
    setSelectedKpiPart(null);
    setEditingKpiPart(null);
  }, [setSelectedKpiPart]);

  const selectInputPart = useCallback(
    (blockId: string, part: ComunicadoInputPartRef, options?: { additive?: boolean }) => {
      flushActiveTextEdit();
      setSelectedIds([blockId]);
      setEditingTextId(null);
      setSelectedChartPart(null);
      setEditingChartPart(null);
      setSelectedTablePart(null);
      setSelectedKpiPart(null);
      setEditingKpiPart(null);
      setSelectedCanvasTableCell(null);
      setSelectedInputParts((current) =>
        toggleCompositePartSelection({
          blockType: "input",
          current,
          next: part,
          equal: isInputPartRefEqual,
          additive: options?.additive,
        }),
      );
      requestRibbonTab("element");
    },
    [flushActiveTextEdit, requestRibbonTab, setSelectedKpiPart, setSelectedTablePart],
  );

  const clearInputPartSelection = useCallback(() => {
    setSelectedInputPart(null);
  }, [setSelectedInputPart]);

  const selectCanvasTableCell = useCallback(
    (blockId: string, cell: { row: number; col: number } | null) => {
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
      setSelectedCanvasTableCell(
        cell ? { blockId, row: cell.row, col: cell.col } : null,
      );
      requestRibbonTab("canvasTable");
    },
    [flushActiveTextEdit, requestRibbonTab, setSelectedInputPart, setSelectedKpiPart, setSelectedTablePart],
  );

  const clearCanvasTableCellSelection = useCallback(() => {
    setSelectedCanvasTableCell(null);
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

  /**
   * Entra em edição inline (L5): isola o bloco (sem reexpandir grupo) e ativa caret.
   * Preferir a `selectBlock` + `setEditingTextId` soltos — evita conflito com grupo fechado.
   */
  const enterTextEdit = useCallback(
    (blockId: string) => {
      const blocksNow = configRef.current.blocks ?? [];
      const targetId = resolveStageSelectionTargetId(blockId, blocksNow);
      if (!targetId) return;
      const block = blocksNow.find((item) => item.id === targetId);
      if (!block) return;
      if (block.type !== "heading" && block.type !== "text" && block.type !== "shape") {
        return;
      }

      if (editingTextIdRef.current && editingTextIdRef.current !== targetId) {
        flushActiveTextEdit(editingTextIdRef.current);
      }

      setSelectedIds([targetId]);
      clearPartSelections();
      setEditingTextId(targetId);
      clearTextEditUi();
      requestRibbonTab(block.type === "shape" ? "shape" : "element");
    },
    [clearPartSelections, clearTextEditUi, configRef, flushActiveTextEdit, requestRibbonTab],
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
    if (selection && selection.end > selection.start) {
      setLastPartialTextEditSelection(selection);
    }
    if (!selection) {
      setTextEditSelectionStyle(null);
      setTextEditListSelection(null);
      setTextEditNamedStyleSelection(null);
      return;
    }

    const resolvedBlock = configRef.current.blocks?.find((item) => item.id === selection.blockId);
    const isVisualText =
      resolvedBlock &&
      (resolvedBlock.type === "heading" ||
        resolvedBlock.type === "text" ||
        resolvedBlock.type === "shape");
    const resolvedRuns = (() => {
      if (runs) return runs;
      if (!resolvedBlock || !isVisualText) return null;
      if (resolvedBlock.type === "shape") {
        return (
          resolvedBlock.contentRuns?.length
            ? resolvedBlock.contentRuns
            : [{ text: resolvedBlock.content ?? "" }]
        );
      }
      return resolveTextBlockDisplayRuns(resolvedBlock);
    })();

    if (!resolvedRuns || !resolvedBlock || !isVisualText) {
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
        resolvedBlock.type === "shape"
          ? defaultNamedStyleForBlockType("text")
          : resolveNamedStyleSelectionForBlock(resolvedBlock, selection.start, selection.start),
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
        defaultNamedStyleForBlockType(resolvedBlock.type === "shape" ? "text" : resolvedBlock.type),
    );
  }, [configRef]);

  const resolveActiveTextBridgeId = useCallback((): string | null => {
    if (editingTextId) return editingTextId;
    if (editingKpiPart || editingChartPart) {
      return selectedIds[selectedIds.length - 1] ?? null;
    }
    return null;
  }, [editingChartPart, editingKpiPart, editingTextId, selectedIds]);

  const toggleEditingTextRunStyle = useCallback(
    (toggleKey: ContentRunStyleToggleKey): boolean => {
      const bridgeId = resolveActiveTextBridgeId();
      if (!bridgeId) return false;
      const bridge = textEditorBridgesRef.current.get(bridgeId);
      if (!bridge) return false;
      /* Garante lastPartial a partir do DOM antes do clique na ribbon. */
      bridge.refreshSelectionState?.();
      return Boolean(bridge.applyPartialStyleToggle(toggleKey));
    },
    [resolveActiveTextBridgeId],
  );

  const applyEditingTextRunStylePatch = useCallback(
    (patch: import("@delpi/tv-dashboard-presentation").ContentRunStylePatch): boolean => {
      const bridgeId = resolveActiveTextBridgeId();
      if (!bridgeId) return false;
      const bridge = textEditorBridgesRef.current.get(bridgeId);
      if (!bridge?.applyPartialStylePatch) return false;
      bridge.refreshSelectionState?.();
      return Boolean(bridge.applyPartialStylePatch(patch));
    },
    [resolveActiveTextBridgeId],
  );

  const toggleSelectedTextListType = useCallback((listType: ComunicadoListType) => {
    let target: ComunicadoBlock | null =
      editingTextId != null
        ? configRef.current.blocks?.find((block) => block.id === editingTextId) ?? null
        : selected && isComunicadoVisualBoxBlock(selected)
          ? selected
          : null;
    if (!target || !isComunicadoVisualBoxBlock(target)) return;

    const rich = visualBoxEnsureRichTextBlock(target);
    if (rich !== target) {
      const nextBlocks = (configRef.current.blocks ?? []).map((block) =>
        block.id === rich.id ? rich : block,
      );
      updateBlocksRef.current(nextBlocks);
      target = rich;
    }

    if (editingTextId === target.id) {
      const bridge = textEditorBridgesRef.current.get(editingTextId);
      bridge?.applyListToggle(listType);
      return;
    }

    const runs = resolveTextBlockDisplayRuns({
      content: target.content ?? "",
      contentRuns: target.contentRuns,
      textProjection: target.textProjection,
      resolved: "resolved" in target ? target.resolved : undefined,
    });
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

    const rich = visualBoxEnsureRichTextBlock(target);
    if (rich !== target) {
      const nextBlocks = (configRef.current.blocks ?? []).map((block) =>
        block.id === rich.id ? rich : block,
      );
      updateBlocksRef.current(nextBlocks);
      target = rich;
    }

    if (editingTextId === target.id) {
      const bridge = textEditorBridgesRef.current.get(editingTextId);
      bridge?.applyNamedStyleToggle(namedStyle);
      return;
    }

    const runs = resolveTextBlockDisplayRuns({
      content: target.content ?? "",
      contentRuns: target.contentRuns,
      textProjection: target.textProjection,
      resolved: "resolved" in target ? target.resolved : undefined,
    });
    const nextRuns = applyNamedStyleOnAllLines(runs, namedStyle);
    updateBlockTextFieldsRef.current(target.id, syncTextBlockFromRuns(nextRuns));
  }, [configRef, editingTextId, selected, updateBlockTextFieldsRef, updateBlocksRef]);

  const applyDynamicContentSpec = useCallback(
    (spec: DynamicContentSpec) => {
      return applyDynamicContent(spec, {
        blocks: configRef.current.blocks ?? blocks,
        editingTextId,
        selectedCanvasTableCell,
        getTextEditorBridge: (blockId) => textEditorBridgesRef.current.get(blockId),
        updateBlock: (blockId, patch) => {
          const current = configRef.current.blocks ?? [];
          updateBlocksRef.current(
            current.map((block) => (block.id === blockId ? { ...block, ...patch } : block)),
          );
        },
      });
    },
    [blocks, configRef, editingTextId, selectedCanvasTableCell, updateBlocksRef],
  );

  /** @deprecated Preferir picker `{ }` → `applyDynamicContentSpec`. */
  const insertDataFieldAtCursor = useCallback(() => {
    /* Sem picker: no-op — o atalho abre DynamicContentInsertControl. */
  }, []);

  /** Ao trocar de slide: limpa seleção (não auto-seleciona o 1º bloco). */
  const resetSelectionForSlide = useCallback(() => {
    setSelectedIds([]);
    setPreferGroupChildrenSelection(false);
    setEditingTextId(null);
    clearPartSelections();
    clearTextEditUi();
  }, [clearPartSelections, clearTextEditUi]);

  return {
    selectedIds,
    setSelectedIds,
    preferGroupChildrenSelection,
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
    selectedKpiParts,
    setSelectedKpiPart,
    selectKpiPart,
    clearKpiPartSelection,
    editingKpiPart,
    setEditingKpiPart,
    beginEditKpiPart,
    cancelEditKpiPart,
    selectedInputPart,
    selectedInputParts,
    setSelectedInputPart,
    selectInputPart,
    clearInputPartSelection,
    selectedCanvasTableCell,
    selectCanvasTableCell,
    clearCanvasTableCellSelection,
    editingTextId,
    setEditingTextId: setEditingTextIdWithSelection,
    enterTextEdit,
    textEditSelection,
    lastPartialTextEditSelection,
    textFormatContextMenu,
    openTextFormatContextMenu,
    closeTextFormatContextMenu,
    textEditSelectionStyle,
    textEditListSelection,
    textEditNamedStyleSelection,
    registerTextEditorBridge,
    reportTextEditSelection,
    toggleEditingTextRunStyle,
    applyEditingTextRunStylePatch,
    toggleSelectedTextListType,
    applySelectedNamedTextStyle,
    insertDataFieldAtCursor,
    applyDynamicContentSpec,
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
