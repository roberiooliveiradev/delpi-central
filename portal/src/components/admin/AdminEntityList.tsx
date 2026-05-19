// src/components/admin/AdminEntityList.tsx

import type { ReactNode } from "react";
import { ChevronLeft, ChevronRight, Search } from "lucide-react";
import "./AdminEntityList.css";

export type AdminEntitySummaryItem = {
  label: string;
  value: ReactNode;
};

export type AdminEntityToolbarAction = {
  label: ReactNode;
  active?: boolean;
  danger?: boolean;
  primary?: boolean;
  disabled?: boolean;
  onClick: () => void | Promise<void>;
};

export type AdminEntityBadge = {
  label: ReactNode;
  tone?: "default" | "success" | "danger" | "warning";
};

export type AdminEntityCardAction = {
  label: ReactNode;
  danger?: boolean;
  disabled?: boolean;
  onClick: () => void | Promise<void>;
};

export type AdminEntityPagination = {
  page: number;
  totalPages: number;
  onPrevious: () => void;
  onNext: () => void;
};

type AdminEntityListProps<T> = {
  title: string;
  description?: string;

  summary?: AdminEntitySummaryItem[];

  search?: {
    value: string;
    placeholder: string;
    onChange: (value: string) => void;
  };

  toolbarActions?: AdminEntityToolbarAction[];
  filterSlot?: ReactNode;

  listTitle: string;
  listSubtitle?: string;

  items: T[];
  loading?: boolean;
  emptyText: string;

  getId: (item: T) => string;

  selectedIds?: string[];
  selectionLabel?: string;
  onToggleSelected?: (id: string) => void;
  onSelectVisible?: () => void;
  onClearSelection?: () => void;
  bulkActions?: AdminEntityToolbarAction[];

  pagination?: AdminEntityPagination;

  renderIcon?: (item: T) => ReactNode;
  renderTitle: (item: T) => ReactNode;
  renderSubtitle?: (item: T) => ReactNode;
  renderDescription?: (item: T) => ReactNode;
  renderBadges?: (item: T) => AdminEntityBadge[];
  renderMeta?: (item: T) => ReactNode[];
  renderActions?: (item: T) => AdminEntityCardAction[];

  getItemClassName?: (item: T) => string | undefined;

  className?: string;
};

const getToneClass = (tone?: AdminEntityBadge["tone"]) => {
  if (!tone || tone === "default") return "";
  return `admin-entity-badge-${tone}`;
};

