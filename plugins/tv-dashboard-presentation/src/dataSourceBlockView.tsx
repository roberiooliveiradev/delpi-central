import { Database } from "lucide-react";
import type { CSSProperties } from "react";

import { sanitizeDataSourceStyle } from "./comunicadoHelpers";
import { formatDataSourceBindingSummary } from "./formatDataSourceBindingSummary";
import type { ComunicadoDataFilters, ComunicadoDataSourceBlock } from "./comunicadoTypes";
import { formatNumber } from "./nativeFormat";
import { resolveDataBlockErrorText } from "./resolveDataBlockErrorText";

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

/**
 * Cor só quando o usuário escolheu um valor explícito (não default legacy / auto).
 * Caso contrário → azul do chrome da fonte (CSS `--tdp-data-accent`).
 */
function resolveDataSourcePaintStyle(
  block: ComunicadoDataSourceBlock,
): CSSProperties | undefined {
  const color = sanitizeDataSourceStyle(block.style).color?.trim();
  if (!color) return undefined;
  return {
    color,
    ["--tdp-data-source-fg" as string]: color,
  };
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
  const summary = formatDataSourceBindingSummary(block, {
    slideFilters,
    labelForKey: labelForParamKey,
    labelForValue: labelForParamValue,
  });
  const paintStyle = resolveDataSourcePaintStyle(block);
  const kpiRaw = block.resolved?.kpi?.value;
  const kpiDisplay =
    kpiRaw != null && kpiRaw !== ""
      ? typeof kpiRaw === "number"
        ? formatNumber(kpiRaw)
        : String(kpiRaw)
      : null;

  const errorText = resolveDataBlockErrorText(block.resolved);
  if (errorText) {
    return (
      <div className="tdp-data-block tdp-data-block--error tdp-data-source" style={paintStyle}>
        <Database size={28} aria-hidden="true" />
        <span>{errorText}</span>
      </div>
    );
  }

  if (editorMode || interactive) {
    return (
      <div
        className={`tdp-data-source tdp-data-source--editor${loading ? " tdp-data-block--loading" : ""}`}
        style={paintStyle}
        title={summary.title}
        aria-label={summary.title}
      >
        <div className="tdp-data-source__header">
          <Database className="tdp-data-source__icon" aria-hidden="true" />
          <span className="tdp-data-source__label">{summary.label}</span>
        </div>
        {kpiDisplay != null ? (
          <span className="tdp-data-source__value">{kpiDisplay}</span>
        ) : summary.operationId && summary.operationId !== summary.label ? (
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
