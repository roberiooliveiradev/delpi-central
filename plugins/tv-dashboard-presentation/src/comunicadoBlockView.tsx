import type { CSSProperties, ReactNode } from "react";

import { ComunicadoShapeGraphic } from "./comunicadoShapeGraphic";
import { ComunicadoIconGraphic } from "./comunicadoIconView";
import { ComunicadoTextRunsView } from "./ComunicadoTextRunsView";
import {
  blockEntranceAnimationClass,
  blockEntranceAnimationStyle,
} from "./comunicadoBlockAnimations";
import { comunicadoImageCropCssProperties } from "./comunicadoImageCrop";
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

function blockLinkHref(block: ComunicadoBlock): string | undefined {
  if (
    block.type === "heading" ||
    block.type === "text" ||
    block.type === "image" ||
    block.type === "video" ||
    block.type === "shape" ||
    block.type === "icon"
  ) {
    return block.href;
  }
  return undefined;
}

function blockLinkTarget(block: ComunicadoBlock): "_blank" | "_self" | undefined {
  if (
    block.type === "heading" ||
    block.type === "text" ||
    block.type === "image" ||
    block.type === "video" ||
    block.type === "shape" ||
    block.type === "icon"
  ) {
    return block.linkTarget;
  }
  return undefined;
}

function wrapWithLink(node: ReactNode, block: ComunicadoBlock) {
  const href = blockLinkHref(block);
  if (!href) return node;
  const target = blockLinkTarget(block) ?? "_blank";
  return (
    <a
      href={href}
      target={target}
      rel={target === "_blank" ? "noopener noreferrer" : undefined}
      className="tdp-comunicado__link"
    >
      {node}
    </a>
  );
}

function ShapeGraphic({ block }: { block: Extract<ComunicadoBlock, { type: "shape" }> }) {
  return (
    <ComunicadoShapeGraphic
      kind={block.shape}
      fill={block.style?.fill ?? "#089bdb"}
      stroke={block.style?.stroke ?? "#ffffff"}
      strokeWidth={block.style?.strokeWidth ?? 2}
      borderRadius={block.style?.borderRadius}
    />
  );
}

export function ComunicadoBlockView({
  block,
  fontScale = 1,
  className = "",
  interactive = false,
  embedded = false,
  dataLoading = false,
}: Props) {
  const baseStyle = embedded
    ? {
        ...blockCssStyle(block, { fontScale }),
        position: "relative" as const,
        left: undefined,
        top: undefined,
        width: "100%",
        height: "100%",
      }
    : blockCssStyle(block, { fontScale });
  const animClass = blockEntranceAnimationClass(block.animations);
  const style: CSSProperties = { ...baseStyle, ...blockEntranceAnimationStyle(block.animations) };
  const blockClass = (extra = "") =>
    [
      `tdp-comunicado__block tdp-comunicado__block--${block.type}`,
      animClass,
      className,
      extra,
    ]
      .filter(Boolean)
      .join(" ");

  if (block.type === "heading") {
    const innerStyle = comunicadoTextInnerStyle(block, { fontScale });
    const content = (
      <ComunicadoTextRunsView block={block} as="h1" baseStyle={innerStyle} fontScale={fontScale} />
    );
    return (
      <div className={blockClass("tdp-comunicado__block--heading")} style={style}>
        {wrapWithLink(content, block)}
      </div>
    );
  }

  if (block.type === "text") {
    const innerStyle = comunicadoTextInnerStyle(block, { fontScale });
    const content = (
      <ComunicadoTextRunsView block={block} as="p" baseStyle={innerStyle} fontScale={fontScale} />
    );
    return (
      <div className={blockClass("tdp-comunicado__block--text")} style={style}>
        {wrapWithLink(content, block)}
      </div>
    );
  }

  if (block.type === "image" && (block.url || interactive)) {
    const fit = block.style?.objectFit ?? "contain";
    const media = block.url ? (
      <img
        src={block.url}
        alt=""
        style={comunicadoImageCropCssProperties(block.imageCrop, fit)}
      />
    ) : (
      <ComunicadoMediaPlaceholder kind="image" />
    );
    return (
      <div className={blockClass("tdp-comunicado__block--media")} style={style}>
        {wrapWithLink(media, block)}
      </div>
    );
  }

  if (block.type === "video" && (block.url || interactive)) {
    const media = block.url ? (
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
    );
    return (
      <div className={blockClass("tdp-comunicado__block--media")} style={style}>
        {wrapWithLink(media, block)}
      </div>
    );
  }

  if (block.type === "shape") {
    const shapeContent = (
      <>
        <ShapeGraphic block={block} />
        {block.content ? (
          <div className="tdp-comunicado__shape-text">
            <span>{block.content}</span>
          </div>
        ) : null}
      </>
    );
    return (
      <div className={blockClass("tdp-comunicado__block--shape")} style={style}>
        {wrapWithLink(shapeContent, block)}
      </div>
    );
  }

  if (block.type === "icon") {
    const iconNode = <ComunicadoIconGraphic block={block} />;
    return (
      <div className={blockClass("tdp-comunicado__block--icon")} style={style}>
        {wrapWithLink(iconNode, block)}
      </div>
    );
  }

  if (isDataBlockType(block.type)) {
    return (
      <div className={blockClass("tdp-comunicado__block--data")} style={style}>
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
