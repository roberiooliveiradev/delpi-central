import {
  CompactPagination,
  compactPaginationBemClasses,
  type DashboardCompactPaginationProps,
} from "@delpi/plugin-ui/index";

const LABELS = {
  info: ({ page, totalPages, total }: { page: number; totalPages: number; total: number }) =>
    `Página ${page} / ${totalPages} (${total} registros)`,
  previous: "Anterior",
  next: "Próxima",
  navigationAriaLabel: "Paginação da tabela",
};

const classNames = {
  ...compactPaginationBemClasses("pa", {
    ghostBtn: "pa-btn pa-btn--secondary",
  }),
  root: "pa-pagination pa-table-card__footer",
};

export function Pagination(props: DashboardCompactPaginationProps) {
  return (
    <CompactPagination
      classNames={classNames}
      labels={LABELS}
      layout="flat"
      hideWhenSinglePage
      {...props}
    />
  );
}
