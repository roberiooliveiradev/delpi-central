import { useCallback, useEffect, useState } from "react";
import {
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  ClipboardList,
  FileText,
  GitCompare,
  History,
  ListChecks,
  Plus,
  RotateCcw,
  Search,
} from "lucide-react";

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
  type RevisionDiffRow,
  type RevisionDiffSection,
} from "../utils/planRevisionDiff";
import {
  canRestorePlanRevision,
  planRestoreBlockedReason,
} from "../utils/planRestorePolicy";
import {
  revisionScopeBadgeClass,
  revisionScopeLabel,
} from "../utils/planRevisionLabels";
import { SectionCard } from "./ui/SectionCard";
import { PAC_GHOST_BTN } from "./ui/ghostChrome";

const REVISION_RETENTION_LIMIT = 50;

type Props = {
  planId: string;
  detail: ActionPlanDetail | null | undefined;
  canWrite: boolean;
  onRestored: () => Promise<void>;
  confirm: (options: { title: string; message: string }) => Promise<boolean>;
};

function scopeIcon(scope: string | null | undefined) {
  switch ((scope || "").trim()) {
    case "created":
      return Plus;
    case "status":
      return History;
    case "ishikawa":
    case "five_whys":
      return Search;
    case "rnc_8d":
      return ClipboardList;
    case "actions":
      return ListChecks;
    case "effectiveness":
      return CheckCircle2;
    case "restore":
      return RotateCcw;
    default:
      return FileText;
  }
}

