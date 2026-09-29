import { CheckCircle2, PencilLine } from "lucide-react";

import type {
  ComunicadoDataResolved,
  ParamExpressionSpec,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  expressionCanonicalText,
  summarizeExpressionSpec,
} from "../utils/paramExpressionLabels";
import { readExpressionAst } from "../utils/paramExpressions";

type TraceEntry = {
  resolved?: unknown;
  error?: { message?: unknown; code?: unknown } | null;
  expectedType?: unknown;
};

function formatTraceValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "object") {
    try {
      return JSON.stringify(value);
    } catch {
      return "—";
    }
  }
  return String(value);
}

/** Entrada do trace backend (`resolved.paramExpressions`) para o param. */
export function findParamExpressionTrace(
  resolved: ComunicadoDataResolved | null | undefined,
  paramKey: string,
): TraceEntry | null {
  const raw = (resolved as { paramExpressions?: unknown } | null | undefined)
    ?.paramExpressions;
  if (!Array.isArray(raw)) return null;
  const entry = raw.find(
    (item) => item && typeof item === "object" && (item as { param?: unknown }).param === paramKey,
  );
  return (entry as TraceEntry | undefined) ?? null;
}

type Props = {
  spec: ParamExpressionSpec;
  paramKey: string;
  /** `resolved` enriquecido do backend para o trace/resultado. */
  resolved?: ComunicadoDataResolved | null;
  /** Abre o drawer de edição — ausente = cartão somente leitura. */
  onEdit?: () => void;
  /** Datas resolvidas para exibir período efetivo (effectiveParams). */
  resolvedParamValue?: unknown;
};

/**
 * Cartão-resumo de expressão ativa — apresentação only (§19/§98):
 * frase amigável + AST canônico + resultado backend + «Editar expressão».
 * Nunca avalia; erros técnicos ficam em <details>.
 */
export function ExpressionSummaryCard({
  spec,
  paramKey,
  resolved = null,
  onEdit,
  resolvedParamValue,
}: Props) {
  const ast = readExpressionAst(spec);
  const summary = summarizeExpressionSpec(spec);
  const canonical = ast ? expressionCanonicalText(ast) : null;
  const trace = findParamExpressionTrace(resolved, paramKey);
  const traceError = trace?.error
    ? String(trace.error.message ?? trace.error.code ?? "erro")
    : null;
  const resolvedValue =
    trace?.resolved !== undefined ? trace.resolved : resolvedParamValue;

  return (
    <div className="td-expression-summary" data-param-key={paramKey}>
      <p className="td-expression-summary__title">{summary}</p>
      {canonical ? (
        <code className="td-expression-summary__canonical">{canonical}</code>
      ) : null}
      {traceError ? (
        <div className="td-expression-summary__error" role="alert">
          <p>Não foi possível validar a expressão.</p>
          <details className="td-expression-summary__details">
            <summary>Detalhes técnicos</summary>
            <pre className="td-param-expression__json">{traceError}</pre>
          </details>
        </div>
      ) : resolvedValue !== undefined && resolvedValue !== null ? (
        <p className="td-expression-summary__result">
          <CheckCircle2 size={14} aria-hidden="true" />
          Resultado: {formatTraceValue(resolvedValue)}
        </p>
      ) : null}
      {onEdit ? (
        <button
          type="button"
          className="td-btn td-btn--sm td-btn--ghost td-expression-summary__edit"
          onClick={onEdit}
          title={TV_DASHBOARD_HELP_TOOLTIPS.data.paramExpression}
        >
          <PencilLine size={14} aria-hidden="true" />
          Editar expressão
        </button>
      ) : null}
    </div>
  );
}
