import type { CSSProperties, ReactNode } from "react";

import { ComunicadoVisualBoxView } from "./ComunicadoVisualBoxView";
import { ComunicadoCanvasTableView } from "./ComunicadoCanvasTableView";
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
import type { ComunicadoBlock, ComunicadoDataBlock, ComunicadoDataFilters } from "./comunicadoTypes";
import { ChartViewBlockView } from "./chartViewBlockView";
import { DataSourceBlockView } from "./dataSourceBlockView";
import { KpiViewBlockView } from "./kpiViewBlockView";
import { TableViewBlockView } from "./tableViewBlockView";
import { ComunicadoInputBlockView } from "./ComunicadoInputBlockView";
import type { ComunicadoInputInteraction } from "./comunicadoInputParts";
import { TvDataBlockView } from "./tvDataBlockView";

type Props = {
  block: ComunicadoBlock;
  fontScale?: number;
  className?: string;
  interactive?: boolean;
  /** Kiosk/editor: permite editar blocos `input` (filtros da sessão). */
  inputsInteractive?: boolean;
  /** Valor runtime do input (kiosk); se omitido usa defaultValue. */
  inputRuntimeValue?: string | number | boolean | null;
  onInputValueChange?: (blockId: string, value: string | number | boolean | null) => void;
  /** Subseleção de partes do filtro (editor). */
  inputInteraction?: ComunicadoInputInteraction | null;
  /** Quando true, o pai controla left/top/width/height. */
  embedded?: boolean;
  dataLoading?: boolean;
  /** Filtros do slide — exibidos no cartão da fonte de dados. */
  slideDataFilters?: ComunicadoDataFilters | null;
  labelForDataParamKey?: (key: string) => string;
  labelForDataParamValue?: (key: string, value: string) => string;
  /** Conteúdo de texto customizado (editor); só caixas visuais. */
  visualBoxTextContent?: ReactNode;
  visualBoxTextClassName?: string;
  visualBoxInnerStyle?: CSSProperties;
  /** Palco do editor: texto interativo dentro de formas. */
  visualBoxEditorInteractive?: boolean;
  onCanvasTableCellChange?: (row: number, col: number, value: string) => void;
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

function mountBlockRoot(className: string, style: CSSProperties, children: ReactNode) {
  return (
    <div className={className} style={style}>
      {children}
    </div>
  );
}

export function ComunicadoBlockView({
  block,
  fontScale = 1,
  className = "",
  interactive = false,
  inputsInteractive = false,
  inputRuntimeValue,
  onInputValueChange,
  inputInteraction = null,
  embedded = false,
  dataLoading = false,
  slideDataFilters = null,
  labelForDataParamKey,
  labelForDataParamValue,
  visualBoxTextContent,
  visualBoxTextClassName,
  visualBoxInnerStyle,
  visualBoxEditorInteractive = false,
  onCanvasTableCellChange,
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
    return mountBlockRoot(
      blockClass([...modifiers, "tdp-comunicado__visual-box"].join(" ")),
      style,
      wrapWithLink(content, block),
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
    );
  }

  if (block.type === "icon") {
    const iconNode = <ComunicadoIconGraphic block={block} fontScale={fontScale} />;
    return mountBlockRoot(
      blockClass("tdp-comunicado__block--icon"),
      style,
      wrapWithLink(iconNode, block),
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
        slideFilters={slideDataFilters}
        labelForParamKey={labelForDataParamKey}
        labelForParamValue={labelForDataParamValue}
      />,
    );
  }

  if (block.type === "chart_view") {
    return mountBlockRoot(
      blockClass("tdp-comunicado__block--chart-view"),
      style,
      <ChartViewBlockView block={block} interactive={interactive} loading={dataLoading} />,
    );
  }

  if (block.type === "table_view") {
    return mountBlockRoot(
      blockClass("tdp-comunicado__block--table-view"),
      style,
      <TableViewBlockView block={block} interactive={interactive} loading={dataLoading} />,
    );
  }

  if (block.type === "canvas_table") {
    return mountBlockRoot(
      blockClass("tdp-comunicado__block--canvas-table"),
      style,
      <ComunicadoCanvasTableView
        block={block}
        editable={interactive}
        onCellChange={onCanvasTableCellChange}
      />,
    );
  }

  if (block.type === "kpi_view") {
    return mountBlockRoot(
      blockClass("tdp-comunicado__block--kpi-view"),
      style,
      <KpiViewBlockView block={block} interactive={interactive} loading={dataLoading} />,
    );
  }

  if (block.type === "input") {
    const resolvedField =
      block.input &&
      typeof block.input === "object" &&
      "resolvedField" in block.input &&
      block.input.resolvedField &&
      typeof block.input.resolvedField === "object"
        ? (block.input.resolvedField as {
            type?: string;
            label?: string;
            description?: string;
            enum?: Array<string | number | boolean>;
            format?: string;
          })
        : null;
    const paramAvailable =
      !("paramAvailable" in (block.input ?? {})) || Boolean((block.input as { paramAvailable?: boolean }).paramAvailable);
    const canEdit = interactive || inputsInteractive;
    return mountBlockRoot(
      blockClass("tdp-comunicado__block--input"),
      style,
      <ComunicadoInputBlockView
        block={block}
        field={resolvedField}
        value={inputRuntimeValue}
        interactive={canEdit}
        paramAvailable={paramAvailable && Boolean(block.input?.paramKey)}
        linkedSourceCount={
          block.input?.targetScope === "sources"
            ? (block.input.targetSourceIds?.length ?? 0)
            : undefined
        }
        dataLoading={dataLoading}
        interaction={inputInteraction}
        onChange={
          onInputValueChange
            ? (value) => onInputValueChange(block.id, value)
            : undefined
        }
      />,
    );
  }

  return null;
}
