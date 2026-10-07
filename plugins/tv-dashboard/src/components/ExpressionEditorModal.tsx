/**
 * Workbench (modal host-contained) de edição de expressão tipada — entry point único de authoring
 * estrutural do AST. O draft é local: «Cancelar»/Escape não tocam no
 * parâmetro persistido; «Aplicar» usa o `apply` do host (mesma regra de
 * conflito preset/expressão de `buildParamValueUpdates`).
 *
 * Preview usa `previewTvDataRoute` — o backend resolve e valida; este
 * componente nunca avalia a expressão (§19/§33).
 */
import { useMemo, useState } from "react";
import { Play } from "lucide-react";
import type { DataRoutePreviewPayload } from "@delpi/plugin-ui/index";
import type { ParamExpressionSpec } from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { ParamExpressionSupport } from "../hooks/useParamExpressionCapability";
import {
  availableExpressionTemplates,
  expressionCanonicalText,
  summarizeExpressionSpec,
} from "../utils/paramExpressionLabels";
import {
  buildExpressionParamValue,
  expressionAstIncomplete,
  readExpressionAst,
} from "../utils/paramExpressions";
import type { ExpressionEditRequest } from "./comunicadoEditorContextCore";
import { TypedExpressionEditor } from "./TypedExpressionEditor";
import { HostContainedModal } from "./ui/Modal";

export type ExpressionEditorModalProps = {
  open: boolean;
  request: ExpressionEditRequest;
  support: ParamExpressionSupport;
  /**
   * Preview backend com o draft aplicado — retorna o payload tipado
   * (`paramExpressions`/`effectiveParams` do enrichment). Sem callback
   * (bloco sem preview) o botão não aparece.
   */
  onPreview?: (
    spec: ParamExpressionSpec,
  ) => Promise<DataRoutePreviewPayload | null>;
  onClose: () => void;
};

export function ExpressionEditorModal({
  open,
  request,
  support,
  onPreview,
  onClose,
}: ExpressionEditorModalProps) {
  const [draft, setDraft] = useState<ParamExpressionSpec>(() => request.spec);
  const [previewing, setPreviewing] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [previewResult, setPreviewResult] = useState<{
    resolved?: unknown;
    error?: string | null;
    expectedType?: unknown;
  } | null>(null);

  const draftAst = readExpressionAst(draft);
  const summary = summarizeExpressionSpec(draft);
  const canonical = draftAst ? expressionCanonicalText(draftAst) : "";
  const incomplete = expressionAstIncomplete(draftAst);

  const templates = useMemo(
    () =>
      availableExpressionTemplates({
        expectedReturnTypes: request.expectedReturnTypes,
        functionNames: new Set(support.functions.map((item) => item.name)),
      }),
    [request.expectedReturnTypes, support.functions],
  );

  async function runPreview() {
    if (!onPreview) return;
    setPreviewing(true);
    setPreviewError(null);
    setPreviewResult(null);
    try {
      const payload = await onPreview(draft);
      const trace = payload?.paramExpressions?.find(
        (entry) => entry && entry.param === request.paramKey,
      ) as
        | { resolved?: unknown; error?: { message?: unknown; code?: unknown } | null; expectedType?: unknown }
        | undefined;
      setPreviewResult({
        resolved: trace?.resolved ?? payload?.effectiveParams?.[request.paramKey],
        error:
          payload?.error ??
          (trace?.error
            ? String(trace.error.message ?? trace.error.code ?? "erro")
            : null),
        expectedType: trace?.expectedType,
      });
    } catch (error) {
      setPreviewError(
        error instanceof Error ? error.message : "Falha ao pré-visualizar.",
      );
    } finally {
      setPreviewing(false);
    }
  }

  function apply() {
    request.apply(draft);
    onClose();
  }

  return (
    <HostContainedModal
      open={open}
      onClose={onClose}
      title={`Expressão — ${request.paramLabel}`}
      description={TV_DASHBOARD_HELP_TOOLTIPS.data.paramExpression}
      closeAriaLabel="Fechar editor de expressão"
      footer={
        <div className="td-expression-editor__actions">
          {onPreview ? (
            <button
              type="button"
              className="td-btn td-btn--sm td-btn--ghost"
              disabled={previewing}
              onClick={() => void runPreview()}
            >
              <Play size={14} aria-hidden="true" />
              {previewing ? "Pré-visualizando…" : "Pré-visualizar"}
            </button>
          ) : null}
          <span className="td-expression-editor__spacer" />
          <button
            type="button"
            className="td-btn td-btn--sm td-btn--ghost"
            onClick={onClose}
          >
            Cancelar
          </button>
          <button
            type="button"
            className="td-btn td-btn--sm"
            onClick={apply}
            title="Aplica a expressão no parâmetro"
          >
            Aplicar expressão
          </button>
        </div>
      }
    >
      <div className="td-expression-editor">
        <div className="td-expression-editor__summary">
          <p className="td-expression-summary__title">{summary}</p>
          {canonical ? (
            <code className="td-expression-summary__canonical">{canonical}</code>
          ) : null}
        </div>

        {templates.length > 0 ? (
          <div
            className="td-expression-editor__templates"
            role="group"
            aria-label="Sugestões de expressão"
          >
            {templates.map((template) => (
              <button
                key={template.id}
                type="button"
                className="delpi-ui-data-route-catalog__chip"
                onClick={() =>
                  setDraft(buildExpressionParamValue(template.build()))
                }
              >
                {template.label}
              </button>
            ))}
          </div>
        ) : null}

        {support.enabled ? (
          <TypedExpressionEditor
            value={draft}
            onChange={setDraft}
            support={support}
            refParamKeys={request.refParamKeys ?? []}
            refInputKeys={request.refInputKeys ?? []}
            expectedReturnTypes={request.expectedReturnTypes}
            idPrefix="td-expr-editor"
          />
        ) : (
          <p className="td-param-expression__hint" role="status">
            Catálogo de funções indisponível — o AST permanece editável em
            detalhes técnicos abaixo.
          </p>
        )}

        {incomplete ? (
          <p className="td-param-expression__hint" role="status">
            Expressão incompleta — o backend valida a semântica ao
            aplicar/pré-visualizar.
          </p>
        ) : null}

        {previewError ? (
          <p className="delpi-ui-data-route-preview__error" role="alert">
            {previewError}
          </p>
        ) : null}
        {previewResult ? (
          previewResult.error ? (
            <p className="delpi-ui-data-route-preview__error" role="alert">
              {previewResult.error}
            </p>
          ) : (
            <p className="td-expression-summary__result" role="status">
              Resultado do backend: {formatPreviewValue(previewResult.resolved)}
            </p>
          )
        ) : null}

        <details className="td-expression-editor__technical">
          <summary>Detalhes técnicos (AST v1)</summary>
          <pre className="td-param-expression__json">
            {JSON.stringify(draftAst, null, 2)}
          </pre>
        </details>
      </div>
    </HostContainedModal>
  );
}

function formatPreviewValue(value: unknown): string {
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
