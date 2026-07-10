import { useCallback, useEffect, useLayoutEffect, useRef, type CSSProperties } from "react";
import {
  blockCssStyle,
  comunicadoTextInnerStyle,
  ComunicadoTextRunsView,
  contentRunsFromEditableRoot,
  getEditableTextSelectionOffsets,
  hasRichTextRuns,
  renderContentRunsHtml,
  resolveTextBlockDisplayRuns,
  restoreEditableTextSelection,
  syncTextBlockFromRuns,
  toggleContentRunStyleInRange,
  type ComunicadoBlock,
  type ContentRunStyleToggleKey,
} from "@delpi/tv-dashboard-presentation";
import { ComunicadoEditorLinkChrome } from "./ComunicadoEditorLinkChrome";
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

export function ComunicadoEditorTextBlock({
  block,
  fontScale = 1,
  className = "",
  isSelected,
  isEditing,
}: Props) {
  const {
    updateBlockTextFields,
    setEditingTextId,
    selectBlock,
    registerTextEditorBridge,
    reportTextEditSelection,
  } = useComunicadoEditor();
  const editorRef = useRef<HTMLDivElement>(null);
  const draftRef = useRef(syncTextBlockFromRuns(resolveTextBlockDisplayRuns(block)));
  const renderedSignatureRef = useRef("");

  const style: CSSProperties = {
    ...blockCssStyle(block, { fontScale }),
    position: "relative",
    left: undefined,
    top: undefined,
    width: "100%",
    height: "100%",
  };
  const innerStyle = comunicadoTextInnerStyle(block, { fontScale });

  const blockClass = [
    "tdp-comunicado__block",
    `tdp-comunicado__block--${block.type}`,
    "td-composer__text-block",
    "td-composer__text-block--readonly",
    isEditing ? "td-composer__text-block--editing" : "",
    isSelected && !isEditing ? "td-composer__text-block--selected" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const syncEditorHtml = useCallback((runs = resolveTextBlockDisplayRuns(block), restoreSelection = false) => {
    const editor = editorRef.current;
    if (!editor) return;
    const selection = restoreSelection ? getEditableTextSelectionOffsets(editor) : null;
    const signature = JSON.stringify(runs);
    if (signature === renderedSignatureRef.current) return;
    editor.innerHTML = renderContentRunsHtml(runs, { fontScale });
    renderedSignatureRef.current = signature;
    if (selection) restoreEditableTextSelection(editor, selection.start, selection.end);
  }, [block, fontScale]);

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

  const commitDraft = useCallback(() => {
    updateBlockTextFields(block.id, draftRef.current);
  }, [block.id, updateBlockTextFields]);

  const applyPartialStyleToggle = useCallback((toggleKey: ContentRunStyleToggleKey) => {
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
    draftRef.current = syncTextBlockFromRuns(nextRuns);
    renderedSignatureRef.current = "";
    syncEditorHtml(nextRuns, true);
    commitDraft();
    reportTextEditSelection(
      { blockId: block.id, start: selection.start, end: selection.end },
      nextRuns,
    );
  }, [block.id, commitDraft, reportTextEditSelection, syncEditorHtml]);

  function exitEditing() {
    const editor = editorRef.current;
    if (editor) {
      draftRef.current = syncTextBlockFromRuns(contentRunsFromEditableRoot(editor));
      commitDraft();
    }
    reportTextEditSelection(null);
    setEditingTextId(null);
  }

  useEffect(() => {
    if (!isEditing) return;
    draftRef.current = syncTextBlockFromRuns(resolveTextBlockDisplayRuns(block));
    renderedSignatureRef.current = "";
    const editor = editorRef.current;
    if (!editor) return;
    syncEditorHtml(resolveTextBlockDisplayRuns(block));
    editor.focus();
    const end = draftRef.current.content.length;
    restoreEditableTextSelection(editor, end, end);
    reportTextEditSelection(
      { blockId: block.id, start: end, end },
      resolveTextBlockDisplayRuns(block),
    );
  }, [isEditing, block.id, syncEditorHtml, reportTextEditSelection, block]);

  useLayoutEffect(() => {
    if (!isEditing) return;
    syncEditorHtml(resolveTextBlockDisplayRuns(block), true);
    draftRef.current = syncTextBlockFromRuns(resolveTextBlockDisplayRuns(block));
  }, [block.contentRuns, block.content, isEditing, fontScale, syncEditorHtml, block]);

  useEffect(() => {
    if (!isEditing) {
      registerTextEditorBridge(block.id, null);
      return;
    }

    registerTextEditorBridge(block.id, {
      applyPartialStyleToggle,
      refreshSelectionState: reportSelectionFromEditor,
    });

    return () => registerTextEditorBridge(block.id, null);
  }, [
    isEditing,
    block.id,
    applyPartialStyleToggle,
    reportSelectionFromEditor,
    registerTextEditorBridge,
  ]);

  if (isEditing) {
    const showPlaceholder = !draftRef.current.content.trim();
    return (
      <div className={blockClass} style={style} onPointerDown={(event) => event.stopPropagation()}>
        <div className={`td-composer__inline-text-wrap td-composer__inline-text-wrap--${block.type}`}>
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
              draftRef.current = syncTextBlockFromRuns(runs);
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

  const label = block.content.trim() || PLACEHOLDER[block.type];
  const isPlaceholder = !block.content.trim();
  const showInlineChrome = isSelected;

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
      <div className="td-composer__text-block-body">
        {hasRichTextRuns(block) ? (
          <ComunicadoTextRunsView
            block={block}
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
      </div>
      {showInlineChrome ? (
        <ComunicadoEditorLinkChrome
          blockId={block.id}
          href={block.href}
          hint="Duplo-clique para editar"
        />
      ) : null}
    </div>
  );
}
