import { useCallback, useEffect, useLayoutEffect, useRef, type CSSProperties } from "react";
import {
  appendHrefLineToRuns,
  blockCssStyle,
  comunicadoTextInnerStyle,
  ComunicadoBlockView,
  contentRunsFromEditableRoot,
  getEditableTextSelectionOffsets,
  insertDataRefAtOffset,
  partitionTextBlockRunsAndHref,
  patchTextProjectionFromEditedDisplay,
  plainTextFromContentRuns,
  renderTextBlockEditorHtml,
  resolveTextBlockDisplayRuns,
  restoreEditableTextSelection,
  syncTextBlockFromRuns,
  visualBoxBlockModifierClasses,
  type ComunicadoBlock,
  type ComunicadoTextDataRef,
} from "@delpi/tv-dashboard-presentation";
import { useVisualBoxTextEditorBridge } from "../hooks/useVisualBoxTextEditorBridge";
import { useComunicadoEditor } from "./comunicadoEditorContext";

type TextBlock = Extract<ComunicadoBlock, { type: "heading" } | { type: "text" }>;

type Props = {
  block: TextBlock;
  fontScale?: number;
  className?: string;
  isSelected: boolean;
  isEditing: boolean;
};

const PLACEHOLDER: Record<TextBlock["type"], string> = {
  heading: "Título",
  text: "Texto",
};

function editorRunsForBlock(block: TextBlock) {
  return appendHrefLineToRuns(
    resolveTextBlockDisplayRuns(block, block.resolved),
    block.href,
  );
}

export function externalTextBlockEditorKey(block: TextBlock, fontScale: number) {
  return JSON.stringify({
    content: block.content,
    contentRuns: block.contentRuns,
    href: block.href,
    textProjection: block.textProjection,
    resolvedFingerprint: block.resolved
      ? JSON.stringify(block.resolved.kpi ?? block.resolved.kpiMetrics ?? null)
      : null,
    fontScale,
  });
}

