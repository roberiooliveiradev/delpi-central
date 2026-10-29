import {
  formatDepartmentIddScore,
  useDepartmentIdd,
} from "../hooks/useDepartmentIdd";
import type { DepartmentIddFilterInput } from "../utils/departmentIddFilters";

type DepartmentIddBadgeProps = {
  departmentId: string;
  filters: DepartmentIddFilterInput;
  classPrefix?: string;
};

export function DepartmentIddBadge({
  departmentId,
  filters,
  classPrefix = "dc",
}: DepartmentIddBadgeProps) {
  const { item, loading } = useDepartmentIdd(departmentId, filters);
  const scoreLabel = loading ? null : formatDepartmentIddScore(item?.score);
  const classification = loading ? null : item?.classification?.trim();

  if (loading) {
    return (
      <div
        className={`${classPrefix}-dept-idd ${classPrefix}-dept-idd--loading`}
        aria-busy="true"
        aria-label="Carregando IDD departamental"
      >
        <span className={`${classPrefix}-dept-idd__label`}>IDD</span>
        <span className={`${classPrefix}-dept-idd__value`}>…</span>
      </div>
    );
  }

  if (!scoreLabel) {
    return null;
  }

  return (
    <div
      className={`${classPrefix}-dept-idd`}
      role="status"
      aria-label={`IDD departamental ${scoreLabel}${
        classification ? `, ${classification}` : ""
      }`}
    >
      <span className={`${classPrefix}-dept-idd__label`}>IDD</span>
      <strong className={`${classPrefix}-dept-idd__value`}>{scoreLabel}</strong>
      {classification ? (
        <span className={`${classPrefix}-dept-idd__classification`}>
          {classification}
        </span>
      ) : null}
    </div>
  );
}
