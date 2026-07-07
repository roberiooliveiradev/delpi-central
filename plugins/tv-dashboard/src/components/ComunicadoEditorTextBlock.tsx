import { useEffect, useRef, type CSSProperties } from "react";
import { Link2 } from "lucide-react";
import { blockCssStyle, comunicadoTextInnerStyle, type ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

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
  const { updateBlockContent, updateBlockLink, setEditingTextId, selectBlock } = useComunicadoEditor();
  const inputRef = useRef<HTMLTextAreaElement>(null);

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
      <div className={blockClass} style={style} onPointerDown={(event) => event.stopPropagation()}>
        <div className={`td-composer__inline-text-wrap td-composer__inline-text-wrap--${block.type}`}>
          <textarea
            ref={inputRef}
            className="td-composer__inline-text"
            style={innerStyle}
            value={block.content}
            placeholder={PLACEHOLDER[block.type]}
            rows={1}
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
        {block.type === "heading" ? (
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
        <div
          className="td-composer__text-inline-chrome"
          onPointerDown={(event) => event.stopPropagation()}
        >
          <span className="td-composer__text-inline-hint">Duplo-clique para editar</span>
          <label className="td-composer__text-link-field">
            <Link2 size={12} aria-hidden="true" />
            <input
              type="url"
              placeholder="Link (URL)"
              value={block.href ?? ""}
              onChange={(event) => updateBlockLink(block.id, event.target.value)}
            />
          </label>
        </div>
      ) : null}
    </div>
  );
}
