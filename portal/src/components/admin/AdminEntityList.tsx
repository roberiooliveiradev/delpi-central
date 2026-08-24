// src/components/admin/AdminEntityList.tsx

import type { ReactNode } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button, Checkbox, SearchInput } from "../../ui-kit";
import "./AdminEntityList.css";

export type AdminEntitySummaryItem = {
  label: string;
  value: ReactNode;
};

export type AdminEntityToolbarAction = {
  label: ReactNode;
  icon?: ReactNode;
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
  icon?: ReactNode;
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
  onOpenItem?: (item: T) => void;

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
  onOpenItem,
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
            <div className="admin-entity-search">
              <SearchInput
                value={search.value}
                onChange={(event) => search.onChange(event.target.value)}
                onClear={() => search.onChange("")}
                placeholder={search.placeholder}
              />
            </div>
          )}

          {toolbarActions.length > 0 && (
            <div className="admin-entity-toolbar-actions">
              {toolbarActions.map((action, index) => (
                <Button
                  key={index}
                  type="button"
                  size="sm"
                  variant={
                    action.danger
                      ? "danger"
                      : action.primary
                        ? "primary"
                        : "secondary"
                  }
                  pressed={action.active}
                  disabled={action.disabled}
                  onClick={action.onClick}
                  icon={action.icon}
                >
                  {action.label}
                </Button>
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
              <Button type="button" size="sm" variant="ghost" onClick={onClearSelection}>
                Limpar seleção
              </Button>
            )}

            {bulkActions.map((action, index) => (
              <Button
                key={index}
                type="button"
                size="sm"
                variant={
                  action.danger
                    ? "danger"
                    : action.primary
                      ? "primary"
                      : "secondary"
                }
                disabled={action.disabled}
                onClick={action.onClick}
                icon={action.icon}
              >
                {action.label}
              </Button>
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
            <Button
              type="button"
              size="sm"
              variant="secondary"
              onClick={onSelectVisible}
              disabled={items.length === 0}
            >
              Selecionar visíveis
            </Button>
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
                    onOpenItem ? "admin-entity-card--clickable" : "",
                    itemClassName,
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  onClick={
                    onOpenItem
                      ? (event) => {
                          const target = event.target as HTMLElement | null;
                          if (
                            target?.closest(
                              "button, a, input, label, .admin-entity-card-select",
                            )
                          ) {
                            return;
                          }
                          onOpenItem(item);
                        }
                      : undefined
                  }
                  onKeyDown={
                    onOpenItem
                      ? (event) => {
                          if (event.key === "Enter" || event.key === " ") {
                            event.preventDefault();
                            onOpenItem(item);
                          }
                        }
                      : undefined
                  }
                  tabIndex={onOpenItem ? 0 : undefined}
                  role={onOpenItem ? "button" : undefined}
                >
                  {selectable && (
                    <div className="admin-entity-card-select">
                      <Checkbox
                        checked={selected}
                        onChange={() => onToggleSelected?.(id)}
                        aria-label={`Selecionar ${String(renderTitle(item))}`}
                      />
                    </div>
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
                        <Button
                          key={index}
                          type="button"
                          size="sm"
                          variant={action.danger ? "danger-soft" : "secondary"}
                          disabled={action.disabled}
                          onClick={action.onClick}
                          icon={action.icon}
                        >
                          {action.label}
                        </Button>
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
          <Button
            type="button"
            size="sm"
            variant="secondary"
            onClick={pagination.onPrevious}
            disabled={pagination.page <= 1}
            icon={<ChevronLeft size={16} />}
          >
            Anterior
          </Button>

          <span>
            Página <strong>{pagination.page}</strong> de{" "}
            <strong>{pagination.totalPages}</strong>
          </span>

          <Button
            type="button"
            size="sm"
            variant="secondary"
            onClick={pagination.onNext}
            disabled={pagination.page >= pagination.totalPages}
          >
            Próxima
            <ChevronRight size={16} />
          </Button>
        </section>
      )}
    </div>
  );
}