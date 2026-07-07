import type { CSSProperties, ReactNode } from "react";

import { ComunicadoMediaPlaceholder } from "./ComunicadoMediaPlaceholder";
import { blockCssStyle, comunicadoTextInnerStyle, isDataBlockType } from "./comunicadoHelpers";
import type { ComunicadoBlock, ComunicadoDataBlock } from "./comunicadoTypes";
import { TvDataBlockView } from "./tvDataBlockView";

type Props = {
  block: ComunicadoBlock;
  fontScale?: number;
  className?: string;
  interactive?: boolean;
  /** Quando true, o pai controla left/top/width/height. */
  embedded?: boolean;
  dataLoading?: boolean;
};

function wrapWithLink(node: ReactNode, block: ComunicadoBlock) {
  if (block.type !== "heading" && block.type !== "text") return node;
  if (!block.href) return node;
  return (
    <a
      href={block.href}
      target={block.linkTarget ?? "_blank"}
      rel={block.linkTarget === "_blank" ? "noopener noreferrer" : undefined}
      className="tdp-comunicado__link"
    >
      {node}
    </a>
  );
}

function ShapeGraphic({ block }: { block: Extract<ComunicadoBlock, { type: "shape" }> }) {
  const fill = block.style?.fill ?? "#089bdb";
  const stroke = block.style?.stroke ?? "#ffffff";
  const strokeWidth = block.style?.strokeWidth ?? 2;

  if (block.shape === "line") {
    return (
      <div
        className="tdp-comunicado__shape-line"
        style={{ backgroundColor: stroke, height: Math.max(2, strokeWidth) }}
      />
    );
  }

  if (block.shape === "triangle") {
    return (
      <svg viewBox="0 0 100 100" className="tdp-comunicado__shape-svg" aria-hidden="true">
        <polygon points="50,8 92,92 8,92" fill={fill} stroke={stroke} strokeWidth={strokeWidth} />
      </svg>
    );
  }

  if (block.shape === "arrow-right") {
    return (
      <svg viewBox="0 0 100 60" className="tdp-comunicado__shape-svg" aria-hidden="true">
        <path
          d="M4 30 H62 L48 14 L58 4 L96 30 L58 56 L48 46 L62 30 Z"
          fill={fill}
          stroke={stroke}
          strokeWidth={strokeWidth}
        />
      </svg>
    );
  }

  const shapeStyle: CSSProperties = {
    width: "100%",
    height: "100%",
    backgroundColor: fill,
    border: `${strokeWidth}px solid ${stroke}`,
    borderRadius:
      block.shape === "ellipse"
        ? "50%"
        : block.shape === "rounded-rect"
          ? block.style?.borderRadius ?? 16
          : 0,
  };

  return <div className="tdp-comunicado__shape-fill" style={shapeStyle} />;
}

export function ComunicadoBlockView({
  block,
  fontScale = 1,
  className = "",
  interactive = false,
  embedded = false,
  dataLoading = false,
}: Props) {
  const style = embedded
    ? {
        ...blockCssStyle(block, { fontScale }),
        position: "relative" as const,
        left: undefined,
        top: undefined,
        width: "100%",
        height: "100%",
      }
    : blockCssStyle(block, { fontScale });
  const blockClass = `tdp-comunicado__block tdp-comunicado__block--${block.type}${className ? ` ${className}` : ""}`;

  if (block.type === "heading") {
    const innerStyle = comunicadoTextInnerStyle(block, { fontScale });
    const content = <h1 style={innerStyle}>{block.content}</h1>;
    return (
      <div className={`${blockClass} tdp-comunicado__block--heading`} style={style}>
        {wrapWithLink(content, block)}
      </div>
    );
  }

  if (block.type === "text") {
    const innerStyle = comunicadoTextInnerStyle(block, { fontScale });
    const content = <p style={innerStyle}>{block.content}</p>;
    return (
      <div className={`${blockClass} tdp-comunicado__block--text`} style={style}>
        {wrapWithLink(content, block)}
      </div>
    );
  }

  if (block.type === "image" && (block.url || interactive)) {
    return (
      <div className={`${blockClass} tdp-comunicado__block--media`} style={style}>
        {block.url ? (
          <img src={block.url} alt="" style={{ objectFit: block.style?.objectFit ?? "contain" }} />
        ) : (
          <ComunicadoMediaPlaceholder kind="image" />
        )}
      </div>
    );
  }

  if (block.type === "video" && (block.url || interactive)) {
    return (
      <div className={`${blockClass} tdp-comunicado__block--media`} style={style}>
        {block.url ? (
          <video
            src={block.url}
            autoPlay={!interactive}
            muted
            loop
            playsInline
            style={{ objectFit: block.style?.objectFit ?? "contain" }}
          />
        ) : (
          <ComunicadoMediaPlaceholder kind="video" />
        )}
      </div>
    );
  }

  if (block.type === "shape") {
    return (
      <div className={`${blockClass} tdp-comunicado__block--shape`} style={style}>
        <ShapeGraphic block={block} />
        {block.content ? (
          <div className="tdp-comunicado__shape-text">
            <span>{block.content}</span>
          </div>
        ) : null}
      </div>
    );
  }

  if (isDataBlockType(block.type)) {
    return (
      <div className={`${blockClass} tdp-comunicado__block--data`} style={style}>
        <TvDataBlockView
          block={block as ComunicadoDataBlock}
          interactive={interactive}
          loading={dataLoading}
        />
      </div>
    );
  }

  return null;
}
