import type { TimelineItemModel, TimelineTone } from "@delpi/plugin-ui/index";

import type { KaizenRevision, KaizenRevisionChangeType } from "../../types/kaizen";
import { statusLabel } from "../../utils/labels";
import { Timeline } from "../data";

const DIFF_FIELDS: Array<{ key: string; label: string; kind?: "status" }> = [
  { key: "status", label: "Status", kind: "status" },
  { key: "savings_type", label: "Tipo economia" },
  { key: "daily_savings", label: "Economia/dia" },
  { key: "realized_daily_savings", label: "Realizada/dia" },
  { key: "date_idea_received", label: "Recebimento da ideia" },
  { key: "categories", label: "Categorias" },
  { key: "date_committee_approved", label: "Aprovação no comitê" },
  { key: "date_implemented", label: "Implantação" },
  { key: "title", label: "Título" },
  { key: "branch_code", label: "Unidade" },
];

function formatSnapshotValue(value: unknown, kind?: "status"): string {
  if (value == null || value === "") return "—";
  if (Array.isArray(value)) {
    const items = value.map((item) => String(item).trim()).filter(Boolean);
    return items.length > 0 ? items.join(", ") : "—";
  }
  if (kind === "status") return statusLabel(String(value));
  return String(value);
}

type RevisionDiff = { label: string; from: string; to: string };

function computeDiff(
  current: Record<string, unknown>,
  previous: Record<string, unknown> | undefined,
): RevisionDiff[] {
  if (!previous) return [];
  const diffs: RevisionDiff[] = [];
  for (const field of DIFF_FIELDS) {
    const before = previous[field.key];
    const after = current[field.key];
    if (String(before ?? "") !== String(after ?? "")) {
      diffs.push({
        label: field.label,
        from: formatSnapshotValue(before, field.kind),
        to: formatSnapshotValue(after, field.kind),
      });
    }
  }
  return diffs;
}

const CHANGE_TYPE_LABELS: Record<KaizenRevisionChangeType, string> = {
  baseline: "Baseline",
  implantacao: "Implantação",
  melhoria: "Melhoria",
  correcao: "Correção",
  descontinuacao: "Descontinuação",
  restauracao: "Restauração",
};

const CHANGE_TYPE_TONE: Record<KaizenRevisionChangeType, TimelineTone> = {
  baseline: "default",
  implantacao: "success",
  melhoria: "info",
  correcao: "warning",
  descontinuacao: "danger",
  restauracao: "info",
};

const BADGE_TONE: Record<KaizenRevisionChangeType, string> = {
  baseline: "muted",
  implantacao: "success",
  melhoria: "info",
  correcao: "warning",
  descontinuacao: "danger",
  restauracao: "info",
};

function formatDate(value: string | null): string {
  if (!value) return "—";
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("pt-BR");
}

/** Irmãos com maior revision_number ficam no tronco; demais viram branch visual. */
function resolveBranchKeys(revisions: KaizenRevision[]): Map<string, string> {
  const childrenByParent = new Map<string, KaizenRevision[]>();
  for (const revision of revisions) {
    const parentId = revision.parent_revision_id?.trim();
    if (!parentId) continue;
    const list = childrenByParent.get(parentId) ?? [];
    list.push(revision);
    childrenByParent.set(parentId, list);
  }

  const keys = new Map<string, string>();
  for (const kids of childrenByParent.values()) {
    if (kids.length <= 1) {
      for (const kid of kids) keys.set(kid.id, "main");
      continue;
    }
    const sorted = [...kids].sort((a, b) => a.revision_number - b.revision_number);
    sorted.forEach((kid, index) => {
      keys.set(
        kid.id,
        index === sorted.length - 1 ? "main" : `alt-${kid.revision_number}`,
      );
    });
  }
  return keys;
}

function resolvePreviousRevision(
  revision: KaizenRevision,
  byId: Map<string, KaizenRevision>,
  byNumber: Map<number, KaizenRevision>,
): KaizenRevision | undefined {
  const parentId = revision.parent_revision_id?.trim();
  if (parentId && byId.has(parentId)) {
    return byId.get(parentId);
  }
  return byNumber.get(revision.revision_number - 1);
}

function toRevisionTimelineItem(
  revision: KaizenRevision,
  previous: KaizenRevision | undefined,
  branchKey: string | undefined,
): TimelineItemModel {
  const tone = CHANGE_TYPE_TONE[revision.change_type] ?? "default";
  const badgeTone = BADGE_TONE[revision.change_type] ?? "muted";
  const current = revision.effective_until == null;
  const diffs = computeDiff(revision.snapshot ?? {}, previous?.snapshot);

  return {
    id: revision.id,
    parentId: revision.parent_revision_id,
    branchKey,
    title: (
      <span className="kz-revision-timeline__title">
        <span className="kz-revision-timeline__version">v{revision.revision_number}</span>
        <span className={`kz-badge kz-badge--${badgeTone}`}>
          {CHANGE_TYPE_LABELS[revision.change_type] ?? revision.change_type}
        </span>
        {current ? <span className="kz-badge kz-badge--current">Vigente</span> : null}
      </span>
    ),
    detail: (
      <div className="kz-revision-timeline__detail">
        {revision.change_summary ? (
          <p className="kz-revision-timeline__summary">{revision.change_summary}</p>
        ) : null}
        {revision.change_reason ? (
          <p className="kz-revision-timeline__reason">{revision.change_reason}</p>
        ) : null}
        {diffs.length > 0 ? (
          <ul className="kz-revision-timeline__diff">
            {diffs.map((diff) => (
              <li key={diff.label}>
                <span className="kz-revision-timeline__diff-label">{diff.label}:</span>{" "}
                <span className="kz-revision-timeline__diff-from">{diff.from}</span>
                {" → "}
                <span className="kz-revision-timeline__diff-to">{diff.to}</span>
              </li>
            ))}
          </ul>
        ) : null}
        <p className="kz-revision-timeline__dates">
          Implantação: {formatDate(revision.effective_from)}
          {" → "}
          {revision.effective_until ? formatDate(revision.effective_until) : "atual"}
        </p>
      </div>
    ),
    meta: revision.created_by_name || revision.created_by_user_id || undefined,
    tone,
  };
}

type KaizenRevisionTimelineProps = {
  revisions: KaizenRevision[];
};

export function KaizenRevisionTimeline({ revisions }: KaizenRevisionTimelineProps) {
  const byId = new Map<string, KaizenRevision>();
  const byNumber = new Map<number, KaizenRevision>();
  for (const revision of revisions) {
    byId.set(revision.id, revision);
    byNumber.set(revision.revision_number, revision);
  }
  const branchKeys = resolveBranchKeys(revisions);

  const items = revisions.map((revision) =>
    toRevisionTimelineItem(
      revision,
      resolvePreviousRevision(revision, byId, byNumber),
      branchKeys.get(revision.id),
    ),
  );

  return (
    <Timeline
      layout="tree"
      items={items}
      emptyMessage="Nenhuma revisão registrada."
      aria-label="Versões e mudanças do kaizen"
    />
  );
}
