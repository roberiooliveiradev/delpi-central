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
  navigationAriaLabel: "Paginação dos detalhes",
};

const classNames = {
  ...compactPaginationBemClasses("cr", {
    ghostBtn: "cr-btn cr-btn--secondary",
  }),
  root: "cr-pagination cr-table-card__footer",
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
