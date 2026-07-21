import { useCallback, useEffect, useLayoutEffect, useRef, type CSSProperties } from "react";
import {
  appendHrefLineToRuns,
  blockCssStyle,
  comunicadoTextInnerStyle,
  ComunicadoTextRunsView,
  contentRunsFromEditableRoot,
  getEditableTextSelectionOffsets,
  hasRichTextRuns,
  hrefLineStyle,
  insertDataRefAtOffset,
  insertLineBreakAtOffset,
  applyNamedStyleInRange,
  partitionTextBlockRunsAndHref,
  plainTextFromContentRuns,
  renderTextBlockEditorHtml,
  resolveTextBlockDisplayRuns,
  resolveVisualBoxContentLayoutStyle,
  resolveVisualBoxDisplayText,
  restoreEditableTextSelection,
  syncTextBlockFromRuns,
  toggleContentRunStyleInRange,
  toggleListTypeInRange,
  viewHasTextProjectionConfigured,
  visualBoxBlockModifierClasses,
  type ComunicadoBlock,
  type ComunicadoListType,
  type ComunicadoNamedTextStyle,
  type ComunicadoTextDataRef,
  type ContentRunStyleToggleKey,
} from "@delpi/tv-dashboard-presentation";
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
  return appendHrefLineToRuns(resolveTextBlockDisplayRuns(block), block.href);
}

