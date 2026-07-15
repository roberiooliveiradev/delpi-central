import {
  CompactPagination,
  compactPaginationBemClasses,
  type DashboardCompactPaginationProps,
} from "@delpi/plugin-ui/index";

const LABELS = {
  info: ({ page, totalPages }: { page: number; totalPages: number }) =>
    `Página ${page} / ${totalPages}`,
  previous: "Anterior",
  next: "Próxima",
  navigationAriaLabel: "Paginação dos registros de refugo",
};

const classNames = {
  ...compactPaginationBemClasses("sm", {
    ghostBtn: "sm-btn sm-btn--secondary",
  }),
  root: "sm-pagination sm-table-card__footer",
};

export function Pagination(props: DashboardCompactPaginationProps) {
  return (
    <CompactPagination
      classNames={classNames}
      labels={LABELS}
      layout="flat"
      {...props}
    />
  );
}
