import type { CSSProperties, ReactNode } from "react";

import { ComunicadoShapeGraphic } from "./comunicadoShapeGraphic";
import { resolveShapeGeometry } from "./comunicadoShapeGeometry";
import { ComunicadoTextRunsView } from "./ComunicadoTextRunsView";
import { comunicadoTextInnerStyle } from "./comunicadoHelpers";
import type { ComunicadoVisualBoxBlock } from "./comunicadoVisualBox";
import {
  resolveVisualBoxChrome,
  resolveVisualBoxContentLayoutStyle,
  resolveVisualBoxProfile,
} from "./comunicadoVisualBox";

type Props = {
  block: ComunicadoVisualBoxBlock;
  fontScale?: number;
  /** Conteúdo customizado (ex.: editor contentEditable); omitido = render padrão da TV. */
  textContent?: ReactNode;
  textClassName?: string;
  innerStyleOverride?: CSSProperties;
  /** Palco do editor: permite interação com texto dentro da forma. */
  editorInteractive?: boolean;
};

function DefaultTextContent({
  block,
  fontScale = 1,
  className,
  innerStyle,
}: {
  block: ComunicadoVisualBoxBlock;
  fontScale?: number;
  className?: string;
  innerStyle?: CSSProperties;
}) {
  const profile = resolveVisualBoxProfile(block);

  if (block.type === "shape") {
    const label = block.content?.trim();
    if (!label) return null;
    return <span className={className}>{label}</span>;
  }

  const textBlock = block;
  const baseStyle = innerStyle ?? comunicadoTextInnerStyle(textBlock, { fontScale });
  const Tag = profile.textTag;

  return (
    <ComunicadoTextRunsView
      block={textBlock}
      as={Tag}
      baseStyle={baseStyle}
      fontScale={fontScale}
      className={className}
    />
  );
}

/** Caminho único de render: chrome da forma (opcional) + texto interno. */
export function ComunicadoVisualBoxView({
  block,
  fontScale = 1,
  textContent,
  textClassName,
  innerStyleOverride,
  editorInteractive = false,
}: Props) {
  const profile = resolveVisualBoxProfile(block);
  const chrome = resolveVisualBoxChrome(block);
  const contentLayoutStyle = resolveVisualBoxContentLayoutStyle(block, { fontScale, editorInteractive });
  const innerStyle = innerStyleOverride ?? comunicadoTextInnerStyle(
    block.type === "heading" || block.type === "text" ? block : {
      id: block.id,
      type: "text",
      content: block.content ?? "",
      frame: block.frame,
      style: block.style,
    },
    { fontScale },
  );

  const textNode =
    textContent !== undefined ? (
      textContent
    ) : (
      <DefaultTextContent
        block={block}
        fontScale={fontScale}
        className={textClassName}
        innerStyle={innerStyle}
      />
    );

  if (profile.mode === "text") {
    return <div className="tdp-comunicado__visual-box-content">{textNode}</div>;
  }

  return (
    <>
      {chrome.showShapeGraphic && chrome.shapeKind ? (
        <ComunicadoShapeGraphic
          kind={chrome.shapeKind}
          fill={chrome.fill}
          stroke={chrome.stroke}
          strokeWidth={chrome.strokeWidth}
          borderRadius={chrome.borderRadius}
          geometry={block.type === "shape" ? resolveShapeGeometry(block) : undefined}
          markerRadius={block.style?.markerRadius}
        />
      ) : null}
      {textNode ? (
        <div className="tdp-comunicado__shape-text tdp-comunicado__visual-box-content" style={contentLayoutStyle}>
          {textNode}
        </div>
      ) : null}
    </>
  );
}