export function ComunicadoEditorTextBlock({
  block,
  fontScale = 1,
  className = "",
  isSelected,
  isEditing,
}: Props) {
  const {
    updateBlockTextFields,
    updateBlock,
    updateBlockLink,
    setEditingTextId,
    enterTextEdit,
    cancelPendingTapDeselect,
    registerTextEditorBridge,
    reportTextEditSelection,
  } = useComunicadoEditor();
  const editorRef = useRef<HTMLDivElement>(null);
  const blockRef = useRef(block);
  blockRef.current = block;
  const draftRef = useRef(
    syncTextBlockFromRuns(resolveTextBlockDisplayRuns(block, block.resolved)),
  );
  const renderedSignatureRef = useRef("");
  const editingInitBlockIdRef = useRef<string | null>(null);
  const lastSyncedExternalKeyRef = useRef("");

  const style: CSSProperties = {
    ...blockCssStyle(block, { fontScale }),
    position: "relative",
    left: undefined,
    top: undefined,
    width: "100%",
    height: "100%",
    // Rotação fica no wrap de seleção (handles/outline alinhados ao bloco).
    transform: undefined,
  };
  const innerStyle = comunicadoTextInnerStyle(block, { fontScale });

  const blockClass = [
    "tdp-comunicado__block",
    "tdp-comunicado__visual-box",
    ...visualBoxBlockModifierClasses(block),
    "td-composer__text-block",
    "td-composer__text-block--readonly",
    isEditing ? "td-composer__text-block--editing" : "",
    isSelected && !isEditing ? "td-composer__text-block--selected" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const syncEditorHtml = useCallback(
    (
      runs = editorRunsForBlock(blockRef.current),
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
      const fromEditor = runs ?? (editorRef.current ? contentRunsFromEditableRoot(editorRef.current) : null);
      if (fromEditor) {
        const { runs: contentRuns, href } = partitionTextBlockRunsAndHref(fromEditor);
        draftRef.current = syncTextBlockFromRuns(contentRuns);
        const hasDataRuns = contentRuns.some((run) => run.dataRef?.field?.trim());
        const blockNow = blockRef.current;
        const projection = blockNow.textProjection;
        if (hasDataRuns) {
          updateBlock(block.id, {
            ...draftRef.current,
            textProjection: undefined,
          } as Partial<ComunicadoBlock>);
        } else if (projection?.field?.trim()) {
          // Prefixo/sufixo vivem em textProjection — não assar o valor dinâmico em content.
          const editedPlain = plainTextFromContentRuns(contentRuns);
          const nextProjection = patchTextProjectionFromEditedDisplay(
            projection,
            editedPlain,
            blockNow.resolved,
          );
          updateBlock(block.id, {
            textProjection: nextProjection,
          } as Partial<ComunicadoBlock>);
        } else {
          updateBlockTextFields(block.id, draftRef.current);
        }
        updateBlockLink(block.id, href);
        return;
      }
      updateBlockTextFields(block.id, draftRef.current);
    },
    [block.id, updateBlock, updateBlockLink, updateBlockTextFields],
  );

  const commitPending = useCallback(() => {
    commitDraft();
  }, [commitDraft]);
  const commitPendingRef = useRef(commitPending);
  commitPendingRef.current = commitPending;

  const normalizeEditorRuns = useCallback(
    (runs: import("@delpi/tv-dashboard-presentation").ComunicadoContentRun[]) =>
      partitionTextBlockRunsAndHref(runs).runs,
    [],
  );

  const {
    applyPartialStyleToggle,
    applyPartialStylePatch,
    applyListToggle,
    applyNamedStyleToggle,
    insertLineBreak,
    reportSelectionFromEditor,
  } = useVisualBoxTextEditorBridge({
    blockId: block.id,
    editorRef,
    draftRef,
    renderedSignatureRef,
    syncEditorHtml,
    commitDraft,
    reportTextEditSelection,
    normalizeEditorRuns,
  });

  const insertDataRefAtSelection = useCallback(
    (dataRef: ComunicadoTextDataRef) => {
      const editor = editorRef.current;
      if (!editor) return;
      const runs = contentRunsFromEditableRoot(editor);
      const selection = getEditableTextSelectionOffsets(editor);
      const offset = selection?.start ?? plainTextFromContentRuns(runs).length;
      const nextRuns = insertDataRefAtOffset(runs, offset, dataRef);
      const nextOffset = offset + 1;
      draftRef.current = syncTextBlockFromRuns(partitionTextBlockRunsAndHref(nextRuns).runs);
      renderedSignatureRef.current = "";
      syncEditorHtml(appendHrefLineToRuns(nextRuns, blockRef.current.href), {
        start: nextOffset,
        end: nextOffset,
      });
      updateBlock(block.id, {
        ...draftRef.current,
        textProjection: undefined,
      } as Partial<ComunicadoBlock>);
      reportTextEditSelection({ blockId: block.id, start: nextOffset, end: nextOffset }, nextRuns);
    },
    [block.id, reportTextEditSelection, syncEditorHtml, updateBlock],
  );

  function exitEditing() {
    commitPending();
    reportTextEditSelection(null);
    setEditingTextId(null);
  }

  useEffect(() => {
    if (!isEditing) {
      editingInitBlockIdRef.current = null;
      return;
    }
    if (editingInitBlockIdRef.current === block.id) return;
    editingInitBlockIdRef.current = block.id;

    const blockNow = blockRef.current;
    lastSyncedExternalKeyRef.current = externalTextBlockEditorKey(blockNow, fontScale);

    const editorRuns = editorRunsForBlock(blockNow);
    draftRef.current = syncTextBlockFromRuns(partitionTextBlockRunsAndHref(editorRuns).runs);
    renderedSignatureRef.current = "";
    const editor = editorRef.current;
    if (!editor) return;
    syncEditorHtml(editorRuns, null);
    editor.focus();
    const end = editorRuns.map((run) => run.text).join("").length;
    restoreEditableTextSelection(editor, end, end);
    reportTextEditSelection({ blockId: block.id, start: end, end }, editorRuns);
  }, [isEditing, block.id, fontScale, syncEditorHtml, reportTextEditSelection]);

  useEffect(() => {
    if (!isEditing) return;
    /*
     * Cleanup só ao sair da edição — NÃO depender de commitPending.
     * Senão cada nova identidade do callback dispara cleanup → commit →
     * update do bloco → novo callback → React #185 (maximum update depth).
     */
    return () => {
      commitPendingRef.current();
    };
  }, [isEditing]);

  useLayoutEffect(() => {
    if (!isEditing) {
      lastSyncedExternalKeyRef.current = "";
      return;
    }
    const externalKey = externalTextBlockEditorKey(block, fontScale);
    if (lastSyncedExternalKeyRef.current === externalKey) return;
    lastSyncedExternalKeyRef.current = externalKey;

    const editor = editorRef.current;
    const editorRuns = editorRunsForBlock(block);
    const selection = editor ? getEditableTextSelectionOffsets(editor) : null;
    syncEditorHtml(editorRuns, selection);
    draftRef.current = syncTextBlockFromRuns(partitionTextBlockRunsAndHref(editorRuns).runs);
  }, [block.contentRuns, block.content, block.href, isEditing, fontScale, syncEditorHtml]);

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
      insertDataRefAtSelection,
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
    insertDataRefAtSelection,
  ]);

  if (isEditing) {
    const showPlaceholder = !editorRunsForBlock(block).some((run) => run.text.trim());
    return (
      <div className={blockClass} style={style} onPointerDown={(event) => event.stopPropagation()}>
        <ComunicadoBlockView
          block={block}
          fontScale={fontScale}
          embedded
          interactive
          visualBoxEditorInteractive
          visualBoxInnerStyle={innerStyle}
          visualBoxTextContent={
            <div
              ref={editorRef}
              className={[
                "td-composer__inline-text",
                "td-composer__inline-text--rich",
                block.type === "heading" ? "td-composer__inline-text--heading" : "td-composer__inline-text--body",
                showPlaceholder ? "td-composer__text-placeholder" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              style={innerStyle}
              contentEditable
              suppressContentEditableWarning
              role="textbox"
              aria-multiline="true"
              aria-label={PLACEHOLDER[block.type]}
              data-placeholder={PLACEHOLDER[block.type]}
              onInput={() => {
                const editor = editorRef.current;
                if (!editor) return;
                const runs = contentRunsFromEditableRoot(editor);
                draftRef.current = syncTextBlockFromRuns(partitionTextBlockRunsAndHref(runs).runs);
                renderedSignatureRef.current = JSON.stringify(runs);
                reportSelectionFromEditor();
              }}
              onBlur={exitEditing}
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
                  if (block.type === "heading" && !event.shiftKey) {
                    exitEditing();
                    return;
                  }
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

  // Mesmo caminho da TV: chrome geométrico (fill/contorno/raio) + tipografia.
  // Default transparente só na inserção (`defaultStyle`) — não há remoção no render.
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
