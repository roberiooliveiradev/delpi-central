export type CompactPaginationClassNames = {
  root: string;
  left: string;
  info: string;
  pageSize: string;
  actions: string;
  ghostBtn: string;
};

export type CompactPaginationLabels = {
  info: (args: { page: number; totalPages: number; total: number }) => string;
  pageSizeLabel: string;
  previous: string;
  next: string;
  navigationAriaLabel: string;
};

export type CompactPaginationProps = {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
  pageSizeOptions: readonly number[];
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  classNames: CompactPaginationClassNames;
  labels: CompactPaginationLabels;
};

export function compactPaginationBemClasses(
  prefix: string,
  options?: { ghostBtnModifier?: string },
): CompactPaginationClassNames {
  const base = `${prefix}-pagination`;
  const ghostModifier = options?.ghostBtnModifier ?? "ghost";

  return {
    root: base,
    left: `${base}__left`,
    info: `${base}__info`,
    pageSize: `${base}__size`,
    actions: `${base}__actions`,
    ghostBtn: `${prefix}-btn ${prefix}-btn--${ghostModifier}`,
  };
}

export function CompactPagination({
  page,
  pageSize,
  total,
  totalPages,
  pageSizeOptions,
  onPageChange,
  onPageSizeChange,
  classNames,
  labels,
}: CompactPaginationProps) {
  const canPrev = page > 1;
  const canNext = page < totalPages;

  if (total === 0) return null;

  return (
    <div className={classNames.root} role="navigation" aria-label={labels.navigationAriaLabel}>
      <div className={classNames.left}>
        <span className={classNames.info}>
          {labels.info({ page, totalPages, total })}
        </span>
        <label className={classNames.pageSize}>
          <span>{labels.pageSizeLabel}</span>
          <select
            value={pageSize}
            onChange={(event) => onPageSizeChange(Number(event.target.value))}
          >
            {pageSizeOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className={classNames.actions}>
        <button
          type="button"
          className={classNames.ghostBtn}
          disabled={!canPrev}
          onClick={() => onPageChange(page - 1)}
        >
          {labels.previous}
        </button>
        <button
          type="button"
          className={classNames.ghostBtn}
          disabled={!canNext}
          onClick={() => onPageChange(page + 1)}
        >
          {labels.next}
        </button>
      </div>
    </div>
  );
}

export type DashboardCompactPaginationProps = Omit<
  CompactPaginationProps,
  "classNames" | "labels"
>;

export function createCompactPagination(config: {
  prefix: string;
  labels: CompactPaginationLabels;
  ghostBtnModifier?: string;
}) {
  const classNames = compactPaginationBemClasses(config.prefix, {
    ghostBtnModifier: config.ghostBtnModifier,
  });

  return function DashboardCompactPagination(props: DashboardCompactPaginationProps) {
    return <CompactPagination classNames={classNames} labels={config.labels} {...props} />;
  };
}
