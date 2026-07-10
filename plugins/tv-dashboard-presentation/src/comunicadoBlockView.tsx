import type { CSSProperties, ReactNode } from "react";

import { ComunicadoVisualBoxView } from "./ComunicadoVisualBoxView";
import { ComunicadoIconGraphic } from "./comunicadoIconView";
import {
  blockEntranceAnimationClass,
  blockEntranceAnimationStyle,
} from "./comunicadoBlockAnimations";
import { comunicadoImageCropCssProperties } from "./comunicadoImageCrop";
import { ComunicadoMediaPlaceholder } from "./ComunicadoMediaPlaceholder";
import { blockCssStyle, isDataBlockType, isDataSourceBlockType } from "./comunicadoHelpers";
import {
  isComunicadoVisualBoxBlock,
  visualBoxBlockModifierClasses,
} from "./comunicadoVisualBox";
import type { ComunicadoBlock, ComunicadoDataBlock } from "./comunicadoTypes";
import { ChartViewBlockView } from "./chartViewBlockView";
import { DataSourceBlockView } from "./dataSourceBlockView";
import { TableViewBlockView } from "./tableViewBlockView";
import { TvDataBlockView } from "./tvDataBlockView";

type Props = {
  block: ComunicadoBlock;
  fontScale?: number;
  className?: string;
  interactive?: boolean;
  /** Quando true, o pai controla left/top/width/height. */
  embedded?: boolean;
  dataLoading?: boolean;
  /** Conteúdo de texto customizado (editor); só caixas visuais. */
  visualBoxTextContent?: ReactNode;
  visualBoxTextClassName?: string;
  visualBoxInnerStyle?: CSSProperties;
  /** Palco do editor: texto interativo dentro de formas. */
  visualBoxEditorInteractive?: boolean;
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

export function ComunicadoBlockView({
  block,
  fontScale = 1,
  className = "",
  interactive = false,
  embedded = false,
  dataLoading = false,
  visualBoxTextContent,
  visualBoxTextClassName,
  visualBoxInnerStyle,
  visualBoxEditorInteractive = false,
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

  if (isComunicadoVisualBoxBlock(block)) {
    const modifiers = visualBoxBlockModifierClasses(block);
    const content = (
      <ComunicadoVisualBoxView
        block={block}
        fontScale={fontScale}
        textContent={visualBoxTextContent}
        textClassName={visualBoxTextClassName}
        innerStyleOverride={visualBoxInnerStyle}
        editorInteractive={visualBoxEditorInteractive}
      />
    );
    return (
      <div className={blockClass([...modifiers, "tdp-comunicado__visual-box"].join(" "))} style={style}>
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

  if (isDataSourceBlockType(block.type)) {
    if (!interactive) return null;
    return (
      <div className={blockClass("tdp-comunicado__block--data-source")} style={style}>
        <DataSourceBlockView
          block={block}
          interactive={interactive}
          loading={dataLoading}
          editorMode={interactive}
        />
      </div>
    );
  }

  if (block.type === "chart_view") {
    return (
      <div className={blockClass("tdp-comunicado__block--chart-view")} style={style}>
        <ChartViewBlockView block={block} interactive={interactive} loading={dataLoading} />
      </div>
    );
  }

  if (block.type === "table_view") {
    return (
      <div className={blockClass("tdp-comunicado__block--table-view")} style={style}>
        <TableViewBlockView block={block} interactive={interactive} loading={dataLoading} />
      </div>
    );
  }

  return null;
}
