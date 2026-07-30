import { AlertTriangle, CheckCircle2, Loader2, Route, XCircle } from "lucide-react";

import type { DiagramValidationReport } from "../../../data/api/transformometroDiagramApi";

type Props = {
  report: DiagramValidationReport | null;
  loading?: boolean;
  /** `aside` = painel lateral compacto; `stack` = bloco abaixo do editor. */
  layout?: "aside" | "stack";
};

/**
 * Resultado de validação estrutural + simulação por token.
 */
export function DiagramValidationPanel({
  report,
  loading = false,
  layout = "stack",
}: Props) {
  if (loading) {
    return (
      <div
        className={[
          "delpi-ui-bpmn-validation",
          "delpi-ui-bpmn-validation--loading",
          layout === "aside" ? "delpi-ui-bpmn-validation--aside" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        role="status"
      >
        <Loader2 size={16} className="delpi-ui-bpmn-validation__spinner" aria-hidden="true" />
        <p className="delpi-ui-bpmn-validation__loading-text">Validando diagrama…</p>
      </div>
    );
  }
  if (!report) {
    return null;
  }

  const completed = report.simulation.completed_count;
  const stuck = report.simulation.stuck_count;
  const hasSimulation = completed > 0 || stuck > 0;
  const errorCount = report.issues.filter((issue) => issue.severity === "error").length;
  const warningCount = report.issues.filter((issue) => issue.severity === "warning").length;

  return (
    <aside
      className={[
        "delpi-ui-bpmn-validation",
        report.valid ? "delpi-ui-bpmn-validation--ok" : "delpi-ui-bpmn-validation--invalid",
        layout === "aside" ? "delpi-ui-bpmn-validation--aside" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      aria-label="Validação e simulação do diagrama"
    >
      <header className="delpi-ui-bpmn-validation__header">
        <div className="delpi-ui-bpmn-validation__status">
          {report.valid ? (
            <CheckCircle2 size={18} aria-hidden="true" className="delpi-ui-bpmn-validation__status-icon" />
          ) : (
            <XCircle size={18} aria-hidden="true" className="delpi-ui-bpmn-validation__status-icon" />
          )}
          <div className="delpi-ui-bpmn-validation__status-copy">
            <p className="delpi-ui-bpmn-validation__title">
              {report.valid ? "Validação estrutural OK" : "Validação com problemas"}
            </p>
            <p className="delpi-ui-bpmn-validation__subtitle">
              {report.valid
                ? "O diagrama passou nas regras estruturais."
                : "Revise os erros antes de salvar ou publicar."}
            </p>
          </div>
        </div>
        {hasSimulation ? (
          <div className="delpi-ui-bpmn-validation__stats" role="group" aria-label="Resumo da simulação">
            <span className="delpi-ui-bpmn-validation__stat delpi-ui-bpmn-validation__stat--ok">
              {completed} completo{completed === 1 ? "" : "s"}
            </span>
            <span className="delpi-ui-bpmn-validation__stat delpi-ui-bpmn-validation__stat--stuck">
              {stuck} interrompido{stuck === 1 ? "" : "s"}
            </span>
          </div>
        ) : null}
      </header>

      {report.issues.length ? (
        <section className="delpi-ui-bpmn-validation__section" aria-label="Problemas encontrados">
          <h3 className="delpi-ui-bpmn-validation__section-title">
            Problemas
            {errorCount || warningCount ? (
              <span className="delpi-ui-bpmn-validation__section-meta">
                {errorCount ? `${errorCount} erro${errorCount === 1 ? "" : "s"}` : null}
                {errorCount && warningCount ? " · " : null}
                {warningCount ? `${warningCount} aviso${warningCount === 1 ? "" : "s"}` : null}
              </span>
            ) : null}
          </h3>
          <ul className="delpi-ui-bpmn-validation__issues">
            {report.issues.map((issue) => (
              <li
                key={`${issue.code}-${issue.node_id ?? issue.message}`}
                className={`delpi-ui-bpmn-validation__issue delpi-ui-bpmn-validation__issue--${issue.severity}`}
              >
                {issue.severity === "error" ? (
                  <XCircle size={14} aria-hidden="true" />
                ) : (
                  <AlertTriangle size={14} aria-hidden="true" />
                )}
                <span>{issue.message}</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {hasSimulation ? (
        <section className="delpi-ui-bpmn-validation__section" aria-label="Simulação por token">
          <h3 className="delpi-ui-bpmn-validation__section-title">
            <Route size={14} aria-hidden="true" />
            Simulação por token
          </h3>
          <div className="delpi-ui-bpmn-validation__paths">
            {report.simulation.completed_paths.map((path, index) => (
              <article
                key={`done-${index}`}
                className="delpi-ui-bpmn-validation__path delpi-ui-bpmn-validation__path--ok"
              >
                <header className="delpi-ui-bpmn-validation__path-head">
                  <CheckCircle2 size={14} aria-hidden="true" />
                  <span>Caminho {index + 1}</span>
                  <span className="delpi-ui-bpmn-validation__path-meta">{path.steps} etapa(s)</span>
                </header>
                <ol className="delpi-ui-bpmn-validation__path-steps">
                  {path.path_labels.map((label, stepIndex) => (
                    <li key={`${index}-ok-${stepIndex}`}>{label}</li>
                  ))}
                </ol>
              </article>
            ))}
            {report.simulation.stuck_paths.map((path, index) => (
              <article
                key={`stuck-${index}`}
                className="delpi-ui-bpmn-validation__path delpi-ui-bpmn-validation__path--stuck"
              >
                <header className="delpi-ui-bpmn-validation__path-head">
                  <AlertTriangle size={14} aria-hidden="true" />
                  <span>Interrompido {index + 1}</span>
                </header>
                <p className="delpi-ui-bpmn-validation__path-reason">{path.reason}</p>
                <ol className="delpi-ui-bpmn-validation__path-steps">
                  {path.path_labels.map((label, stepIndex) => (
                    <li key={`${index}-stuck-${stepIndex}`}>{label}</li>
                  ))}
                </ol>
              </article>
            ))}
          </div>
        </section>
      ) : null}
    </aside>
  );
}
