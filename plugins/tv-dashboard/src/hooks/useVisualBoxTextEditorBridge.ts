import { useCallback, useRef, type MutableRefObject, type RefObject } from "react";
import {
  applyContentRunStyleInRange,
  applyNamedStyleInRange,
  contentRunsFromEditableRoot,
  getEditableTextSelectionOffsets,
  insertDataRefAtOffset,
  insertLineBreakAtOffset,
  plainTextFromContentRuns,
  syncTextBlockFromRuns,
  toggleContentRunStyleInRange,
  toggleListTypeInRange,
  type ComunicadoContentRun,
  type ComunicadoListType,
  type ComunicadoNamedTextStyle,
  type ComunicadoTextDataRef,
  type ContentRunStylePatch,
  type ContentRunStyleToggleKey,
} from "@delpi/tv-dashboard-presentation";

type TextFields = { content: string; contentRuns?: ComunicadoContentRun[] };
type TextRange = { start: number; end: number };

type Options = {
  blockId: string;
  editorRef: RefObject<HTMLElement | null>;
  draftRef: MutableRefObject<TextFields>;
  renderedSignatureRef: MutableRefObject<string>;
  syncEditorHtml: (
    runs?: ComunicadoContentRun[],
    selectionOverride?: { start: number; end: number } | null,
  ) => void;
  commitDraft: (runs?: ComunicadoContentRun[]) => void;
  reportTextEditSelection: (
    selection: { blockId: string; start: number; end: number } | null,
    runs?: ComunicadoContentRun[],
  ) => void;
  /** Pós-processa runs do DOM antes de gravar (ex.: separar href do texto). */
  normalizeEditorRuns?: (runs: ComunicadoContentRun[]) => ComunicadoContentRun[];
  /**
   * Após inserir `dataRef`: grava no bloco (Text limpa `textProjection`; Shape só runs).
   * Sem callback, a inserção só atualiza draft/editor local.
   */
  onDataRefInserted?: (runs: ComunicadoContentRun[]) => void;
};

/**
 * Bridge canônico de edição rich-text da caixa visual (text / heading / shape).
 * Ribbon e atalhos só falam com estes handlers — sem duplicar lógica por tipo.
 */
