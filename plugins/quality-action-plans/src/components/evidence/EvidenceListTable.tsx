import { Download, Eye, Trash2 } from "lucide-react";
import { useState } from "react";

import {
  deletePlanEvidence,
  downloadPlanEvidenceFile,
} from "../../api/actionPlansApi";
import {
  evidenceSectionLabel,
  evidenceTypeLabel,
} from "../../constants/evidence";
import { PAC_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { PlanAction } from "../../types/actionPlan";
import type { PlanEvidence } from "../../types/rnc8d";
import { formatDateTime } from "../../utils/format";
import { TableHeaderCell } from "../ui/HelpTooltip";
import {
  formatEvidenceFileSize,
  linkedActionCell,
} from "./evidenceAttachmentUtils";
import { EvidencePreviewModal } from "./EvidencePreviewModal";
import { canPreviewEvidence } from "./evidencePreviewUtils";

const T = PAC_HELP_TOOLTIPS.tables;

type Props = {
  planId: string;
  evidences: PlanEvidence[];
  actions?: PlanAction[];
  readOnly?: boolean;
  onChanged: () => void | Promise<void>;
  compact?: boolean;
};

export function EvidenceListTable({
  planId,
  evidences,
  actions = [],
  readOnly = false,
  onChanged,
  compact = false,
}: Props) {
  const [error, setError] = useState<string | null>(null);
  const [previewEvidence, setPreviewEvidence] = useState<PlanEvidence | null>(null);
  const actionById = new Map(actions.map((action) => [action.id, action]));
  const showActionsColumn = true;

  async function handleDelete(evidenceId: string) {
    setError(null);
    try {
      await deletePlanEvidence(planId, evidenceId);
      if (previewEvidence?.id === evidenceId) {
        setPreviewEvidence(null);
      }
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao remover evidência.");
    }
  }

  if (!evidences.length) {
    return <p className="pac-muted">Nenhuma evidência anexada ainda.</p>;
  }

  return (
    <>
      {error ? <p className="pac-muted pac-evidence-list__error">{error}</p> : null}
      <div className={`pac-table-wrap${compact || readOnly ? " pac-table-wrap--compact-read" : ""}`}>
        <table className={`pac-table${compact || readOnly ? " pac-table--compact-read" : ""}`}>
          <thead>
            <tr>
              <TableHeaderCell label="Arquivo" hint={T.file} />
              <TableHeaderCell label="Tipo" hint={T.evidenceType} />
              <TableHeaderCell label="Seção" hint={T.sectionRef} />
              <TableHeaderCell label="Ação" hint={T.linkedAction} />
              <TableHeaderCell label="Tamanho" hint={T.fileSize} />
              <TableHeaderCell label="Enviado em" hint={T.uploadedAt} />
              {showActionsColumn ? (
                <TableHeaderCell
                  label="Ações"
                  hint={T.evidenceActions}
                  className="pac-table__actions-col"
                />
              ) : null}
            </tr>
          </thead>
          <tbody>
            {evidences.map((evidence) => (
              <tr key={evidence.id}>
                <td>
                  <div className="pac-evidence-name">
                    <span>{evidence.file_name ?? evidence.id}</span>
                    {evidence.description ? (
                      <small className="pac-muted">{evidence.description}</small>
                    ) : null}
                  </div>
                </td>
                <td>{evidenceTypeLabel(evidence.type)}</td>
                <td>{evidenceSectionLabel(evidence.section)}</td>
                <td className="pac-table-cell--linked-action">
                  {linkedActionCell(evidence.action_id, actionById)}
                </td>
                <td>{formatEvidenceFileSize(evidence.size_bytes)}</td>
                <td>{formatDateTime(evidence.created_at)}</td>
                {showActionsColumn ? (
                  <td className="pac-table__actions-cell">
                    <div className="pac-table-actions">
                      {canPreviewEvidence(evidence) ? (
                        <button
                          type="button"
                          className="pac-ghost-btn pac-ghost-btn--icon"
                          aria-label="Pré-visualizar evidência"
                          title="Pré-visualizar"
                          onClick={() => setPreviewEvidence(evidence)}
                        >
                          <Eye size={16} />
                        </button>
                      ) : null}
                      <button
                        type="button"
                        className="pac-ghost-btn pac-ghost-btn--icon"
                        aria-label="Baixar evidência"
                        title="Baixar"
                        onClick={() =>
                          void downloadPlanEvidenceFile(
                            planId,
                            evidence.id,
                            evidence.file_name ?? `evidence-${evidence.id}`,
                          )
                        }
                      >
                        <Download size={16} />
                      </button>
                      {!readOnly ? (
                        <button
                          type="button"
                          className="pac-ghost-btn pac-ghost-btn--icon"
                          aria-label="Remover evidência"
                          title="Remover"
                          onClick={() => void handleDelete(evidence.id)}
                        >
                          <Trash2 size={16} />
                        </button>
                      ) : null}
                    </div>
                  </td>
                ) : null}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <EvidencePreviewModal
        planId={planId}
        evidence={previewEvidence}
        open={previewEvidence != null}
        onClose={() => setPreviewEvidence(null)}
      />
    </>
  );
}