export function externalTextBlockEditorKey(block: TextBlock, fontScale: number) {
  return JSON.stringify({
    content: block.content,
    contentRuns: block.contentRuns,
    href: block.href,
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
    selectBlock,
    registerTextEditorBridge,
    reportTextEditSelection,
  } = useComunicadoEditor();
  const editorRef = useRef<HTMLDivElement>(null);
  const blockRef = useRef(block);
  blockRef.current = block;
  const draftRef = useRef(syncTextBlockFromRuns(resolveTextBlockDisplayRuns(block)));
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
  const contentLayoutStyle = resolveVisualBoxContentLayoutStyle(block, {
    fontScale,
    editorInteractive: true,
  });
  const innerStyle = comunicadoTextInnerStyle(block, { fontScale });
  const linkStyle = hrefLineStyle();

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

  const reportSelectionFromEditor = useCallback(() => {
    const editor = editorRef.current;
    if (!editor) return;
    const offsets = getEditableTextSelectionOffsets(editor);
    if (!offsets) {
      reportTextEditSelection(null);
      return;
    }
    const runs = contentRunsFromEditableRoot(editor);
    reportTextEditSelection({ blockId: block.id, ...offsets }, runs);
  }, [block.id, reportTextEditSelection]);

  const commitDraft = useCallback(
    (runs?: ReturnType<typeof contentRunsFromEditableRoot>) => {
      const fromEditor = runs ?? (editorRef.current ? contentRunsFromEditableRoot(editorRef.current) : null);
      if (fromEditor) {
        const { runs: contentRuns, href } = partitionTextBlockRunsAndHref(fromEditor);
        draftRef.current = syncTextBlockFromRuns(contentRuns);
        const hasDataRuns = contentRuns.some((run) => run.dataRef?.field?.trim());
        if (hasDataRuns) {
          updateBlock(block.id, {
            ...draftRef.current,
            textProjection: undefined,
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

  const applyPartialStyleToggle = useCallback(
    (toggleKey: ContentRunStyleToggleKey) => {
      const editor = editorRef.current;
      if (!editor) return;
      const selection = getEditableTextSelectionOffsets(editor);
      if (!selection || selection.start >= selection.end) return;
      const runs = contentRunsFromEditableRoot(editor);
      const nextRuns = toggleContentRunStyleInRange(runs, selection.start, selection.end, toggleKey);
      draftRef.current = syncTextBlockFromRuns(partitionTextBlockRunsAndHref(nextRuns).runs);
      renderedSignatureRef.current = "";
      syncEditorHtml(nextRuns, { start: selection.start, end: selection.end });
      commitDraft(nextRuns);
      reportTextEditSelection(
        { blockId: block.id, start: selection.start, end: selection.end },
        nextRuns,
      );
    },
    [block.id, commitDraft, reportTextEditSelection, syncEditorHtml],
  );

  const applyListToggle = useCallback(
    (listType: ComunicadoListType) => {
      const editor = editorRef.current;
      if (!editor) return;
      const selection = getEditableTextSelectionOffsets(editor);
      const runs = contentRunsFromEditableRoot(editor);
      const start = selection?.start ?? runs.map((run) => run.text).join("").length;
      const end = selection?.end ?? start;
      const nextRuns = toggleListTypeInRange(runs, start, end, listType);
      draftRef.current = syncTextBlockFromRuns(partitionTextBlockRunsAndHref(nextRuns).runs);
      renderedSignatureRef.current = "";
      syncEditorHtml(nextRuns, { start, end });
      commitDraft(nextRuns);
      reportTextEditSelection({ blockId: block.id, start, end }, nextRuns);
    },
    [block.id, commitDraft, reportTextEditSelection, syncEditorHtml],
  );

  const applyNamedStyleToggle = useCallback(
    (namedStyle: ComunicadoNamedTextStyle) => {
      const editor = editorRef.current;
      if (!editor) return;
      const selection = getEditableTextSelectionOffsets(editor);
      const runs = contentRunsFromEditableRoot(editor);
      const start = selection?.start ?? 0;
      const end = selection?.end ?? runs.map((run) => run.text).join("").length;
      const nextRuns = applyNamedStyleInRange(runs, start, end, namedStyle);
      draftRef.current = syncTextBlockFromRuns(partitionTextBlockRunsAndHref(nextRuns).runs);
      renderedSignatureRef.current = "";
      syncEditorHtml(nextRuns, { start, end });
      commitDraft(nextRuns);
      reportTextEditSelection({ blockId: block.id, start, end }, nextRuns);
    },
    [block.id, commitDraft, reportTextEditSelection, syncEditorHtml],
  );

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

  const insertLineBreak = useCallback(() => {
    const editor = editorRef.current;
    if (!editor) return;
    const selection = getEditableTextSelectionOffsets(editor);
    if (!selection) return;
    const runs = contentRunsFromEditableRoot(editor);
    const nextRuns = insertLineBreakAtOffset(runs, selection.start);
    const nextOffset = selection.start + 1;
    draftRef.current = syncTextBlockFromRuns(partitionTextBlockRunsAndHref(nextRuns).runs);
    renderedSignatureRef.current = "";
    syncEditorHtml(nextRuns, { start: nextOffset, end: nextOffset });
    commitDraft(nextRuns);
    reportTextEditSelection({ blockId: block.id, start: nextOffset, end: nextOffset }, nextRuns);
  }, [block.id, commitDraft, reportTextEditSelection, syncEditorHtml]);

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
    return () => {
      commitPending();
    };
  }, [isEditing, commitPending]);

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
        <div
          className={`td-composer__inline-text-wrap td-composer__inline-text-wrap--${block.type}`}
          style={contentLayoutStyle}
        >
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
        </div>
      </div>
    );
  }

  // Blocos vinculados a um campo (textProjection/dataRef) exibem o valor resolvido da
  // fonte no palco — mesmo caminho da TV (ComunicadoVisualBoxView/DefaultTextContent):
  // substitui `content` pelo valor projetado antes de renderizar.
  const displayBlock: TextBlock = viewHasTextProjectionConfigured(block)
    ? ({ ...block, ...resolveVisualBoxDisplayText(block) } as TextBlock)
    : block;
  const label = displayBlock.content.trim() || PLACEHOLDER[block.type];
  const isPlaceholder = !displayBlock.content.trim();

  return (
    <div
      className={blockClass}
      style={style}
      onDoubleClick={(event) => {
        event.stopPropagation();
        selectBlock(block.id);
        setEditingTextId(block.id);
      }}
    >
      <div className="td-composer__text-block-body" style={contentLayoutStyle}>
        {hasRichTextRuns(displayBlock) ? (
          <ComunicadoTextRunsView
            block={displayBlock}
            as={block.type === "heading" ? "h1" : "p"}
            baseStyle={innerStyle}
            fontScale={fontScale}
            className={isPlaceholder ? "td-composer__text-placeholder" : undefined}
          />
        ) : block.type === "heading" ? (
          <h1
            className={isPlaceholder ? "td-composer__text-placeholder" : undefined}
            style={innerStyle}
          >
            {label}
          </h1>
        ) : (
          <p
            className={isPlaceholder ? "td-composer__text-placeholder" : undefined}
            style={innerStyle}
          >
            {label}
          </p>
        )}
        {block.href ? (
          <a
            className="td-composer__text-href-line"
            href={block.href}
            style={linkStyle}
            onClick={(event) => event.preventDefault()}
            onPointerDown={(event) => event.stopPropagation()}
          >
            {block.href}
          </a>
        ) : null}
      </div>
    </div>
  );
}
