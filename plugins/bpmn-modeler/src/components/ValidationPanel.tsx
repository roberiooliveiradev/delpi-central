import { ActionButton } from "@delpi/plugin-ui/index";

import type { ValidationReport } from "../data/api/bpmnModelerApi";
import { BpmnmEmptyState, BpmnmStatusBadge } from "../ui/kit";

type Props = {
  report: ValidationReport | null;
  onSelectIssue?: (reference: string) => void;
};

const SEVERITY_LABEL: Record<string, string> = {
  ERROR: "Erro",
  WARNING: "Aviso",
  INFO: "Info",
};

/** Painel de validação — lista issues do ValidationReport do backend. */
export function ValidationPanel({ report, onSelectIssue }: Props) {
  if (!report) {
    return (
      <BpmnmEmptyState
        title="Sem validação"
        message="Nenhuma validação executada. Use o botão Validar na barra superior."
      />
    );
  }
  if (report.issues.length === 0) {
    return (
      <BpmnmEmptyState
        title="Sem diagnósticos"
        message="Nenhum diagnóstico — o modelo passou nas regras avaliadas."
      />
    );
  }
  return (
    <ul className="bpmnm-issue-list" aria-label="Diagnósticos de validação">
      {report.issues.map((issue, index) => (
        <li
          key={`${issue.rule_id}-${index}`}
          className={`bpmnm-issue bpmnm-issue--${issue.severity.toLowerCase()}`}
        >
          <ActionButton
            type="button"
            variant="link"
            className="bpmnm-issue__link"
            disabled={!issue.element_id || !onSelectIssue}
            onClick={() => issue.element_id && onSelectIssue?.(issue.element_id)}
          >
            <span className="bpmnm-issue__head">
              <BpmnmStatusBadge
                label={SEVERITY_LABEL[issue.severity] ?? issue.severity}
                variant={
                  issue.severity === "ERROR"
                    ? "danger"
                    : issue.severity === "WARNING"
                      ? "warning"
                      : "info"
                }
              />
              <code>{issue.rule_id}</code>
            </span>
            {issue.message}
            {issue.element_id ? <em> ({issue.element_id})</em> : null}
          </ActionButton>
        </li>
      ))}
    </ul>
  );
}
