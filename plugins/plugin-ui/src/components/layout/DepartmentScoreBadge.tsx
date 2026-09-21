import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";

export type DepartmentScoreBadgeClassNames = {
  root: string;
  label: string;
  value: string;
  classification: string;
};

export type DepartmentScoreBadgeProps = {
  classNames: DepartmentScoreBadgeClassNames;
  /** Already formatted score from the SI contract. Never invent 0. */
  scoreLabel?: string | null;
  classification?: string | null;
  loading?: boolean;
  label?: string;
};

export function departmentScoreBadgeBemClasses(prefix: string): DepartmentScoreBadgeClassNames {
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  const base = `${prefix}-dept-idd`;
  const ui = "delpi-ui-dept-idd";
  return {
    root: pair(base, ui),
    label: pair(`${base}__label`, `${ui}__label`),
    value: pair(`${base}__value`, `${ui}__value`),
    classification: pair(`${base}__classification`, `${ui}__classification`),
  };
}

export function DepartmentScoreBadge({
  classNames,
  scoreLabel,
  classification,
  loading = false,
  label = "IDD",
}: DepartmentScoreBadgeProps) {
  const trimmedScore = scoreLabel?.trim() || null;
  const trimmedClassification = classification?.trim() || null;

  if (loading) {
    return (
      <div
        className={withBemModifier(classNames.root, "loading")}
        aria-busy="true"
        aria-label={`Carregando ${label} departamental`}
      >
        <span className={classNames.label}>{label}</span>
        <span className={classNames.value}>…</span>
      </div>
    );
  }

  if (!trimmedScore) {
    return null;
  }

  return (
    <div
      className={classNames.root}
      role="status"
      aria-label={`${label} departamental ${trimmedScore}${
        trimmedClassification ? `, ${trimmedClassification}` : ""
      }`}
    >
      <span className={classNames.label}>{label}</span>
      <strong className={classNames.value}>{trimmedScore}</strong>
      {trimmedClassification ? (
        <span className={classNames.classification}>{trimmedClassification}</span>
      ) : null}
    </div>
  );
}

export type DashboardDepartmentScoreBadgeProps = Omit<DepartmentScoreBadgeProps, "classNames">;

export function createDashboardDepartmentScoreBadge(config: { prefix: string }) {
  const classNames = departmentScoreBadgeBemClasses(config.prefix);
  return function DashboardDepartmentScoreBadge(props: DashboardDepartmentScoreBadgeProps) {
    return <DepartmentScoreBadge classNames={classNames} {...props} />;
  };
}
