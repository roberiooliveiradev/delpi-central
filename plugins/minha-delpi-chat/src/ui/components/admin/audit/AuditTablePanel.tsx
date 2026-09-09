import type { ReactNode } from "react";

import { ADMIN_HELP } from "../../../../content/adminHelpTooltips";

import type { AdminAuditLog } from "../../../../data/api/adminTypes";
import { AdminDataTable } from "../shared/AdminDataTable";

type AuditTablePanelProps = {
  logs: AdminAuditLog[];
  onSelectLog?: (log: AdminAuditLog) => void;
  footer?: ReactNode;
};

export function AuditTablePanel({ logs, onSelectLog, footer }: AuditTablePanelProps) {
  return (
    <AdminDataTable
      title="Eventos"
      rows={logs}
      rowKey={(log) => String(log.id)}
      emptyMessage="Nenhum evento encontrado para os filtros atuais."
      caption="Registros de auditoria administrativa"
      onRowClick={onSelectLog ? (log) => onSelectLog(log) : undefined}
      footer={footer}
      columns={[
        {
          id: "action",
          header: "Ação",
          headerHint: ADMIN_HELP.fields.audit.colAction,
          render: (log) => log.action,
        },
        {
          id: "context",
          header: "Contexto",
          headerHint: ADMIN_HELP.fields.audit.colContext,
          render: (log) => log.context || "—",
        },
        {
          id: "trace",
          header: "Trace",
          headerHint: ADMIN_HELP.fields.audit.colTrace,
          render: (log) => (log.traceId ? `${log.traceId.slice(0, 10)}…` : "—"),
        },
        {
          id: "user",
          header: "Usuário",
          headerHint: ADMIN_HELP.fields.audit.colUser,
          render: (log) => log.userId || "—",
        },
        {
          id: "date",
          header: "Data",
          headerHint: ADMIN_HELP.fields.audit.colDate,
          render: (log) => new Date(log.createdAt).toLocaleString("pt-BR"),
        },
      ]}
    />
  );
}
