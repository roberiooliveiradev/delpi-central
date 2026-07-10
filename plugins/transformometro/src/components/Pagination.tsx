import {
  CompactPagination,
  compactPaginationBemClasses,
  type CompactPaginationLabels,
} from "@delpi/plugin-ui/index";

const DS_PAGINATION_CLASS_NAMES = compactPaginationBemClasses("ds", {
  ghostBtn: "ds-ghost-btn",
});

const DS_PAGINATION_LABELS = {
  info: ({ page, totalPages, total, pageSize }) => {
    const rangeStart = (page - 1) * pageSize + 1;
    const rangeEnd = Math.min(page * pageSize, total);
    return `Exibindo ${rangeStart}–${rangeEnd} de ${total} · Página ${page} de ${totalPages}`;
  },
  previous: "Anterior",
  next: "Próxima",
  navigationAriaLabel: "Paginação da tabela",
} satisfies CompactPaginationLabels;

type PaginationProps = {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  /** Oculta controles quando há uma única página (padrão: true). */
  hideWhenSinglePage?: boolean;
};

export function Pagination({
  page,
  pageSize,
  total,
  onPageChange,
  hideWhenSinglePage = true,
}: PaginationProps) {
  return (
    <CompactPagination
      page={page}
      pageSize={pageSize}
      total={total}
      onPageChange={onPageChange}
      hideWhenSinglePage={hideWhenSinglePage}
      classNames={DS_PAGINATION_CLASS_NAMES}
      labels={DS_PAGINATION_LABELS}
    />
  );
}