function RevisionDiffPanel({
  loading,
  sections,
}: {
  loading: boolean;
  sections: RevisionDiffSection[];
}) {
  if (loading) {
    return (
      <div className="pac-revision-diff pac-revision-diff--loading">
        <p className="pac-muted">Carregando comparação…</p>
      </div>
    );
  }

  if (sections.length === 0) {
    return (
      <div className="pac-revision-diff pac-revision-diff--empty">
        <GitCompare size={18} aria-hidden />
        <div>
          <p className="pac-revision-diff__empty-title">Sem diferenças visíveis</p>
          <p className="pac-muted">
            Nas seções comparadas, o snapshot desta revisão coincide com o estado atual do plano.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="pac-revision-diff">
      <div className="pac-revision-diff__header">
        <GitCompare size={16} aria-hidden />
        <span>Diferenças em relação ao estado atual</span>
      </div>
      {sections.map((section) => (
        <div key={section.key} className="pac-revision-diff__section">
          <h4 className="pac-revision-diff__section-title">{section.title}</h4>
          <div className="pac-revision-diff__grid" role="table">
            <div className="pac-revision-diff__grid-head" role="row">
              <span role="columnheader">Campo</span>
              <span role="columnheader">Estado atual</span>
              <span role="columnheader">Nesta revisão</span>
            </div>
            {section.rows.map((row: RevisionDiffRow) => (
              <div key={`${section.key}-${row.label}`} className="pac-revision-diff__grid-row" role="row">
                <span className="pac-revision-diff__field" role="cell">{row.label}</span>
                <span className="pac-revision-diff__value pac-revision-diff__value--current" role="cell">
                  {row.current}
                </span>
                <span className="pac-revision-diff__value pac-revision-diff__value--revision" role="cell">
                  {row.revision}
                </span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

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
        <div className="pac-state pac-state--warning" role="status">
          {restoreBlockReason}
        </div>
      ) : null}
      {loading ? <p className="pac-muted">Carregando revisões…</p> : null}
      {error ? (
        <div className="pac-state pac-state--error" role="alert">
          {error}
        </div>
      ) : null}
      {!loading && items.length > 0 ? (
        <>
          <div className="pac-revisions-overview" aria-label="Resumo das revisões">
            <div className="pac-revisions-overview__metric">
              <span className="pac-revisions-overview__label">Revisão atual</span>
              <strong>#{currentRevisionNumber}</strong>
            </div>
            <div className="pac-revisions-overview__metric">
              <span className="pac-revisions-overview__label">Snapshots</span>
              <strong>{items.length}</strong>
            </div>
            <div className="pac-revisions-overview__metric pac-revisions-overview__metric--muted">
              <span className="pac-revisions-overview__label">Retenção</span>
              <span>últimas {REVISION_RETENTION_LIMIT}</span>
            </div>
          </div>

          <ol className="pac-revisions-list">
            {items.map((revision) => {
              const isCurrent = revision.revision_number === currentRevisionNumber;
              const isExpanded = expandedRevision === revision.revision_number;
              const ScopeIcon = scopeIcon(revision.change_scope);
              const actorLabel = formatActorDisplay({
                userId: revision.created_by,
                name: revision.created_by_name,
                email: revision.created_by_email,
              });
              const scopeLabel = revisionScopeLabel(revision.change_scope);
              const scopeBadge = revisionScopeBadgeClass(revision.change_scope);

              return (
                <li
                  key={revision.id}
                  className={`pac-revision-card${isCurrent ? " pac-revision-card--current" : ""}${isExpanded ? " pac-revision-card--expanded" : ""}`}
                >
                  <div className="pac-revision-card__marker" aria-hidden>
                    <ScopeIcon size={16} strokeWidth={2} />
                  </div>

                  <div className="pac-revision-card__body">
                    <div className="pac-revision-card__header">
                      <div className="pac-revision-card__title-row">
                        <span className="pac-revision-card__number">#{revision.revision_number}</span>
                        <span className={`pac-badge ${scopeBadge}`}>{scopeLabel}</span>
                        {isCurrent ? (
                          <span className="pac-badge pac-badge--revision-current">Atual</span>
                        ) : null}
                        {revision.restored_from_revision ? (
                          <span className="pac-revision-card__restore-from">
                            Restaurado de #{revision.restored_from_revision}
                          </span>
                        ) : null}
                      </div>
                      <time className="pac-muted pac-revision-card__date" dateTime={revision.created_at}>
                        {formatDateTime(revision.created_at)}
                      </time>
                    </div>

                    <p className="pac-revision-card__summary">
                      {revision.change_summary || "Alteração registrada sem resumo."}
                    </p>

                    {actorLabel ? (
                      <p className="pac-muted pac-revision-card__author">{actorLabel}</p>
                    ) : null}

                    <div className="pac-revision-card__actions">
                      {!isCurrent ? (
                        <button
                          type="button"
                          className={`${PAC_GHOST_BTN} pac-btn--sm${isExpanded ? " pac-btn--active" : ""}`}
                          onClick={() => void toggleDiff(revision.revision_number)}
                        >
                          {isExpanded ? <ChevronUp size={14} aria-hidden /> : <ChevronDown size={14} aria-hidden />}
                          {loadingDiff === revision.revision_number
                            ? "Carregando…"
                            : isExpanded
                              ? "Ocultar comparação"
                              : "Comparar com atual"}
                        </button>
                      ) : (
                        <span className="pac-revision-card__current-hint">
                          <History size={14} aria-hidden />
                          Estado corrente do plano
                        </span>
                      )}
                      {canWrite && !isCurrent && restoreAllowed ? (
                        <button
                          type="button"
                          className="pac-primary-btn pac-btn--sm"
                          disabled={restoring !== null}
                          onClick={() => void handleRestore(revision)}
                          title="Restaurar esta revisão"
                        >
                          <RotateCcw size={14} aria-hidden />
                          {restoring === revision.revision_number ? "Restaurando…" : "Restaurar"}
                        </button>
                      ) : null}
                    </div>

                    {isExpanded ? (
                      <RevisionDiffPanel
                        loading={loadingDiff === revision.revision_number}
                        sections={expandedDiffSections}
                      />
                    ) : null}
                  </div>
                </li>
              );
            })}
          </ol>
        </>
      ) : null}
    </SectionCard>
  );
}
