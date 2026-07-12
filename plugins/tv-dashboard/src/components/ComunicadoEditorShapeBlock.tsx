import { useCallback, useEffect, useLayoutEffect, useRef, type CSSProperties } from "react";
import {
  blockCssStyle,
  ComunicadoBlockView,
  visualBoxBlockModifierClasses,
  type ComunicadoShapeBlock,
} from "@delpi/tv-dashboard-presentation";

import { useComunicadoEditor } from "./comunicadoEditorContext";

type Props = {
  block: ComunicadoShapeBlock;
  fontScale?: number;
  className?: string;
  isSelected: boolean;
  isEditing: boolean;
};

const PLACEHOLDER = "Texto na forma";

export function ComunicadoEditorShapeBlock({
  block,
  fontScale = 1,
  className = "",
  isSelected,
  isEditing,
}: Props) {
  const {
    updateBlockContent,
    setEditingTextId,
    selectBlock,
    registerTextEditorBridge,
    requestRibbonTab,
  } = useComunicadoEditor();
  const editorRef = useRef<HTMLDivElement>(null);
  const draftRef = useRef(block.content ?? "");

  const style: CSSProperties = {
    ...blockCssStyle(block, { fontScale }),
    position: "relative",
    left: undefined,
    top: undefined,
    width: "100%",
    height: "100%",
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

  const commitDraft = useCallback(() => {
    const fromEditor = editorRef.current?.textContent ?? draftRef.current;
    draftRef.current = fromEditor;
    updateBlockContent(block.id, fromEditor);
  }, [block.id, updateBlockContent]);

  function exitEditing() {
    commitDraft();
    setEditingTextId(null);
  }

  useLayoutEffect(() => {
    if (!isEditing) return;
    draftRef.current = block.content ?? "";
    const editor = editorRef.current;
    if (!editor) return;
    editor.textContent = block.content ?? "";
    editor.focus();
    const range = document.createRange();
    range.selectNodeContents(editor);
    range.collapse(false);
    const selection = window.getSelection();
    selection?.removeAllRanges();
    selection?.addRange(range);
  }, [isEditing, block.id]);

  useEffect(() => {
    if (!isEditing) return;
    return () => {
      commitDraft();
    };
  }, [isEditing, commitDraft]);

  useEffect(() => {
    if (!isEditing) {
      registerTextEditorBridge(block.id, null);
      return;
    }

    registerTextEditorBridge(block.id, {
      applyPartialStyleToggle: () => {},
      applyListToggle: () => {},
      applyNamedStyleToggle: () => {},
      refreshSelectionState: () => {},
      commitPending: commitDraft,
    });

    return () => registerTextEditorBridge(block.id, null);
  }, [isEditing, block.id, commitDraft, registerTextEditorBridge]);

  if (isEditing) {
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
              className="td-composer__inline-text td-composer__inline-text--shape"
              contentEditable
              suppressContentEditableWarning
              role="textbox"
              aria-multiline="true"
              aria-label={PLACEHOLDER}
              data-placeholder={PLACEHOLDER}
              onInput={() => {
                draftRef.current = editorRef.current?.textContent ?? "";
              }}
              onBlur={exitEditing}
              onKeyDown={(event) => {
                event.stopPropagation();
                if (event.key === "Escape") {
                  event.preventDefault();
                  exitEditing();
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
        selectBlock(block.id);
        setEditingTextId(block.id);
        requestRibbonTab("shape");
      }}
    >
      <ComunicadoBlockView block={block} fontScale={fontScale} embedded interactive />
    </div>
  );
}
