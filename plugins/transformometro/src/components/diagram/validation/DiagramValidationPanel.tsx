import type { DiagramValidationReport } from "../../../data/api/transformometroDiagramApi";
import { StateBox } from "../../StateBox";

type Props = {
  report: DiagramValidationReport | null;
  loading?: boolean;
};

export function DiagramValidationPanel({ report, loading = false }: Props) {
  if (loading) {
    return <p className="ds-hint">Validando diagrama…</p>;
  }
  if (!report) {
    return null;
  }

  return (
    <div className="delpi-ui-bpmn-validation">
      {report.valid ? (
        <p className="ds-hint">Validação estrutural OK.</p>
      ) : (
        <StateBox variant="warning" dismissible={false}>
          <p>Diagrama com erros de validação — revise antes de publicar.</p>
        </StateBox>
      )}

      {report.issues.length ? (
        <ul className="delpi-ui-bpmn-validation__issues">
          {report.issues.map((issue) => (
            <li
              key={`${issue.code}-${issue.node_id ?? issue.message}`}
              className={`delpi-ui-bpmn-validation__issue delpi-ui-bpmn-validation__issue--${issue.severity}`}
            >
              {issue.message}
            </li>
          ))}
        </ul>
      ) : null}

      {report.simulation.completed_count || report.simulation.stuck_count ? (
        <details className="delpi-ui-bpmn-validation__simulation">
          <summary>
            Simulação por token — {report.simulation.completed_count} caminho(s) completo(s),{" "}
            {report.simulation.stuck_count} interrompido(s)
          </summary>
          {report.simulation.completed_paths.map((path, index) => (
            <p key={`done-${index}`} className="ds-hint">
              ✓ {path.path_labels.join(" → ")}
            </p>
          ))}
          {report.simulation.stuck_paths.map((path, index) => (
            <p key={`stuck-${index}`} className="ds-hint">
              ⚠ {path.path_labels.join(" → ")} ({path.reason})
            </p>
          ))}
        </details>
      ) : null}
    </div>
  );
}
