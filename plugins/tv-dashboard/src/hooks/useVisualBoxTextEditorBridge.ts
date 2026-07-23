import { useCallback, type MutableRefObject, type RefObject } from "react";
import {
  applyContentRunStyleInRange,
  applyNamedStyleInRange,
  contentRunsFromEditableRoot,
  getEditableTextSelectionOffsets,
  insertLineBreakAtOffset,
  plainTextFromContentRuns,
  syncTextBlockFromRuns,
  toggleContentRunStyleInRange,
  toggleListTypeInRange,
  type ComunicadoContentRun,
  type ComunicadoListType,
  type ComunicadoNamedTextStyle,
  type ContentRunStylePatch,
  type ContentRunStyleToggleKey,
} from "@delpi/tv-dashboard-presentation";

type TextFields = { content: string; contentRuns?: ComunicadoContentRun[] };

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
}: Options) {
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
      const selection = getEditableTextSelectionOffsets(editor);
      if (!selection || selection.start >= selection.end) return;
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
      syncEditorHtml,
    ],
  );

  const applyPartialStylePatch = useCallback(
    (patch: ContentRunStylePatch) => {
      const editor = editorRef.current;
      if (!editor) return;
      const selection = getEditableTextSelectionOffsets(editor);
      if (!selection || selection.start >= selection.end) return;
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
      syncEditorHtml,
    ],
  );

  const applyListToggle = useCallback(
    (listType: ComunicadoListType) => {
      const editor = editorRef.current;
      if (!editor) return;
      const selection = getEditableTextSelectionOffsets(editor);
      const runs = contentRunsFromEditableRoot(editor);
      const start = selection?.start ?? plainTextFromContentRuns(runs).length;
      const end = selection?.end ?? start;
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
      syncEditorHtml,
    ],
  );

  const applyNamedStyleToggle = useCallback(
    (namedStyle: ComunicadoNamedTextStyle) => {
      const editor = editorRef.current;
      if (!editor) return;
      const selection = getEditableTextSelectionOffsets(editor);
      const runs = contentRunsFromEditableRoot(editor);
      const start = selection?.start ?? 0;
      const end = selection?.end ?? plainTextFromContentRuns(runs).length;
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

  const reportSelectionFromEditor = useCallback(() => {
    const editor = editorRef.current;
    if (!editor) return;
    const offsets = getEditableTextSelectionOffsets(editor);
    if (!offsets) {
      reportTextEditSelection(null);
      return;
    }
    const runs = contentRunsFromEditableRoot(editor);
    reportTextEditSelection({ blockId, ...offsets }, runs);
  }, [blockId, editorRef, reportTextEditSelection]);

  return {
    applyPartialStyleToggle,
    applyPartialStylePatch,
    applyListToggle,
    applyNamedStyleToggle,
    insertLineBreak,
    reportSelectionFromEditor,
    readRuns,
  };
}
