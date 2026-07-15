import {
  CompactPagination,
  compactPaginationBemClasses,
} from "@delpi/plugin-ui/index";

type PaginationProps = {
  page: number;
  pageSize: number;
  pageSizeOptions: readonly number[];
  hasNext: boolean;
  loading: boolean;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  ariaLabel?: string;
};

const classNames = compactPaginationBemClasses("ip", {
  ghostBtn: "ip-button",
});

/**
 * Paginação cursor/`hasNext` adaptada ao CompactPagination do kit
 * (total sintético só para habilitar Próxima).
 */
export function Pagination({
  page,
  pageSize,
  pageSizeOptions,
  hasNext,
  loading,
  onPageChange,
  onPageSizeChange,
  ariaLabel = "Paginação do histórico",
}: PaginationProps) {
  const totalPages = hasNext ? page + 1 : Math.max(1, page);
  const total = totalPages * pageSize;

  return (
    <CompactPagination
      page={page}
      pageSize={pageSize}
      total={total}
      totalPages={totalPages}
      pageSizeOptions={pageSizeOptions}
      onPageChange={onPageChange}
      onPageSizeChange={onPageSizeChange}
      disabled={loading}
      classNames={classNames}
      labels={{
        info: ({ page: current }) =>
          `Página ${current}${hasNext ? " · há próxima página" : " · última página"}`,
        pageSizeLabel: "Itens por página",
        previous: "Anterior",
        next: "Próxima",
        navigationAriaLabel: ariaLabel,
      }}
    />
  );
}
