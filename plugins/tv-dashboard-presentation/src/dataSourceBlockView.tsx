import { Database } from "lucide-react";
import { useLayoutEffect, useRef, useState, type CSSProperties } from "react";

import { resolvePaintTextColor } from "@delpi/plugin-ui/index";

import { formatDataSourceBindingSummary } from "./formatDataSourceBindingSummary";
import type { ComunicadoDataFilters, ComunicadoDataSourceBlock } from "./comunicadoTypes";

type Props = {
  block: ComunicadoDataSourceBlock;
  interactive?: boolean;
  loading?: boolean;
  /** Palco do editor — ícone + rótulo + filtros. */
  editorMode?: boolean;
  /** Filtros globais do slide (mergeidos com params do bloco). */
  slideFilters?: ComunicadoDataFilters | null;
  labelForParamKey?: (key: string) => string;
  labelForParamValue?: (key: string, value: string) => string;
};

function resolveDataSourceContrastBackground(
  block: ComunicadoDataSourceBlock,
  computedBackground?: string,
): string {
  const fromStyle = block.style?.backgroundColor ?? block.style?.fill;
  if (typeof fromStyle === "string" && fromStyle.trim()) return fromStyle;
  if (computedBackground && computedBackground !== "rgba(0, 0, 0, 0)" && computedBackground !== "transparent") {
    return computedBackground;
  }
  return "#ffffff";
}

export function DataSourceBlockView({
  block,
  interactive = false,
  loading = false,
  editorMode = false,
  slideFilters = null,
  labelForParamKey,
  labelForParamValue,
}: Props) {
  const rootRef = useRef<HTMLDivElement>(null);
  const [autoColor, setAutoColor] = useState<string | undefined>();

  const summary = formatDataSourceBindingSummary(block, {
    slideFilters,
    labelForKey: labelForParamKey,
    labelForValue: labelForParamValue,
  });

  useLayoutEffect(() => {
    if (!(editorMode || interactive)) return;
    const node = rootRef.current;
    const computed = node ? getComputedStyle(node).backgroundColor : undefined;
    const bg = resolveDataSourceContrastBackground(block, computed);
    setAutoColor(resolvePaintTextColor(block.style?.color ?? "auto", bg));
  }, [block, editorMode, interactive, block.style?.color, block.style?.backgroundColor, block.style?.fill]);

  const paintStyle: CSSProperties | undefined = autoColor
    ? {
        color: autoColor,
        ["--tdp-data-source-fg" as string]: autoColor,
      }
    : undefined;

  if (block.resolved?.error) {
    return (
      <div className="tdp-data-block tdp-data-block--error tdp-data-source" style={paintStyle}>
        <Database size={28} aria-hidden="true" />
        <span>{String(block.resolved.error)}</span>
      </div>
    );
  }

  if (editorMode || interactive) {
    return (
      <div
        ref={rootRef}
        className={`tdp-data-source tdp-data-source--editor${loading ? " tdp-data-block--loading" : ""}`}
        style={paintStyle}
        title={summary.title}
        aria-label={summary.title}
      >
        <div className="tdp-data-source__header">
          <Database className="tdp-data-source__icon" aria-hidden="true" />
          <span className="tdp-data-source__label">{summary.label}</span>
        </div>
        {summary.operationId && summary.operationId !== summary.label ? (
          <span className="tdp-data-source__meta">{summary.operationId}</span>
        ) : null}
        {summary.filterLines.length > 0 ? (
          <ul className="tdp-data-source__filters">
            {summary.filterLines.map((line) => (
              <li key={line} className="tdp-data-source__filter">
                {line}
              </li>
            ))}
          </ul>
        ) : (
          <span className="tdp-data-source__hint">Sem filtros aplicados</span>
        )}
        {loading ? <span className="tdp-data-source__hint">Carregando…</span> : null}
      </div>
    );
  }

  return null;
}
