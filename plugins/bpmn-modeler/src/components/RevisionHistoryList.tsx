import { ActionButton } from "@delpi/plugin-ui/index";
import { Eye, Plus, RotateCcw } from "lucide-react";

import type { RevisionSummary } from "../data/api/bpmnModelerApi";
import { HELP_TOOLTIPS } from "../content/helpTooltips";
import { BpmnmEmptyState } from "../ui/kit";

type Props = {
  revisions: RevisionSummary[];
  loading: boolean;
  canManage: boolean;
  onView: (revisionNumber: number) => void;
  onRestore: (revisionNumber: number) => void;
  onCreateRevision: () => void;
};

export function RevisionHistoryList({
  revisions,
  loading,
  canManage,
  onView,
  onRestore,
  onCreateRevision,
}: Props) {
  return (
    <div className="bpmnm-revisions">
      <div className="bpmnm-revisions__header">
        <h3>Revisões</h3>
        {canManage && (
          <ActionButton
            type="button"
            title={HELP_TOOLTIPS.revisions.create}
            onClick={onCreateRevision}
          >
            <Plus size={15} aria-hidden="true" />
            Criar revisão
          </ActionButton>
        )}
      </div>
      {loading ? <p className="bpmnm-hint" role="status">Carregando…</p> : null}
      {!loading && revisions.length === 0 ? (
        <BpmnmEmptyState
          title="Nenhuma revisão"
          message="Nenhuma revisão ainda. Crie um marco para preservar este estado."
        />
      ) : null}
      <ul className="bpmnm-revision-list">
        {revisions.map((rev) => (
          <li key={rev.revision_number} className="bpmnm-revision-item">
            <div>
              <strong>Revisão {rev.revision_number}</strong>
              <small>
                {new Date(rev.created_at).toLocaleString("pt-BR")} · {rev.created_by}
                {rev.origin === "restore" ? " · restauração" : ""}
              </small>
            </div>
            <div className="bpmnm-revision-item__actions">
              <ActionButton
                type="button"
                variant="ghost"
                title={HELP_TOOLTIPS.revisions.view}
                onClick={() => onView(rev.revision_number)}
              >
                <Eye size={14} aria-hidden="true" />
                Ver
              </ActionButton>
              {canManage && (
                <ActionButton
                  type="button"
                  variant="ghost"
                  title={HELP_TOOLTIPS.revisions.restore}
                  onClick={() => onRestore(rev.revision_number)}
                >
                  <RotateCcw size={14} aria-hidden="true" />
                  Restaurar
                </ActionButton>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
