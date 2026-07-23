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
import { resolveVisualBoxDisplayText, textBlockHasDataBinding } from "./textViewProjection";
import { ensureComunicadoDualClass } from "@delpi/plugin-ui/index";

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
    const display = textBlockHasDataBinding(block)
      ? resolveVisualBoxDisplayText(block, "resolved" in block ? block.resolved : undefined)
      : null;
    const label = display?.content?.trim() ?? block.content?.trim();
    if (!label && !(display?.contentRuns?.length)) return null;
    if (display?.contentRuns?.length) {
      return (
        <ComunicadoTextRunsView
          block={{
            content: display.content,
            contentRuns: display.contentRuns,
            textProjection: block.textProjection,
            resolved: "resolved" in block ? block.resolved : undefined,
            dataSourceId: block.dataSourceId,
          }}
          as="span"
          fontScale={fontScale}
          className={className}
        />
      );
    }
    return <span className={className}>{label}</span>;
  }

  const textBlock = block;
  const displayBlock = textBlockHasDataBinding(textBlock)
    ? {
        ...textBlock,
        ...resolveVisualBoxDisplayText(textBlock, textBlock.resolved),
      }
    : textBlock;
  const baseStyle = innerStyle ?? comunicadoTextInnerStyle(textBlock, { fontScale });
  const Tag = profile.textTag;

  return (
    <ComunicadoTextRunsView
      block={displayBlock}
      as={Tag}
      baseStyle={baseStyle}
      fontScale={fontScale}
      className={className}
    />
  );
}

/** Caminho único: chrome geométrico + texto interno (texto = forma sem fundo por padrão). */
export function ComunicadoVisualBoxView({
  block,
  fontScale = 1,
  textContent,
  textClassName,
  innerStyleOverride,
  editorInteractive = false,
}: Props) {
  const chrome = resolveVisualBoxChrome(block);
  const contentLayoutStyle = resolveVisualBoxContentLayoutStyle(block, {
    fontScale,
    editorInteractive,
  });
  const innerStyle =
    innerStyleOverride ??
    comunicadoTextInnerStyle(
      block.type === "heading" || block.type === "text"
        ? block
        : {
            id: block.id,
            type: "text",
            content: block.content ?? "",
            frame: block.frame,
            style: block.style,
            shape: block.shape,
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

  return (
    <>
      {chrome.showShapeGraphic && chrome.shapeKind ? (
        <ComunicadoShapeGraphic
          kind={chrome.shapeKind}
          fill={chrome.fill}
          stroke={chrome.stroke}
          strokeWidth={chrome.strokeWidth}
          borderRadius={chrome.borderRadius}
          style={block.style}
          geometry={block.type === "shape" ? resolveShapeGeometry(block) : undefined}
          markerRadius={block.style?.markerRadius}
          lineRouting={
            block.type === "shape" ? block.connector?.routing ?? "straight" : undefined
          }
        />
      ) : null}
      {textNode ? (
        <div
          className={ensureComunicadoDualClass("tdp-comunicado__shape-text tdp-comunicado__visual-box-content")}
          style={contentLayoutStyle}
        >
          {textNode}
        </div>
      ) : null}
    </>
  );
}
