import { useCallback, useEffect, useMemo, useState } from "react";
import { History, RotateCcw } from "lucide-react";

import {
  fetchPlanRevisions,
  restorePlanRevision,
} from "../api/actionPlansApi";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { PlanRevisionSummary } from "../types/actionPlan";
import { formatActorDisplay } from "../utils/actorDisplay";
import { formatDateTime } from "../utils/format";
import { revisionScopeLabel } from "../utils/planRevisionLabels";
import { SectionCard } from "./ui/SectionCard";

type Props = {
  planId: string;
  canWrite: boolean;
  onRestored: () => Promise<void>;
  confirm: (options: { title: string; message: string }) => Promise<boolean>;
};

export function PlanRevisionsSection({ planId, canWrite, onRestored, confirm }: Props) {
  const [items, setItems] = useState<PlanRevisionSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [restoring, setRestoring] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchPlanRevisions(planId);
      setItems(result.items);
    } catch (err) {
      setItems([]);
      setError(err instanceof Error ? err.message : "Erro ao carregar revisões.");
    } finally {
      setLoading(false);
    }
  }, [planId]);

  useEffect(() => {
    void load();
  }, [load]);

  const currentRevisionNumber = useMemo(
    () => items.reduce((max, item) => Math.max(max, item.revision_number), 0),
    [items],
  );

  async function handleRestore(revision: PlanRevisionSummary) {
    const summary = (revision.change_summary || "").trim();
    const scopeLabel = revisionScopeLabel(revision.change_scope);
    const accepted = await confirm({
      title: `Restaurar revisão #${revision.revision_number}?`,
      message:
        `O plano voltará ao estado salvo nesta revisão (${scopeLabel}).`
        + (summary ? `\n\nResumo: ${summary}` : "")
        + "\n\nUma nova revisão será criada no histórico; revisões anteriores permanecem registradas.",
    });
    if (!accepted) {
      return;
    }

    setRestoring(revision.revision_number);
    setError(null);
    try {
      await restorePlanRevision(planId, revision.revision_number);
      await onRestored();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao restaurar revisão.");
    } finally {
      setRestoring(null);
    }
  }

  if (!loading && items.length === 0 && !error) {
    return null;
  }

  return (
    <SectionCard
      title="Revisões do plano"
      subtitle="Snapshots restauráveis de cada alteração relevante."
      hint={PAC_HELP_TOOLTIPS.sections.revisions}
    >
      {loading ? <p className="pac-muted">Carregando revisões…</p> : null}
      {error ? <p className="pac-alert pac-alert--error">{error}</p> : null}
      {!loading && items.length > 0 ? (
        <div className="pac-table-wrap pac-table-wrap--compact-read">
          <table className="pac-table pac-table--compact-read">
            <thead>
              <tr>
                <th>Revisão</th>
                <th>Alteração</th>
                <th>Resumo</th>
                <th>Autor</th>
                <th>Data</th>
                {canWrite ? <th className="pac-table__actions-col" aria-label="Ações" /> : null}
              </tr>
            </thead>
            <tbody>
              {items.map((revision) => {
                const isCurrent = revision.revision_number === currentRevisionNumber;
                const actorLabel = formatActorDisplay({
                  userId: revision.created_by,
                  name: revision.created_by_name,
                  email: revision.created_by_email,
                });
                return (
                  <tr key={revision.id}>
                    <td>
                      <span className="pac-revision-number">
                        #{revision.revision_number}
                      </span>
                      {isCurrent ? (
                        <span className="pac-badge pac-badge--muted">atual</span>
                      ) : null}
                      {revision.restored_from_revision ? (
                        <span className="pac-muted pac-revision-restore-from">
                          {" "}
                          (de #{revision.restored_from_revision})
                        </span>
                      ) : null}
                    </td>
                    <td>{revisionScopeLabel(revision.change_scope)}</td>
                    <td>{revision.change_summary || "—"}</td>
                    <td className="pac-muted">{actorLabel || "—"}</td>
                    <td className="pac-muted">{formatDateTime(revision.created_at)}</td>
                    {canWrite ? (
                      <td className="pac-table__actions-cell">
                        {!isCurrent ? (
                          <button
                            type="button"
                            className="pac-btn pac-btn--ghost pac-btn--sm"
                            disabled={restoring !== null}
                            onClick={() => void handleRestore(revision)}
                            title="Restaurar esta revisão"
                          >
                            <RotateCcw size={14} aria-hidden />
                            {restoring === revision.revision_number ? "Restaurando…" : "Restaurar"}
                          </button>
                        ) : (
                          <span className="pac-muted pac-revision-current-hint">
                            <History size={14} aria-hidden />
                            {" "}
                            Estado corrente
                          </span>
                        )}
                      </td>
                    ) : null}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : null}
    </SectionCard>
  );
}
