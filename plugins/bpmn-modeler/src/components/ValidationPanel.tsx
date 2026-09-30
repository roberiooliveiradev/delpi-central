import type { ValidationReport } from "../data/api/bpmnModelerApi";

type Props = {
  report: ValidationReport | null;
  onSelectIssue?: (reference: string) => void;
};

/** Painel de validação — lista issues do ValidationReport do backend. */
export function ValidationPanel({ report, onSelectIssue }: Props) {
  if (!report) {
    return <p className="bpmnm-hint">Nenhuma validação executada.</p>;
  }
  if (report.issues.length === 0) {
    return <p className="bpmnm-hint">Nenhum diagnóstico.</p>;
  }
  return (
    <ul className="bpmnm-issue-list" aria-label="Diagnósticos de validação">
      {report.issues.map((issue, index) => (
        <li
          key={`${issue.rule_id}-${index}`}
          className={`bpmnm-issue bpmnm-issue--${issue.severity.toLowerCase()}`}
        >
          <button
            type="button"
            className="bpmnm-issue__link"
            disabled={!issue.element_id || !onSelectIssue}
            onClick={() => issue.element_id && onSelectIssue?.(issue.element_id)}
          >
            <code>{issue.rule_id}</code> — {issue.message}
            {issue.element_id ? <em> ({issue.element_id})</em> : null}
          </button>
        </li>
      ))}
    </ul>
  );
}
