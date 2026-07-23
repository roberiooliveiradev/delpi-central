import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  type CSSProperties,
  type FocusEvent,
  type MouseEvent,
} from "react";
import {
  blockCssStyle,
  ComunicadoBlockView,
  contentRunsFromEditableRoot,
  getEditableTextSelectionOffsets,
  patchTextProjectionFromEditedDisplay,
  plainTextFromContentRuns,
  renderTextBlockEditorHtml,
  resolveVisualBoxDisplayText,
  restoreEditableTextSelection,
  syncTextBlockFromRuns,
  visualBoxBlockModifierClasses,
  type ComunicadoShapeBlock,
} from "@delpi/tv-dashboard-presentation";

import { useVisualBoxTextEditorBridge } from "../hooks/useVisualBoxTextEditorBridge";
import { shouldPreserveTextEditOnBlur } from "../utils/preserveTextEditFocus";
import { useComunicadoEditor } from "./comunicadoEditorContext";

type Props = {
  block: ComunicadoShapeBlock;
  fontScale?: number;
  className?: string;
  isSelected: boolean;
  isEditing: boolean;
};

const PLACEHOLDER = "Texto na forma";

function shapeEditorRuns(block: ComunicadoShapeBlock) {
  const display = resolveVisualBoxDisplayText(
    block,
    "resolved" in block ? block.resolved : undefined,
  );
  if (display.contentRuns?.length) return display.contentRuns;
  return [{ text: display.content ?? "" }];
}

