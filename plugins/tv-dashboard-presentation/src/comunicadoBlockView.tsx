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
import { KpiViewBlockView } from "./kpiViewBlockView";
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

/**
 * Sombra no slot externo: o bloco tem overflow:hidden (conteúdo),
 * então box-shadow no mesmo nó era cortado. No editor o wrap faz esse papel.
 */
function mountBlockRoot(
  className: string,
  style: CSSProperties,
  children: ReactNode,
  embedded: boolean,
) {
  const shadow = typeof style.boxShadow === "string" ? style.boxShadow.trim() : "";
  if (embedded || !shadow) {
    const nextStyle = embedded ? { ...style, boxShadow: undefined } : style;
    return (
      <div className={className} style={nextStyle}>
        {children}
      </div>
    );
  }

  const {
    left,
    top,
    right,
    bottom,
    width,
    height,
    position,
    zIndex,
    transform,
    boxShadow,
    opacity,
    ...inner
  } = style;

  return (
    <div
      className="tdp-comunicado__block-slot"
      style={{
        left,
        top,
        right,
        bottom,
        width,
        height,
        position: position ?? "absolute",
        zIndex,
        transform,
        boxShadow,
        opacity,
      }}
    >
      <div
        className={className}
        style={{
          ...inner,
          position: "relative",
          left: undefined,
          top: undefined,
          width: "100%",
          height: "100%",
          boxShadow: undefined,
        }}
      >
        {children}
      </div>
    </div>
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
        boxShadow: undefined,
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
    return mountBlockRoot(
      blockClass([...modifiers, "tdp-comunicado__visual-box"].join(" ")),
      style,
      wrapWithLink(content, block),
      embedded,
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
    return mountBlockRoot(
      blockClass("tdp-comunicado__block--media"),
      style,
      wrapWithLink(media, block),
      embedded,
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
    return mountBlockRoot(
      blockClass("tdp-comunicado__block--media"),
      style,
      wrapWithLink(media, block),
      embedded,
    );
  }

  if (block.type === "icon") {
    const iconNode = <ComunicadoIconGraphic block={block} />;
    return mountBlockRoot(
      blockClass("tdp-comunicado__block--icon"),
      style,
      wrapWithLink(iconNode, block),
      embedded,
    );
  }

  if (isDataBlockType(block.type)) {
    return mountBlockRoot(
      blockClass("tdp-comunicado__block--data"),
      style,
      <TvDataBlockView
        block={block as ComunicadoDataBlock}
        interactive={interactive}
        loading={dataLoading}
      />,
      embedded,
    );
  }

  if (isDataSourceBlockType(block.type)) {
    if (!interactive) return null;
    return mountBlockRoot(
      blockClass("tdp-comunicado__block--data-source"),
      style,
      <DataSourceBlockView
        block={block as import("./comunicadoTypes").ComunicadoDataSourceBlock}
        interactive={interactive}
        loading={dataLoading}
        editorMode={interactive}
      />,
      embedded,
    );
  }

  if (block.type === "chart_view") {
    return mountBlockRoot(
      blockClass("tdp-comunicado__block--chart-view"),
      style,
      <ChartViewBlockView block={block} interactive={interactive} loading={dataLoading} />,
      embedded,
    );
  }

  if (block.type === "table_view") {
    return mountBlockRoot(
      blockClass("tdp-comunicado__block--table-view"),
      style,
      <TableViewBlockView block={block} interactive={interactive} loading={dataLoading} />,
      embedded,
    );
  }

  if (block.type === "kpi_view") {
    return mountBlockRoot(
      blockClass("tdp-comunicado__block--kpi-view"),
      style,
      <KpiViewBlockView block={block} interactive={interactive} loading={dataLoading} />,
      embedded,
    );
  }

  return null;
}
