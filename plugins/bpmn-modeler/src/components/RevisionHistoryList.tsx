import type { RevisionSummary } from "../data/api/bpmnModelerApi";

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
          <button type="button" className="bpmnm-btn" onClick={onCreateRevision}>
            Criar revisão
          </button>
        )}
      </div>
      {loading ? <p className="bpmnm-hint">Carregando…</p> : null}
      {!loading && revisions.length === 0 ? (
        <p className="bpmnm-hint">Nenhuma revisão ainda.</p>
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
              <button type="button" className="bpmnm-btn bpmnm-btn--ghost" onClick={() => onView(rev.revision_number)}>
                Ver
              </button>
              {canManage && (
                <button type="button" className="bpmnm-btn bpmnm-btn--ghost" onClick={() => onRestore(rev.revision_number)}>
                  Restaurar
                </button>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