export function ComunicadoEditorShapeBlock({
  block,
  fontScale = 1,
  className = "",
  isSelected,
  isEditing,
}: Props) {
  const {
    updateBlock,
    setEditingTextId,
    enterTextEdit,
    cancelPendingTapDeselect,
    registerTextEditorBridge,
    reportTextEditSelection,
    lastPartialTextEditSelection,
    openTextFormatContextMenu,
  } = useComunicadoEditor();
  const editorRef = useRef<HTMLDivElement>(null);
  const blockRef = useRef(block);
  blockRef.current = block;
  const draftRef = useRef(syncTextBlockFromRuns(shapeEditorRuns(block)));
  const renderedSignatureRef = useRef("");
  const editingInitBlockIdRef = useRef<string | null>(null);

  const style: CSSProperties = {
    ...blockCssStyle(block, { fontScale }),
    position: "relative",
    left: undefined,
    top: undefined,
    width: "100%",
    height: "100%",
    transform: undefined,
  };

  const blockClass = [
    "tdp-comunicado__block",
    "tdp-comunicado__visual-box",
    ...visualBoxBlockModifierClasses(block),
    "td-composer__shape-block",
    isEditing ? "td-composer__text-block--editing" : "td-composer__text-block--readonly",
    isSelected && !isEditing ? "td-composer__text-block--selected" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const syncEditorHtml = useCallback(
    (
      runs = shapeEditorRuns(blockRef.current),
      selectionOverride?: { start: number; end: number } | null,
    ) => {
      const editor = editorRef.current;
      if (!editor) return;
      const selection =
        selectionOverride === undefined
          ? getEditableTextSelectionOffsets(editor)
          : selectionOverride;
      const signature = JSON.stringify(runs);
      if (signature === renderedSignatureRef.current) return;
      editor.innerHTML = renderTextBlockEditorHtml(runs, { fontScale });
      renderedSignatureRef.current = signature;
      if (selection) restoreEditableTextSelection(editor, selection.start, selection.end);
    },
    [fontScale],
  );

  const commitDraft = useCallback(
    (runs?: ReturnType<typeof contentRunsFromEditableRoot>) => {
      const fromEditor =
        runs ?? (editorRef.current ? contentRunsFromEditableRoot(editorRef.current) : null);
      if (!fromEditor) return;
      const synced = syncTextBlockFromRuns(fromEditor);
      draftRef.current = synced;
      const blockNow = blockRef.current;
      const projection = blockNow.textProjection;
      const hasDataRuns = fromEditor.some((run) => run.dataRef?.field?.trim());
      if (hasDataRuns) {
        updateBlock(blockNow.id, {
          content: synced.content,
          contentRuns: synced.contentRuns,
          textProjection: undefined,
        });
        return;
      }
      if (projection?.field?.trim()) {
        const nextProjection = patchTextProjectionFromEditedDisplay(
          projection,
          synced.content,
          "resolved" in blockNow ? blockNow.resolved : undefined,
        );
        updateBlock(blockNow.id, { textProjection: nextProjection });
        return;
      }
      updateBlock(blockNow.id, {
        content: synced.content,
        contentRuns: synced.contentRuns,
      });
    },
    [updateBlock],
  );
  const commitPending = useCallback(() => {
    commitDraft();
  }, [commitDraft]);
  const commitPendingRef = useRef(commitPending);
  commitPendingRef.current = commitPending;

  const {
    applyPartialStyleToggle,
    applyPartialStylePatch,
    applyListToggle,
    applyNamedStyleToggle,
    insertLineBreak,
    reportSelectionFromEditor,
    clearPartialRangeFallback,
  } = useVisualBoxTextEditorBridge({
    blockId: block.id,
    editorRef,
    draftRef,
    renderedSignatureRef,
    syncEditorHtml,
    commitDraft,
    reportTextEditSelection,
  });

  function exitEditing() {
    commitPending();
    clearPartialRangeFallback();
    reportTextEditSelection(null);
    setEditingTextId(null);
  }

  function handleEditorBlur(event: FocusEvent<HTMLDivElement>) {
    if (shouldPreserveTextEditOnBlur(event.relatedTarget)) return;
    exitEditing();
  }

  function handleEditorContextMenu(event: MouseEvent<HTMLDivElement>) {
    event.preventDefault();
    event.stopPropagation();
    reportSelectionFromEditor();
    const editor = editorRef.current;
    const live = editor ? getEditableTextSelectionOffsets(editor) : null;
    const fallback =
      lastPartialTextEditSelection?.blockId === block.id ? lastPartialTextEditSelection : null;
    const hasPartial =
      (live != null && live.end > live.start) ||
      (fallback != null && fallback.end > fallback.start);
    if (!hasPartial) return;
    openTextFormatContextMenu({ x: event.clientX, y: event.clientY });
  }

  useLayoutEffect(() => {
    if (!isEditing) {
      editingInitBlockIdRef.current = null;
      return;
    }
    if (editingInitBlockIdRef.current === block.id) return;
    editingInitBlockIdRef.current = block.id;

    const editorRuns = shapeEditorRuns(block);
    draftRef.current = syncTextBlockFromRuns(editorRuns);
    renderedSignatureRef.current = "";
    const editor = editorRef.current;
    if (!editor) return;
    syncEditorHtml(editorRuns, null);
    editor.focus();
    const end = plainTextFromContentRuns(editorRuns).length;
    restoreEditableTextSelection(editor, end, end);
    reportTextEditSelection({ blockId: block.id, start: end, end }, editorRuns);
  }, [isEditing, block.id, syncEditorHtml, reportTextEditSelection]);

  useEffect(() => {
    if (!isEditing) return;
    return () => {
      commitPendingRef.current();
    };
  }, [isEditing]);

  useLayoutEffect(() => {
    if (!isEditing) return;
    const editor = editorRef.current;
    const editorRuns = shapeEditorRuns(block);
    const selection = editor ? getEditableTextSelectionOffsets(editor) : null;
    syncEditorHtml(editorRuns, selection);
    draftRef.current = syncTextBlockFromRuns(editorRuns);
  }, [block.contentRuns, block.content, isEditing, fontScale, syncEditorHtml]);

  useEffect(() => {
    if (!isEditing) {
      registerTextEditorBridge(block.id, null);
      return;
    }

    registerTextEditorBridge(block.id, {
      applyPartialStyleToggle,
      applyPartialStylePatch,
      applyListToggle,
      applyNamedStyleToggle,
      refreshSelectionState: reportSelectionFromEditor,
      commitPending,
    });

    return () => registerTextEditorBridge(block.id, null);
  }, [
    isEditing,
    block.id,
    applyPartialStyleToggle,
    applyPartialStylePatch,
    applyListToggle,
    applyNamedStyleToggle,
    reportSelectionFromEditor,
    registerTextEditorBridge,
    commitPending,
  ]);

  if (isEditing) {
    const showPlaceholder = !shapeEditorRuns(block).some((run) => run.text.trim());
    return (
      <div className={blockClass} style={style} onPointerDown={(event) => event.stopPropagation()}>
        <ComunicadoBlockView
          block={block}
          fontScale={fontScale}
          embedded
          interactive
          visualBoxEditorInteractive
          visualBoxTextContent={
            <div
              ref={editorRef}
              className={[
                "td-composer__inline-text",
                "td-composer__inline-text--rich",
                "td-composer__inline-text--shape",
                showPlaceholder ? "td-composer__text-placeholder" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              contentEditable
              suppressContentEditableWarning
              role="textbox"
              aria-multiline="true"
              aria-label={PLACEHOLDER}
              data-placeholder={PLACEHOLDER}
              onInput={() => {
                const editor = editorRef.current;
                if (!editor) return;
                const runs = contentRunsFromEditableRoot(editor);
                draftRef.current = syncTextBlockFromRuns(runs);
                renderedSignatureRef.current = JSON.stringify(runs);
                reportSelectionFromEditor();
              }}
              onBlur={handleEditorBlur}
              onContextMenu={handleEditorContextMenu}
              onKeyUp={reportSelectionFromEditor}
              onMouseUp={reportSelectionFromEditor}
              onKeyDown={(event) => {
                event.stopPropagation();
                if (event.key === "Escape") {
                  event.preventDefault();
                  exitEditing();
                  return;
                }
                if (event.key === "Enter") {
                  event.preventDefault();
                  insertLineBreak();
                  return;
                }
                if (!(event.ctrlKey || event.metaKey)) return;
                const key = event.key.toLowerCase();
                if (key === "b") {
                  event.preventDefault();
                  applyPartialStyleToggle("fontWeight");
                } else if (key === "i") {
                  event.preventDefault();
                  applyPartialStyleToggle("fontStyle");
                } else if (key === "u") {
                  event.preventDefault();
                  applyPartialStyleToggle("underline");
                }
              }}
            />
          }
        />
      </div>
    );
  }

  return (
    <div
      className={blockClass}
      style={style}
      onDoubleClick={(event) => {
        event.stopPropagation();
        cancelPendingTapDeselect();
        enterTextEdit(block.id);
      }}
    >
      <ComunicadoBlockView block={block} fontScale={fontScale} embedded interactive />
    </div>
  );
}
