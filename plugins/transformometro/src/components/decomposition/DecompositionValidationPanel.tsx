import {
  scrollToDecompositionNode,
  type DecompositionValidationReport,
} from "../../utils/decompositionValidation";

type Props = {
  report: DecompositionValidationReport | null;
};

export function DecompositionValidationPanel({ report }: Props) {
  if (!report || report.valid) {
    return null;
  }

  return (
    <div className="tm-decomposition-validation" role="alert" aria-live="polite">
      <p className="ds-state ds-state--warn">
        Corrija os itens abaixo antes de salvar o mapeamento.
      </p>
      <ul className="tm-decomposition-validation__issues">
        {report.issues.map((issue, index) => (
          <li
            key={issue.nodeId ?? `${issue.field}-${index}`}
            className="tm-decomposition-validation__issue tm-decomposition-validation__issue--error"
          >
            {issue.nodeId ? (
              <button
                type="button"
                className="tm-decomposition-validation__link"
                onClick={() => scrollToDecompositionNode(issue.nodeId!)}
              >
                {issue.message}
              </button>
            ) : (
              issue.message
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
