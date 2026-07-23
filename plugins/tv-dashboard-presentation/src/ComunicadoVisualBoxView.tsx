import type { CSSProperties, ReactNode } from "react";

import { ComunicadoShapeGraphic } from "./comunicadoShapeGraphic";
import { resolveShapeGeometry } from "./comunicadoShapeGeometry";
import { ComunicadoTextSurface } from "./ComunicadoTextSurface";
import { comunicadoTextInnerStyle } from "./comunicadoHelpers";
import type { ComunicadoVisualBoxBlock } from "./comunicadoVisualBox";
import {
  resolveVisualBoxChrome,
  resolveVisualBoxContentLayoutStyle,
} from "./comunicadoVisualBox";
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

/**
 * Conteúdo textual padrão — sempre via `ComunicadoTextSurface`
 * (resolve + TextRunsView; nunca string crua com contentRuns).
 */
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
  return (
    <ComunicadoTextSurface
      block={block}
      fontScale={fontScale}
      className={className}
      baseStyle={
        block.type === "heading" || block.type === "text" ? innerStyle : undefined
      }
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
