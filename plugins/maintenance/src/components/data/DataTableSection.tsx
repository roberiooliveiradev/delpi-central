import type { ReactNode } from "react";

import { DataTable } from "./DataTable";
import type { DataTableColumn } from "./types";

type DataTableSectionProps<T> = {
  title: string;
  hint?: string;
  badge?: ReactNode;
  actions?: ReactNode;
  toolbar?: ReactNode;
  columns: DataTableColumn<T>[];
  rows: T[];
  loading?: boolean;
  emptyMessage?: string;
  getRowKey: (row: T, index: number) => string;
  getRowClassName?: (row: T) => string | undefined;
  embedded?: boolean;
};

export function DataTableSection<T>({
  title,
  hint,
  badge,
  actions,
  toolbar,
  columns,
  rows,
  loading = false,
  emptyMessage,
  getRowKey,
  getRowClassName,
  embedded = false,
}: DataTableSectionProps<T>) {
  const content = (
    <>
      <div className="dm-section-header">
        <div className="dm-section-header__title-group">
          <h3 className="dm-section-header__title">{title}</h3>
          {hint ? <p className="dm-section-header__hint">{hint}</p> : null}
        </div>
        <div className="dm-section-header__meta">
          {badge ? <span className="dm-badge">{badge}</span> : null}
          {actions}
        </div>
      </div>

      {toolbar ? <div className="dm-section-toolbar">{toolbar}</div> : null}

      <DataTable
        columns={columns}
        rows={rows}
        loading={loading}
        emptyMessage={emptyMessage}
        getRowKey={getRowKey}
        getRowClassName={getRowClassName}
      />
    </>
  );

  if (embedded) {
    return <section className="dm-table-section dm-table-section--embedded">{content}</section>;
  }

  return <section className="dm-card dm-table-section">{content}</section>;
}
