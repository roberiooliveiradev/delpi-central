import {
  CompactPagination,
  compactPaginationBemClasses,
  type CompactPaginationLabels,
} from "@delpi/plugin-ui";

const KZ_PAGINATION_CLASS_NAMES = compactPaginationBemClasses("kz", {
  ghostBtn: "kz-ghost-btn",
});

const KZ_PAGINATION_LABELS = {
  info: ({ page, totalPages, total }) =>
    `Página ${page} de ${totalPages} · ${total} registro(s)`,
  previous: "Anterior",
  next: "Próxima",
  navigationAriaLabel: "Paginação da tabela",
} satisfies CompactPaginationLabels;

type PaginationProps = {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
};

export function Pagination({ page, pageSize, total, onPageChange }: PaginationProps) {
  return (
    <CompactPagination
      page={page}
      pageSize={pageSize}
      total={total}
      onPageChange={onPageChange}
      layout="flat"
      classNames={KZ_PAGINATION_CLASS_NAMES}
      labels={KZ_PAGINATION_LABELS}
    />
  );
}
