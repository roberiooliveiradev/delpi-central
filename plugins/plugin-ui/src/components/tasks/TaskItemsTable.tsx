import { ActionButton } from "../actions/ActionButton";
import { DataTable, dataTableBemClasses, type DataTableColumn } from "../data/DataTable";
import { StatusBadge, statusBadgeBemClasses } from "../feedback/StatusBadge";
import type { TaskItemPresentation } from "./taskPresentation";

export type TaskItemsTableProps = {
  items: TaskItemPresentation[];
  emptyMessage?: string;
  refreshing?: boolean;
  onOpen?: (item: TaskItemPresentation) => void;
  onEdit?: (item: TaskItemPresentation) => void;
  onComplete?: (item: TaskItemPresentation) => void;
  onCancel?: (item: TaskItemPresentation) => void;
};

const TABLE = dataTableBemClasses("delpi-ui");
const BADGE = statusBadgeBemClasses("delpi-ui");

export function TaskItemsTable({
  items,
  emptyMessage = "Nenhuma tarefa pendente no momento.",
  refreshing = false,
  onOpen,
  onEdit,
  onComplete,
  onCancel,
}: TaskItemsTableProps) {
  const columns: DataTableColumn<TaskItemPresentation>[] = [
    { key: "title", header: "Tarefa", render: (row) => row.title },
    { key: "source", header: "Origem", render: (row) => row.sourceLabel ?? "—" },
    {
      key: "status",
      header: "Status",
      render: (row) => (
        <StatusBadge
          classNames={BADGE}
          label={row.overdue ? `${row.statusLabel} · vencida` : row.statusLabel}
          variant={row.overdue ? "danger" : row.statusTone === "success" ? "success" : "info"}
        />
      ),
    },
    { key: "due", header: "Prazo", render: (row) => row.dueDateLabel ?? "—" },
    { key: "assignee", header: "Responsável", render: (row) => row.assigneeLabel ?? "—" },
    { key: "context", header: "Contexto", render: (row) => row.contextLabel ?? "—" },
    {
      key: "actions",
      header: "Ações",
      interactive: true,
      render: (row) => (
        <div className="delpi-ui-task-items-table__actions">
          {row.actions?.canOpen && onOpen ? (
            <ActionButton variant="link" onClick={() => onOpen(row)}>
              Abrir
            </ActionButton>
          ) : null}
          {row.actions?.canEdit && onEdit ? (
            <ActionButton variant="link" onClick={() => onEdit(row)}>
              Editar
            </ActionButton>
          ) : null}
          {row.actions?.canComplete && onComplete ? (
            <ActionButton variant="link" onClick={() => onComplete(row)}>
              Concluir
            </ActionButton>
          ) : null}
          {row.actions?.canCancel && onCancel ? (
            <ActionButton variant="link" onClick={() => onCancel(row)}>
              Cancelar
            </ActionButton>
          ) : null}
        </div>
      ),
    },
  ];

  return (
    <div aria-busy={refreshing || undefined}>
      <DataTable
        classNames={TABLE}
        labels={{
          emptyMessage,
          loadingMessage: "Carregando…",
          sortByAriaLabel: (header) => `Ordenar por ${header}`,
          headerHelpAriaLabel: (header) => `Ajuda: ${header}`,
        }}
        columns={columns}
        rows={items}
        rowKey={(row) => row.id}
        emptyMessage={emptyMessage}
      />
    </div>
  );
}
