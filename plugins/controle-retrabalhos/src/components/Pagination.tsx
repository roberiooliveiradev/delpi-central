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

const classNames = compactPaginationBemClasses("cr", {
  ghostBtn: "cr-btn cr-btn--secondary",
});

type PaginationProps = DashboardCompactPaginationProps & {
  footerClassName?: string;
};

export function Pagination({ footerClassName, ...props }: PaginationProps) {
  return (
    <div className={footerClassName}>
      <CompactPagination
        classNames={classNames}
        labels={LABELS}
        layout="flat"
        {...props}
      />
    </div>
  );
}
