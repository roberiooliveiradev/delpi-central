import { Fragment, useCallback, useEffect, useState } from "react";
import { ChevronDown, ChevronUp, History, RotateCcw } from "lucide-react";

import {
  fetchPlanRevision,
  fetchPlanRevisions,
  restorePlanRevision,
} from "../api/actionPlansApi";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { ActionPlanDetail, PlanRevisionSummary } from "../types/actionPlan";
import { formatActorDisplay } from "../utils/actorDisplay";
import { formatDateTime } from "../utils/format";
import {
  buildRevisionSnapshotDiff,
  type RevisionDiffSection,
} from "../utils/planRevisionDiff";
import {
  canRestorePlanRevision,
  planRestoreBlockedReason,
} from "../utils/planRestorePolicy";
import { revisionScopeLabel } from "../utils/planRevisionLabels";
import { SectionCard } from "./ui/SectionCard";

const REVISION_RETENTION_LIMIT = 50;

type Props = {
  planId: string;
  detail: ActionPlanDetail | null | undefined;
  canWrite: boolean;
  onRestored: () => Promise<void>;
  confirm: (options: { title: string; message: string }) => Promise<boolean>;
};

export function PlanRevisionsSection({
  planId,
  detail,
  canWrite,
  onRestored,
  confirm,
}: Props) {
  const plan = detail?.plan;
  const [items, setItems] = useState<PlanRevisionSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [restoring, setRestoring] = useState<number | null>(null);
  const [expandedRevision, setExpandedRevision] = useState<number | null>(null);
  const [expandedDiffSections, setExpandedDiffSections] = useState<RevisionDiffSection[]>([]);
  const [loadingDiff, setLoadingDiff] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const restoreAllowed = canRestorePlanRevision(plan);
  const restoreBlockReason = planRestoreBlockedReason(plan);
  const currentRevisionNumber =
    plan?.current_revision_number
    ?? items.reduce((max, item) => Math.max(max, item.revision_number), 0);

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

  async function toggleDiff(revisionNumber: number) {
    if (expandedRevision === revisionNumber) {
      setExpandedRevision(null);
      setExpandedDiffSections([]);
      return;
    }

    if (!detail) {
      return;
    }

    setExpandedRevision(revisionNumber);
    setLoadingDiff(revisionNumber);
    setExpandedDiffSections([]);
    try {
      const revisionDetail = await fetchPlanRevision(planId, revisionNumber);
      const snapshot =
        revisionDetail.snapshot && typeof revisionDetail.snapshot === "object"
          ? revisionDetail.snapshot
          : {};
      setExpandedDiffSections(buildRevisionSnapshotDiff(detail, snapshot));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar diff da revisão.");
      setExpandedRevision(null);
    } finally {
      setLoadingDiff(null);
    }
  }

  async function handleRestore(revision: PlanRevisionSummary) {
    if (!restoreAllowed) {
      return;
    }

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
      setExpandedRevision(null);
      setExpandedDiffSections([]);
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
      subtitle={`Snapshots restauráveis de cada alteração relevante. Mantidas as últimas ${REVISION_RETENTION_LIMIT} revisões por plano.`}
      hint={PAC_HELP_TOOLTIPS.sections.revisions}
    >
      {restoreBlockReason ? (
        <div className="pac-state pac-state--warning" role="status" style={{ marginBottom: "0.75rem" }}>
          {restoreBlockReason}
        </div>
      ) : null}
      {loading ? <p className="pac-muted">Carregando revisões…</p> : null}
      {error ? (
        <div className="pac-state pac-state--error" role="alert" style={{ marginBottom: "0.75rem" }}>
          {error}
        </div>
      ) : null}
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
                <th className="pac-table__actions-col" aria-label="Ações" />
              </tr>
            </thead>
            <tbody>
              {items.map((revision) => {
                const isCurrent = revision.revision_number === currentRevisionNumber;
                const isExpanded = expandedRevision === revision.revision_number;
                const actorLabel = formatActorDisplay({
                  userId: revision.created_by,
                  name: revision.created_by_name,
                  email: revision.created_by_email,
                });
                return (
                  <Fragment key={revision.id}>
                    <tr>
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
                      <td className="pac-table__actions-cell">
                        <div className="pac-table-actions">
                          {!isCurrent ? (
                            <button
                              type="button"
                              className="pac-btn pac-btn--ghost pac-btn--sm"
                              onClick={() => void toggleDiff(revision.revision_number)}
                            >
                              {isExpanded ? (
                                <ChevronUp size={14} aria-hidden />
                              ) : (
                                <ChevronDown size={14} aria-hidden />
                              )}
                              {loadingDiff === revision.revision_number
                                ? "Carregando…"
                                : isExpanded
                                  ? "Ocultar diff"
                                  : "Ver diff"}
                            </button>
                          ) : null}
                          {canWrite && !isCurrent && restoreAllowed ? (
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
                          ) : null}
                          {isCurrent ? (
                            <span className="pac-muted pac-revision-current-hint">
                              <History size={14} aria-hidden />
                              {" "}
                              Estado corrente
                            </span>
                          ) : null}
                        </div>
                      </td>
                    </tr>
                    {isExpanded ? (
                      <tr>
                        <td colSpan={6}>
                          <div className="pac-revision-diff">
                            <p className="pac-muted pac-revision-diff__title">
                              Diferenças por seção em relação ao estado atual
                            </p>
                            {loadingDiff === revision.revision_number ? (
                              <p className="pac-muted">Carregando comparação…</p>
                            ) : expandedDiffSections.length > 0 ? (
                              expandedDiffSections.map((section) => (
                                <div key={section.key} className="pac-revision-diff__section">
                                  <h4 className="pac-revision-diff__section-title">{section.title}</h4>
                                  <ul className="pac-revision-diff__list">
                                    {section.rows.map((row) => (
                                      <li key={`${section.key}-${row.label}`}>
                                        <strong>{row.label}:</strong>{" "}
                                        atual «{row.current}» · na revisão «{row.revision}»
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              ))
                            ) : (
                              <p className="pac-muted">
                                Nenhuma diferença nas seções comparadas em relação ao estado atual.
                              </p>
                            )}
                          </div>
                        </td>
                      </tr>
                    ) : null}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : null}
    </SectionCard>
  );
}
