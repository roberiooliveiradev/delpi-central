import {
  applyContentRunStyleInRange,
  contentRunsFromEditableRoot,
  getEditableTextSelectionOffsets,
  renderTextBlockEditorHtml,
  restoreEditableTextSelection,
  syncTextBlockFromRuns,
  toggleContentRunStyleInRange,
  type ComunicadoContentRun,
  type ContentRunStylePatch,
  type ContentRunStyleToggleKey,
} from "@delpi/tv-dashboard-presentation";
import type { DeckContentRun } from "@delpi/plugin-ui/index";
import type { TextEditorBridge } from "../components/comunicadoEditorContextCore";

export function toDeckContentRuns(runs: ComunicadoContentRun[]): DeckContentRun[] {
  return runs.map((run) => ({
    text: run.text,
    style: run.style
      ? {
          fontSize: run.style.fontSize,
          color: run.style.color,
          fontFamily: run.style.fontFamily,
          textHighlight: run.style.textHighlight,
          fontWeight: run.style.fontWeight,
          fontStyle: run.style.fontStyle,
          textDecoration: run.style.textDecoration,
          lineHeight: run.style.lineHeight,
        }
      : undefined,
  }));
}

export function fromDeckContentRuns(runs: DeckContentRun[] | undefined): ComunicadoContentRun[] {
  if (!runs?.length) return [];
  return runs.map((run) => {
    if (!run.style) return { text: run.text };
    const style: NonNullable<ComunicadoContentRun["style"]> = {};
    if (typeof run.style.fontSize === "number") style.fontSize = run.style.fontSize;
    if (run.style.color) style.color = run.style.color;
    if (run.style.fontFamily) style.fontFamily = run.style.fontFamily;
    if (run.style.textHighlight) style.textHighlight = run.style.textHighlight;
    if (run.style.fontWeight === "bold" || run.style.fontWeight === "normal") {
      style.fontWeight = run.style.fontWeight;
    }
    if (run.style.fontStyle === "italic" || run.style.fontStyle === "normal") {
      style.fontStyle = run.style.fontStyle;
    }
    if (
      run.style.textDecoration === "none" ||
      run.style.textDecoration === "underline" ||
      run.style.textDecoration === "line-through" ||
      run.style.textDecoration === "underline line-through"
    ) {
      style.textDecoration = run.style.textDecoration;
    }
    if (typeof run.style.lineHeight === "number") style.lineHeight = run.style.lineHeight;
    return { text: run.text, style: Object.keys(style).length ? style : undefined };
  });
}

export function renderPartEditorHtml(
  content: string,
  contentRuns?: DeckContentRun[],
): string {
  const runs = contentRuns?.length
    ? fromDeckContentRuns(contentRuns)
    : [{ text: content || "\u00a0" }];
  return renderTextBlockEditorHtml(runs);
}

export function parsePartEditorRuns(root: HTMLElement): DeckContentRun[] {
  return toDeckContentRuns(contentRunsFromEditableRoot(root));
}

/** Bridge de tipografia parcial para contentEditable de part KPI/chart. */
export function createPartTextEditorBridge(params: {
  blockId: string;
  editor: HTMLElement;
  reportTextEditSelection: (
    selection: { blockId: string; start: number; end: number } | null,
    runs?: ComunicadoContentRun[],
  ) => void;
  onRunsCommit: (runs: ComunicadoContentRun[]) => void;
}): TextEditorBridge {
  const { blockId, editor, reportTextEditSelection, onRunsCommit } = params;
  let lastPartial: { start: number; end: number } | null = null;

  const resolvePartial = () => {
    const live = getEditableTextSelectionOffsets(editor);
    if (live && live.end > live.start) {
      lastPartial = live;
      return live;
    }
    return lastPartial && lastPartial.end > lastPartial.start ? lastPartial : null;
  };

  const applyToggle = (toggleKey: ContentRunStyleToggleKey): boolean => {
    const selection = resolvePartial();
    if (!selection) return false;
    const runs = contentRunsFromEditableRoot(editor);
    const nextRuns = toggleContentRunStyleInRange(
      runs,
      selection.start,
      selection.end,
      toggleKey,
    );
    editor.innerHTML = renderTextBlockEditorHtml(nextRuns);
    restoreEditableTextSelection(editor, selection.start, selection.end);
    onRunsCommit(nextRuns);
    reportTextEditSelection(
      { blockId, start: selection.start, end: selection.end },
      nextRuns,
    );
    return true;
  };

  const applyPatch = (patch: ContentRunStylePatch): boolean => {
    const selection = resolvePartial();
    if (!selection) return false;
    const runs = contentRunsFromEditableRoot(editor);
    const nextRuns = applyContentRunStyleInRange(
      runs,
      selection.start,
      selection.end,
      patch,
    );
    editor.innerHTML = renderTextBlockEditorHtml(nextRuns);
    restoreEditableTextSelection(editor, selection.start, selection.end);
    onRunsCommit(nextRuns);
    reportTextEditSelection(
      { blockId, start: selection.start, end: selection.end },
      nextRuns,
    );
    return true;
  };

  return {
    applyPartialStyleToggle: applyToggle,
    applyPartialStylePatch: applyPatch,
    applyListToggle: () => undefined,
    applyNamedStyleToggle: () => undefined,
    refreshSelectionState: () => {
      const offsets = getEditableTextSelectionOffsets(editor);
      if (!offsets) return;
      if (offsets.end > offsets.start) lastPartial = offsets;
      reportTextEditSelection(
        { blockId, ...offsets },
        contentRunsFromEditableRoot(editor),
      );
    },
    commitPending: () => {
      const runs = contentRunsFromEditableRoot(editor);
      onRunsCommit(runs);
    },
  };
}

export function syncPartFieldsFromRuns(runs: ComunicadoContentRun[]) {
  return syncTextBlockFromRuns(runs);
}
