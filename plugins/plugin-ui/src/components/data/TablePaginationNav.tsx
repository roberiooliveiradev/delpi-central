export type TablePaginationNavClassNames = {
  root: string;
  navButton: string;
  info: string;
  current: string;
};

export type TablePaginationNavLabels = {
  previous: string;
  next: string;
  navigationAriaLabel: string;
  infoBeforeCurrent: string;
  infoAfterCurrent: (totalPages: number) => string;
};

export type TablePaginationNavProps = {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  hideWhenSinglePage?: boolean;
  classNames: TablePaginationNavClassNames;
  labels: TablePaginationNavLabels;
};

export function tablePaginationNavBemClasses(prefix: string): TablePaginationNavClassNames {
  const base = `${prefix}-pagination`;

  return {
    root: base,
    navButton: `${prefix}-ghost-btn ${base}__nav`,
    info: `${base}__info`,
    current: `${base}__current`,
  };
}

export function TablePaginationNav({
  page,
  pageSize,
  total,
  onPageChange,
  hideWhenSinglePage = false,
  classNames,
  labels,
}: TablePaginationNavProps) {
  const totalPages = pageSize > 0 ? Math.max(1, Math.ceil(total / pageSize)) : 1;
  const canPrev = page > 1;
  const canNext = page < totalPages;

  if (total === 0) return null;
  if (hideWhenSinglePage && totalPages <= 1) return null;

  return (
    <div className={classNames.root} role="navigation" aria-label={labels.navigationAriaLabel}>
      <button
        type="button"
        className={classNames.navButton}
        disabled={!canPrev}
        onClick={() => onPageChange(page - 1)}
      >
        {labels.previous}
      </button>
      <p className={classNames.info}>
        {labels.infoBeforeCurrent}
        <span className={classNames.current}>{page}</span>
        {labels.infoAfterCurrent(totalPages)}
      </p>
      <button
        type="button"
        className={classNames.navButton}
        disabled={!canNext}
        onClick={() => onPageChange(page + 1)}
      >
        {labels.next}
      </button>
    </div>
  );
}

export type DashboardTablePaginationNavProps = Omit<
  TablePaginationNavProps,
  "classNames" | "labels"
>;

export function createTablePaginationNav(config: {
  prefix: string;
  labels: TablePaginationNavLabels;
}) {
  const classNames = tablePaginationNavBemClasses(config.prefix);

  return function DashboardTablePaginationNav(props: DashboardTablePaginationNavProps) {
    return <TablePaginationNav classNames={classNames} labels={config.labels} {...props} />;
  };
}
