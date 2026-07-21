import { useCallback, useEffect, useLayoutEffect, useRef, type CSSProperties } from "react";
import {
  blockCssStyle,
  ComunicadoBlockView,
  patchTextProjectionFromEditedDisplay,
  resolveVisualBoxDisplayText,
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

function shapeDisplayText(block: ComunicadoShapeBlock): string {
  return (
    resolveVisualBoxDisplayText(block, "resolved" in block ? block.resolved : undefined).content ??
    ""
  );
}

export function ComunicadoEditorShapeBlock({
  block,
  fontScale = 1,
  className = "",
  isSelected,
  isEditing,
}: Props) {
  const {
    updateBlockContent,
    updateBlock,
    setEditingTextId,
    selectBlock,
    registerTextEditorBridge,
    requestRibbonTab,
  } = useComunicadoEditor();
  const editorRef = useRef<HTMLDivElement>(null);
  const blockRef = useRef(block);
  blockRef.current = block;
  const draftRef = useRef(shapeDisplayText(block));

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
    const blockNow = blockRef.current;
    const projection = blockNow.textProjection;
    if (projection?.field?.trim()) {
      const nextProjection = patchTextProjectionFromEditedDisplay(
        projection,
        fromEditor,
        "resolved" in blockNow ? blockNow.resolved : undefined,
      );
      updateBlock(blockNow.id, { textProjection: nextProjection });
      return;
    }
    updateBlockContent(blockNow.id, fromEditor);
  }, [updateBlock, updateBlockContent]);

  function exitEditing() {
    commitDraft();
    setEditingTextId(null);
  }

  useLayoutEffect(() => {
    if (!isEditing) return;
    const display = shapeDisplayText(block);
    draftRef.current = display;
    const editor = editorRef.current;
    if (!editor) return;
    editor.textContent = display;
    editor.focus();
    const range = document.createRange();
    range.selectNodeContents(editor);
    range.collapse(false);
    const selection = window.getSelection();
    selection?.removeAllRanges();
    selection?.addRange(range);
  }, [isEditing, block.id, block.content, block.textProjection, block.resolved]);

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
