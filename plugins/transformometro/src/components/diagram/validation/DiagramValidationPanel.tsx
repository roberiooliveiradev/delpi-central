import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  Loader2,
  PanelRightOpen,
  Route,
  X,
  XCircle,
} from "lucide-react";

import type { DiagramValidationReport } from "../../../data/api/transformometroDiagramApi";

type Props = {
  report: DiagramValidationReport | null;
  loading?: boolean;
  /** `aside` = painel lateral compacto; `stack` = bloco abaixo do editor. */
  layout?: "aside" | "stack";
  /** Recolhe o painel a um trilho estreito (só layout aside). */
  collapsed?: boolean;
  onCollapse?: () => void;
  onExpand?: () => void;
  onClose?: () => void;
};

/**
 * Resultado de validação estrutural + simulação por token.
 */
export function DiagramValidationPanel({
  report,
  loading = false,
  layout = "stack",
  collapsed = false,
  onCollapse,
  onExpand,
  onClose,
}: Props) {
  const isAside = layout === "aside";
  const showChrome = Boolean(onClose || (isAside && (onCollapse || onExpand)));

  if (isAside && collapsed) {
    return (
      <div
        className="delpi-ui-bpmn-validation delpi-ui-bpmn-validation--rail"
        role="complementary"
        aria-label="Validação recolhida"
      >
        <button
          type="button"
          className="delpi-ui-bpmn-validation__rail-btn"
          onClick={onExpand}
          aria-label="Expandir painel de validação"
          title="Expandir validação"
        >
          <PanelRightOpen size={16} aria-hidden="true" />
          <span className="delpi-ui-bpmn-validation__rail-label">Validação</span>
        </button>
        {onClose ? (
          <button
            type="button"
            className="delpi-ui-bpmn-validation__icon-btn"
            onClick={onClose}
            aria-label="Fechar painel de validação"
            title="Fechar"
          >
            <X size={14} aria-hidden="true" />
          </button>
        ) : null}
      </div>
    );
  }

  if (loading) {
    return (
      <div
        className={[
          "delpi-ui-bpmn-validation",
          "delpi-ui-bpmn-validation--loading",
          isAside ? "delpi-ui-bpmn-validation--aside" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        role="status"
      >
        {showChrome ? (
          <div className="delpi-ui-bpmn-validation__toolbar">
            <span className="delpi-ui-bpmn-validation__toolbar-spacer" />
            {isAside && onCollapse ? (
              <button
                type="button"
                className="delpi-ui-bpmn-validation__icon-btn"
                onClick={onCollapse}
                aria-label="Recolher painel de validação"
                title="Recolher"
              >
                <ChevronRight size={14} aria-hidden="true" />
              </button>
            ) : null}
            {onClose ? (
              <button
                type="button"
                className="delpi-ui-bpmn-validation__icon-btn"
                onClick={onClose}
                aria-label="Fechar painel de validação"
                title="Fechar"
              >
                <X size={14} aria-hidden="true" />
              </button>
            ) : null}
          </div>
        ) : null}
        <div className="delpi-ui-bpmn-validation__loading-row">
          <Loader2 size={16} className="delpi-ui-bpmn-validation__spinner" aria-hidden="true" />
          <p className="delpi-ui-bpmn-validation__loading-text">Validando diagrama…</p>
        </div>
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
        isAside ? "delpi-ui-bpmn-validation--aside" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      aria-label="Validação e simulação do diagrama"
    >
      <header className="delpi-ui-bpmn-validation__header">
        <div className="delpi-ui-bpmn-validation__header-row">
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
          {showChrome ? (
            <div className="delpi-ui-bpmn-validation__toolbar">
              {isAside && onCollapse ? (
                <button
                  type="button"
                  className="delpi-ui-bpmn-validation__icon-btn"
                  onClick={onCollapse}
                  aria-label="Recolher painel de validação"
                  title="Recolher"
                >
                  <ChevronRight size={14} aria-hidden="true" />
                </button>
              ) : null}
              {onClose ? (
                <button
                  type="button"
                  className="delpi-ui-bpmn-validation__icon-btn"
                  onClick={onClose}
                  aria-label="Fechar painel de validação"
                  title="Fechar"
                >
                  <X size={14} aria-hidden="true" />
                </button>
              ) : null}
            </div>
          ) : null}
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
