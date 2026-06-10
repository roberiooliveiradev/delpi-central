import type { ReactNode } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

export type ProfileRbacCardItem = {
  id: string;
  label: string;
};

type ProfileRbacCardGridProps = {
  items: ProfileRbacCardItem[];
  icon: ReactNode;
  emptyText?: string;
  variant?: "default" | "permission";
  page?: number;
  pageSize?: number;
  total?: number;
  pageSizeOptions?: number[];
  onPageChange?: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  ariaLabel: string;
};

export function ProfileRbacCardGrid({
  items,
  icon,
  emptyText = "Nenhum registro encontrado.",
  variant = "default",
  page,
  pageSize,
  total,
  pageSizeOptions = [5, 10, 20, 50],
  onPageChange,
  onPageSizeChange,
  ariaLabel,
}: ProfileRbacCardGridProps) {
  const hasPagination =
    typeof page === "number" &&
    typeof pageSize === "number" &&
    typeof total === "number" &&
    typeof onPageChange === "function";

  const totalPages = hasPagination
    ? Math.max(1, Math.ceil(total / pageSize))
    : 1;

  const canGoPrev = hasPagination ? page > 1 : false;
  const canGoNext = hasPagination ? page < totalPages : false;

  if (!items.length) {
    return <p className="profile-rbac-empty">{emptyText}</p>;
  }

  return (
    <div className="profile-rbac-cards">
      <ul
        className={`profile-rbac-card-grid profile-rbac-card-grid--${variant}`}
        aria-label={ariaLabel}
      >
        {items.map((item) => (
          <li key={item.id} className="profile-rbac-card">
            <span className="profile-rbac-card__icon" aria-hidden="true">
              {icon}
            </span>
            <span
              className={
                variant === "permission"
                  ? "profile-rbac-card__title profile-rbac-card__title--mono"
                  : "profile-rbac-card__title"
              }
            >
              {item.label}
            </span>
          </li>
        ))}
      </ul>

      {hasPagination && total > pageSize ? (
        <nav className="profile-rbac-pagination" aria-label={`Paginação — ${ariaLabel}`}>
          <div className="profile-rbac-pagination__controls">
            {typeof onPageSizeChange === "function" ? (
              <label className="profile-rbac-pagination__size">
                <span className="profile-rbac-pagination__size-label">Por página</span>
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

            <button
              type="button"
              className="profile-rbac-pagination__btn"
              disabled={!canGoPrev}
              onClick={() => onPageChange(page - 1)}
            >
              <ChevronLeft size={14} aria-hidden="true" />
              Anterior
            </button>

            <span className="profile-rbac-pagination__info">
              Página {page} de {totalPages} · {total} itens
            </span>

            <button
              type="button"
              className="profile-rbac-pagination__btn"
              disabled={!canGoNext}
              onClick={() => onPageChange(page + 1)}
            >
              Próxima
              <ChevronRight size={14} aria-hidden="true" />
            </button>
          </div>
        </nav>
      ) : null}
    </div>
  );
}
