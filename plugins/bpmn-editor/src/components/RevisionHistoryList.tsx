import { ActionButton } from "@delpi/plugin-ui/index";
import { Eye, Plus, RotateCcw } from "lucide-react";

import type { RevisionSummary } from "../host/types";
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

const dateFmt = new Intl.DateTimeFormat("pt-BR", {
  dateStyle: "short",
  timeStyle: "short",
});

/** Card de revisão — hierarquia: nome amigável (quando informado) ou
 *  número; metadados úteis (data, autor, origem); UUID nunca é primário. */
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
          message="Revisões são marcos imutáveis do modelo. Crie uma para preservar este estado — o salvamento automático continua na cópia de trabalho."
        />
      ) : null}
      <ul className="bpmnm-revision-list">
        {revisions.map((rev) => {
          const title = rev.name?.trim() || `Revisão ${rev.revision_number}`;
          const meta = [
            dateFmt.format(new Date(rev.created_at)),
            rev.created_by_name?.trim() || null,
            rev.origin === "restore" ? "Restauração" : null,
          ]
            .filter(Boolean)
            .join(" · ");
          return (
            <li key={rev.revision_number} className="bpmnm-revision-item">
              <div className="bpmnm-revision-item__main">
                <div className="bpmnm-revision-item__title">
                  <strong>{title}</strong>
                  {rev.name?.trim() ? (
                    <span className="bpmnm-revision-item__tag">
                      Rev. {rev.revision_number}
                    </span>
                  ) : null}
                </div>
                <small>{meta}</small>
                {rev.description ? (
                  <p className="bpmnm-revision-item__desc">{rev.description}</p>
                ) : null}
              </div>
              <div className="bpmnm-revision-item__actions">
                <ActionButton
                  type="button"
                  variant="ghost"
                  title={HELP_TOOLTIPS.revisions.view}
                  aria-label={`Ver revisão ${rev.revision_number}`}
                  onClick={() => onView(rev.revision_number)}
                >
                  <Eye size={14} aria-hidden="true" />
                  Ver
                </ActionButton>
                {canManage && (
                  <ActionButton
                    type="button"
                    title={HELP_TOOLTIPS.revisions.restore}
                    aria-label={`Restaurar revisão ${rev.revision_number}`}
                    onClick={() => onRestore(rev.revision_number)}
                  >
                    <RotateCcw size={14} aria-hidden="true" />
                    Restaurar
                  </ActionButton>
                )}
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
