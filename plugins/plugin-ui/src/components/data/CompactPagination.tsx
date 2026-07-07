export type CompactPaginationClassNames = {
  root: string;
  left: string;
  info: string;
  pageSize: string;
  actions: string;
  ghostBtn: string;
};

export type CompactPaginationLayout = "grouped" | "flat";

export type CompactPaginationLabels = {
  info: (args: { page: number; totalPages: number; total: number }) => string;
  pageSizeLabel?: string;
  previous: string;
  next: string;
  navigationAriaLabel: string;
};

export type CompactPaginationProps = {
  page: number;
  pageSize: number;
  total: number;
  totalPages?: number;
  pageSizeOptions?: readonly number[];
  onPageChange: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  layout?: CompactPaginationLayout;
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
  layout = "grouped",
  classNames,
  labels,
}: CompactPaginationProps) {
  const resolvedTotalPages =
    totalPages ?? (pageSize > 0 ? Math.max(1, Math.ceil(total / pageSize)) : 1);
  const canPrev = page > 1;
  const canNext = page < resolvedTotalPages;
  const showPageSize =
    onPageSizeChange != null && pageSizeOptions != null && pageSizeOptions.length > 0;

  if (total === 0) return null;

  const infoNode = (
    <span className={classNames.info}>
      {labels.info({ page, totalPages: resolvedTotalPages, total })}
    </span>
  );

  const actionsNode = (
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
  );

  if (layout === "flat") {
    return (
      <div className={classNames.root} role="navigation" aria-label={labels.navigationAriaLabel}>
        {infoNode}
        {actionsNode}
      </div>
    );
  }

  return (
    <div className={classNames.root} role="navigation" aria-label={labels.navigationAriaLabel}>
      <div className={classNames.left}>
        {infoNode}
        {showPageSize ? (
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
        ) : null}
      </div>
      {actionsNode}
    </div>
  );
}

export type DashboardCompactPaginationProps = Omit<
  CompactPaginationProps,
  "classNames" | "labels" | "layout"
>;

export function createCompactPagination(config: {
  prefix: string;
  labels: CompactPaginationLabels;
  ghostBtnModifier?: string;
  layout?: CompactPaginationLayout;
}) {
  const classNames = compactPaginationBemClasses(config.prefix, {
    ghostBtnModifier: config.ghostBtnModifier,
  });

  return function DashboardCompactPagination(props: DashboardCompactPaginationProps) {
    return (
      <CompactPagination
        classNames={classNames}
        labels={config.labels}
        layout={config.layout}
        {...props}
      />
    );
  };
}
