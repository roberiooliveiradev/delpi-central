import type { AdminAuditLog } from "../../../../data/api/adminTypes";

import "./AuditTablePanel.css";

type AuditTablePanelProps = {
  logs: AdminAuditLog[];
  onSelectLog?: (log: AdminAuditLog) => void;
};

export function AuditTablePanel({ logs, onSelectLog }: AuditTablePanelProps) {
  if (logs.length === 0) {
    return <p className="mdc-chat-muted">Nenhum evento encontrado para os filtros atuais.</p>;
  }

  return (
    <div className="mdc-audit-table-wrap">
      <table className="mdc-audit-table">
        <thead>
          <tr>
            <th>Ação</th>
            <th>Contexto</th>
            <th>Trace</th>
            <th>Usuário</th>
            <th>Data</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log) => (
            <tr
              key={log.id}
              className={onSelectLog ? "mdc-audit-table__row--clickable" : undefined}
              onClick={() => onSelectLog?.(log)}
            >
              <td>{log.action}</td>
              <td>{log.context || "-"}</td>
              <td>{log.traceId ? `${log.traceId.slice(0, 10)}…` : "-"}</td>
              <td>{log.userId || "-"}</td>
              <td>{new Date(log.createdAt).toLocaleString("pt-BR")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