export function useVisualBoxTextEditorBridge({
  blockId,
  editorRef,
  draftRef,
  renderedSignatureRef,
  syncEditorHtml,
  commitDraft,
  reportTextEditSelection,
  normalizeEditorRuns,
  onDataRefInserted,
}: Options) {
  /** Última seleção parcial — fallback se o clique na ribbon perder o Range do DOM. */
  const lastPartialRangeRef = useRef<TextRange | null>(null);

  const resolvePartialRange = useCallback((): TextRange | null => {
    const editor = editorRef.current;
    if (!editor) return null;
    const live = getEditableTextSelectionOffsets(editor);
    if (live && live.end > live.start) {
      lastPartialRangeRef.current = live;
      return live;
    }
    const fallback = lastPartialRangeRef.current;
    if (fallback && fallback.end > fallback.start) return fallback;
    return null;
  }, [editorRef]);

  const readRuns = useCallback((): ComunicadoContentRun[] | null => {
    const editor = editorRef.current;
    if (!editor) return null;
    const raw = contentRunsFromEditableRoot(editor);
    return normalizeEditorRuns ? normalizeEditorRuns(raw) : raw;
  }, [editorRef, normalizeEditorRuns]);

  const applyPartialStyleToggle = useCallback(
    (toggleKey: ContentRunStyleToggleKey) => {
      const editor = editorRef.current;
      if (!editor) return;
      const selection = resolvePartialRange();
      if (!selection) return;
      const runs = contentRunsFromEditableRoot(editor);
      const nextRuns = toggleContentRunStyleInRange(
        runs,
        selection.start,
        selection.end,
        toggleKey,
      );
      const normalized = normalizeEditorRuns ? normalizeEditorRuns(nextRuns) : nextRuns;
      draftRef.current = syncTextBlockFromRuns(normalized);
      renderedSignatureRef.current = "";
      syncEditorHtml(nextRuns, { start: selection.start, end: selection.end });
      commitDraft(nextRuns);
      reportTextEditSelection(
        { blockId, start: selection.start, end: selection.end },
        nextRuns,
      );
    },
    [
      blockId,
      commitDraft,
      draftRef,
      editorRef,
      normalizeEditorRuns,
      renderedSignatureRef,
      reportTextEditSelection,
      resolvePartialRange,
      syncEditorHtml,
    ],
  );

  const applyPartialStylePatch = useCallback(
    (patch: ContentRunStylePatch) => {
      const editor = editorRef.current;
      if (!editor) return;
      const selection = resolvePartialRange();
      if (!selection) return;
      const runs = contentRunsFromEditableRoot(editor);
      const nextRuns = applyContentRunStyleInRange(
        runs,
        selection.start,
        selection.end,
        patch,
      );
      const normalized = normalizeEditorRuns ? normalizeEditorRuns(nextRuns) : nextRuns;
      draftRef.current = syncTextBlockFromRuns(normalized);
      renderedSignatureRef.current = "";
      syncEditorHtml(nextRuns, { start: selection.start, end: selection.end });
      commitDraft(nextRuns);
      reportTextEditSelection(
        { blockId, start: selection.start, end: selection.end },
        nextRuns,
      );
    },
    [
      blockId,
      commitDraft,
      draftRef,
      editorRef,
      normalizeEditorRuns,
      renderedSignatureRef,
      reportTextEditSelection,
      resolvePartialRange,
      syncEditorHtml,
    ],
  );

  const applyListToggle = useCallback(
    (listType: ComunicadoListType) => {
      const editor = editorRef.current;
      if (!editor) return;
      const selection = getEditableTextSelectionOffsets(editor);
      const partial = resolvePartialRange();
      const runs = contentRunsFromEditableRoot(editor);
      const start = partial?.start ?? selection?.start ?? plainTextFromContentRuns(runs).length;
      const end = partial?.end ?? selection?.end ?? start;
      const nextRuns = toggleListTypeInRange(runs, start, end, listType);
      const normalized = normalizeEditorRuns ? normalizeEditorRuns(nextRuns) : nextRuns;
      draftRef.current = syncTextBlockFromRuns(normalized);
      renderedSignatureRef.current = "";
      syncEditorHtml(nextRuns, { start, end });
      commitDraft(nextRuns);
      reportTextEditSelection({ blockId, start, end }, nextRuns);
    },
    [
      blockId,
      commitDraft,
      draftRef,
      editorRef,
      normalizeEditorRuns,
      renderedSignatureRef,
      reportTextEditSelection,
      resolvePartialRange,
      syncEditorHtml,
    ],
  );

  const applyNamedStyleToggle = useCallback(
    (namedStyle: ComunicadoNamedTextStyle) => {
      const editor = editorRef.current;
      if (!editor) return;
      const selection = getEditableTextSelectionOffsets(editor);
      const partial = resolvePartialRange();
      const runs = contentRunsFromEditableRoot(editor);
      const start = partial?.start ?? selection?.start ?? 0;
      const end = partial?.end ?? selection?.end ?? plainTextFromContentRuns(runs).length;
      const nextRuns = applyNamedStyleInRange(runs, start, end, namedStyle);
      const normalized = normalizeEditorRuns ? normalizeEditorRuns(nextRuns) : nextRuns;
      draftRef.current = syncTextBlockFromRuns(normalized);
      renderedSignatureRef.current = "";
      syncEditorHtml(nextRuns, { start, end });
      commitDraft(nextRuns);
      reportTextEditSelection({ blockId, start, end }, nextRuns);
    },
    [
      blockId,
      commitDraft,
      draftRef,
      editorRef,
      normalizeEditorRuns,
      renderedSignatureRef,
      reportTextEditSelection,
      resolvePartialRange,
      syncEditorHtml,
    ],
  );

  const insertLineBreak = useCallback(() => {
    const editor = editorRef.current;
    if (!editor) return;
    const selection = getEditableTextSelectionOffsets(editor);
    if (!selection) return;
    const runs = contentRunsFromEditableRoot(editor);
    const nextRuns = insertLineBreakAtOffset(runs, selection.start);
    const nextOffset = selection.start + 1;
    const normalized = normalizeEditorRuns ? normalizeEditorRuns(nextRuns) : nextRuns;
    draftRef.current = syncTextBlockFromRuns(normalized);
    renderedSignatureRef.current = "";
    syncEditorHtml(nextRuns, { start: nextOffset, end: nextOffset });
    commitDraft(nextRuns);
    reportTextEditSelection({ blockId, start: nextOffset, end: nextOffset }, nextRuns);
  }, [
    blockId,
    commitDraft,
    draftRef,
    editorRef,
    normalizeEditorRuns,
    renderedSignatureRef,
    reportTextEditSelection,
    syncEditorHtml,
  ]);

  const insertDataRefAtSelection = useCallback(
    (dataRef: ComunicadoTextDataRef) => {
      const editor = editorRef.current;
      if (!editor) return;
      const raw = contentRunsFromEditableRoot(editor);
      const runs = normalizeEditorRuns ? normalizeEditorRuns(raw) : raw;
      const selection = getEditableTextSelectionOffsets(editor);
      const offset = selection?.start ?? plainTextFromContentRuns(runs).length;
      const nextRuns = insertDataRefAtOffset(runs, offset, dataRef);
      const nextOffset = offset + 1;
      const normalized = normalizeEditorRuns ? normalizeEditorRuns(nextRuns) : nextRuns;
      draftRef.current = syncTextBlockFromRuns(normalized);
      renderedSignatureRef.current = "";
      syncEditorHtml(nextRuns, { start: nextOffset, end: nextOffset });
      if (onDataRefInserted) {
        onDataRefInserted(nextRuns);
      } else {
        commitDraft(nextRuns);
      }
      reportTextEditSelection({ blockId, start: nextOffset, end: nextOffset }, nextRuns);
    },
    [
      blockId,
      commitDraft,
      draftRef,
      editorRef,
      normalizeEditorRuns,
      onDataRefInserted,
      renderedSignatureRef,
      reportTextEditSelection,
      syncEditorHtml,
    ],
  );

  const reportSelectionFromEditor = useCallback(() => {
    const editor = editorRef.current;
    if (!editor) return;
    const offsets = getEditableTextSelectionOffsets(editor);
    if (!offsets) {
      /* Não zerar estado — clique na ribbon pode remover o Range sem sair da edição. */
      return;
    }
    if (offsets.end > offsets.start) {
      lastPartialRangeRef.current = offsets;
    }
    const runs = contentRunsFromEditableRoot(editor);
    reportTextEditSelection({ blockId, ...offsets }, runs);
  }, [blockId, editorRef, reportTextEditSelection]);

  const clearPartialRangeFallback = useCallback(() => {
    lastPartialRangeRef.current = null;
  }, []);

  return {
    applyPartialStyleToggle,
    applyPartialStylePatch,
    applyListToggle,
    applyNamedStyleToggle,
    insertLineBreak,
    insertDataRefAtSelection,
    reportSelectionFromEditor,
    readRuns,
    clearPartialRangeFallback,
  };
}