export function AdminEntityList<T>({
  title,
  description,
  summary = [],
  search,
  toolbarActions = [],
  filterSlot,
  listTitle,
  listSubtitle,
  items,
  loading = false,
  emptyText,
  getId,
  selectedIds = [],
  selectionLabel = "itens selecionados",
  onToggleSelected,
  onSelectVisible,
  onClearSelection,
  bulkActions = [],
  pagination,
  renderIcon,
  renderTitle,
  renderSubtitle,
  renderDescription,
  renderBadges,
  renderMeta,
  renderActions,
  getItemClassName,
  className,
}: AdminEntityListProps<T>) {
  const selectedSet = new Set(selectedIds);
  const hasSelection = selectedIds.length > 0;
  const selectable = !!onToggleSelected;

  return (
    <div
      className={[
        "admin-entity-page",
        className ?? "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <section className="admin-entity-header">
        <div>
          <h3>{title}</h3>
          {description && <p>{description}</p>}
        </div>

        {summary.length > 0 && (
          <div className="admin-entity-summary">
            {summary.map((item) => (
              <div
                key={`${item.label}-${String(item.value)}`}
                className="admin-entity-summary-card"
              >
                <strong>{item.value}</strong>
                <span>{item.label}</span>
              </div>
            ))}
          </div>
        )}
      </section>

      {(search || toolbarActions.length > 0) && (
        <section className="admin-entity-toolbar">
          {search && (
            <label className="admin-entity-search">
              <Search size={16} />
              <input
                value={search.value}
                onChange={(event) => search.onChange(event.target.value)}
                placeholder={search.placeholder}
              />
            </label>
          )}

          {toolbarActions.length > 0 && (
            <div className="admin-entity-toolbar-actions">
              {toolbarActions.map((action, index) => (
                <button
                  key={index}
                  type="button"
                  className={[
                    action.active ? "active" : "",
                    action.primary ? "admin-entity-primary-button" : "",
                    action.danger ? "admin-entity-danger-button" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  disabled={action.disabled}
                  onClick={action.onClick}
                >
                  {action.label}
                </button>
              ))}
            </div>
          )}
        </section>
      )}

      {filterSlot ? (
        <section className="admin-entity-filters">{filterSlot}</section>
      ) : null}

      {hasSelection && (
        <section className="admin-entity-selection-bar">
          <span>
            <strong>{selectedIds.length}</strong> {selectionLabel}
          </span>

          <div>
            {onClearSelection && (
              <button type="button" onClick={onClearSelection}>
                Limpar seleção
              </button>
            )}

            {bulkActions.map((action, index) => (
              <button
                key={index}
                type="button"
                className={[
                  action.danger ? "admin-entity-danger-button" : "",
                  action.primary ? "admin-entity-primary-button" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                disabled={action.disabled}
                onClick={action.onClick}
              >
                {action.label}
              </button>
            ))}
          </div>
        </section>
      )}

      <section className="admin-entity-list-shell">
        <div className="admin-entity-list-header">
          <div>
            <strong>{listTitle}</strong>
            {listSubtitle && <span>{listSubtitle}</span>}
          </div>

          {onSelectVisible && (
            <button
              type="button"
              onClick={onSelectVisible}
              disabled={items.length === 0}
            >
              Selecionar visíveis
            </button>
          )}
        </div>

        {loading && (
          <div className="admin-entity-state">Carregando...</div>
        )}

        {!loading && items.length === 0 && (
          <div className="admin-entity-state">{emptyText}</div>
        )}

        {!loading && items.length > 0 && (
          <div className="admin-entity-list">
            {items.map((item) => {
              const id = getId(item);
              const selected = selectedSet.has(id);
              const badges = renderBadges?.(item) ?? [];
              const meta = renderMeta?.(item) ?? [];
              const actions = renderActions?.(item) ?? [];

              const itemClassName = getItemClassName?.(item);

              return (
                <article
                  key={id}
                  className={[
                    "admin-entity-card",
                    selected ? "selected" : "",
                    itemClassName,
                  ]
                    .filter(Boolean)
                    .join(" ")}
                >
                  {selectable && (
                    <label className="admin-entity-card-select">
                      <input
                        type="checkbox"
                        checked={selected}
                        onChange={() => onToggleSelected?.(id)}
                        aria-label={`Selecionar ${String(renderTitle(item))}`}
                      />
                    </label>
                  )}

                  <div className="admin-entity-card-icon" aria-hidden="true">
                    {renderIcon?.(item) ?? "•"}
                  </div>

                  <div className="admin-entity-card-main">
                    <div className="admin-entity-card-title-row">
                      <div>
                        <strong>{renderTitle(item)}</strong>
                        {renderSubtitle && (
                          <span>{renderSubtitle(item)}</span>
                        )}
                      </div>

                      {badges.length > 0 && (
                        <div className="admin-entity-card-pills">
                          {badges.map((badge, index) => (
                            <span
                              key={index}
                              className={[
                                "admin-entity-badge",
                                getToneClass(badge.tone),
                              ]
                                .filter(Boolean)
                                .join(" ")}
                            >
                              {badge.label}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {renderDescription && (
                      <div className="admin-entity-card-description">
                        {renderDescription(item)}
                      </div>
                    )}

                    {meta.length > 0 && (
                      <div className="admin-entity-card-meta">
                        {meta.map((entry, index) => (
                          <span key={index}>{entry}</span>
                        ))}
                      </div>
                    )}
                  </div>

                  {actions.length > 0 && (
                    <div className="admin-entity-card-actions">
                      {actions.map((action, index) => (
                        <button
                          key={index}
                          type="button"
                          className={
                            action.danger
                              ? "admin-entity-danger-button"
                              : ""
                          }
                          disabled={action.disabled}
                          onClick={action.onClick}
                        >
                          {action.label}
                        </button>
                      ))}
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        )}
      </section>

      {pagination && (
        <section className="admin-entity-pagination">
          <button
            type="button"
            onClick={pagination.onPrevious}
            disabled={pagination.page <= 1}
          >
            <ChevronLeft size={16} />
            Anterior
          </button>

          <span>
            Página <strong>{pagination.page}</strong> de{" "}
            <strong>{pagination.totalPages}</strong>
          </span>

          <button
            type="button"
            onClick={pagination.onNext}
            disabled={pagination.page >= pagination.totalPages}
          >
            Próxima
            <ChevronRight size={16} />
          </button>
        </section>
      )}
    </div>
  );
}