import { blockCssStyle, type ComunicadoBlock } from "@delpi/tv-dashboard-presentation";
import { useEffect, useRef, type CSSProperties } from "react";

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
  const { updateBlockContent, setEditingTextId, setSelectedId } = useComunicadoEditor();
  const inputRef = useRef<HTMLTextAreaElement>(null);

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
    `tdp-comunicado__block--${block.type}`,
    "td-composer__text-block",
    isEditing
      ? "td-composer__text-block--editing"
      : "td-composer__text-block--readonly",
    isSelected && !isEditing ? "td-composer__text-block--selected" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  useEffect(() => {
    if (!isEditing) return;
    const node = inputRef.current;
    if (!node) return;
    node.focus();
    const end = node.value.length;
    node.setSelectionRange(end, end);
  }, [isEditing, block.id]);

  function exitEditing() {
    setEditingTextId(null);
  }

  if (isEditing) {
    return (
      <div
        className={blockClass}
        style={style}
        onPointerDown={(event) => event.stopPropagation()}
      >
        <textarea
          ref={inputRef}
          className="td-composer__inline-text"
          value={block.content}
          placeholder={PLACEHOLDER[block.type]}
          rows={block.type === "heading" ? 2 : 4}
          aria-label={PLACEHOLDER[block.type]}
          onChange={(event) => updateBlockContent(block.id, event.target.value)}
          onBlur={exitEditing}
          onKeyDown={(event) => {
            event.stopPropagation();
            if (event.key === "Escape") {
              event.preventDefault();
              exitEditing();
            }
          }}
        />
      </div>
    );
  }

  const label = block.content.trim() || PLACEHOLDER[block.type];
  const isPlaceholder = !block.content.trim();

  return (
    <div
      className={blockClass}
      style={style}
      onDoubleClick={(event) => {
        event.stopPropagation();
        setSelectedId(block.id);
        setEditingTextId(block.id);
      }}
    >
      {block.type === "heading" ? (
        <h1 className={isPlaceholder ? "td-composer__text-placeholder" : undefined}>{label}</h1>
      ) : (
        <p className={isPlaceholder ? "td-composer__text-placeholder" : undefined}>{label}</p>
      )}
    </div>
  );
}
