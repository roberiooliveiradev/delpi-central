import { useEffect, useRef, type CSSProperties } from "react";
import {
  blockCssStyle,
  comunicadoTextInnerStyle,
  ComunicadoTextRunsView,
  hasRichTextRuns,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";
import { TdNativeTextAreaControl } from "./tdFormFields";
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
  const { updateBlockContent, setEditingTextId, selectBlock } = useComunicadoEditor();
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
          <TdNativeTextAreaControl
            ref={inputRef}
            className="td-composer__inline-text"
            style={innerStyle}
            value={block.content}
            placeholder={PLACEHOLDER[block.type]}
            rows={1}
            aria-label={PLACEHOLDER[block.type]}
            onChange={(value) => updateBlockContent(block.id, value)}
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
