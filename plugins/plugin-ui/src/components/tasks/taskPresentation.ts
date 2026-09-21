export type TaskItemActionFlags = {
  canOpen?: boolean;
  canEdit?: boolean;
  canComplete?: boolean;
  canCancel?: boolean;
};

/** Descriptor de apresentação. O kit não conhece entidade de domínio. */
export type TaskItemPresentation = {
  id: string;
  title: string;
  description?: string | null;
  sourceLabel?: string | null;
  statusLabel: string;
  statusTone?: "neutral" | "info" | "warning" | "danger" | "success";
  assigneeLabel?: string | null;
  dueDateLabel?: string | null;
  contextLabel?: string | null;
  overdue?: boolean;
  route?: string | null;
  actions?: TaskItemActionFlags;
};

export type TaskWorkspaceSummary = {
  pending: number;
  dueSoon?: number;
  overdue?: number;
};

export type TaskWorkspaceHighlight = {
  id: string;
  label: string;
  value: string;
  tone?: "warning" | "danger";
  loading?: boolean;
};

export function buildTaskWorkspaceHighlights(
  summary: TaskWorkspaceSummary,
  options?: { loading?: boolean; includeDueBuckets?: boolean },
): TaskWorkspaceHighlight[] {
  const loading = options?.loading === true;
  const includeDue = options?.includeDueBuckets !== false;
  const highlights: TaskWorkspaceHighlight[] = [
    {
      id: "pending",
      label: "Pendentes",
      value: String(summary.pending),
      loading,
    },
  ];
  if (includeDue && summary.dueSoon != null) {
    highlights.push({
      id: "due-soon",
      label: "Vencendo",
      value: String(summary.dueSoon),
      tone: summary.dueSoon > 0 ? "warning" : undefined,
      loading,
    });
  }
  if (includeDue && summary.overdue != null) {
    highlights.push({
      id: "overdue",
      label: "Vencidas",
      value: String(summary.overdue),
      tone: summary.overdue > 0 ? "danger" : undefined,
      loading,
    });
  }
  return highlights;
}
