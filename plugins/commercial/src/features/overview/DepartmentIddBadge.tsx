import {
  formatDepartmentIddScore,
  useDepartmentIdd,
} from "./useDepartmentIdd";
import type { DepartmentIddFilterInput } from "./departmentIddFilters";

type DepartmentIddBadgeProps = {
  departmentId?: string;
  filters: DepartmentIddFilterInput;
};

export function DepartmentIddBadge({
  departmentId = "commercial",
  filters,
}: DepartmentIddBadgeProps) {
  const { item, loading } = useDepartmentIdd(departmentId, filters);
  const scoreLabel = loading ? null : formatDepartmentIddScore(item?.score);
  const classification = loading ? null : item?.classification?.trim();

  if (loading) {
    return (
      <div
        className="cm-dept-idd cm-dept-idd--loading"
        aria-busy="true"
        aria-label="Carregando IDD departamental"
      >
        <span className="cm-dept-idd__label">IDD</span>
        <span className="cm-dept-idd__value">…</span>
      </div>
    );
  }

  if (!scoreLabel) {
    return null;
  }

  return (
    <div
      className="cm-dept-idd"
      role="status"
      aria-label={`IDD departamental ${scoreLabel}${
        classification ? `, ${classification}` : ""
      }`}
    >
      <span className="cm-dept-idd__label">IDD</span>
      <strong className="cm-dept-idd__value">{scoreLabel}</strong>
      {classification ? (
        <span className="cm-dept-idd__classification">{classification}</span>
      ) : null}
    </div>
  );
}
