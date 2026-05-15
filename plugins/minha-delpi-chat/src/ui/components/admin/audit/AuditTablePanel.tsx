import type { AdminAuditLog } from "../../../../data/api/adminTypes";

import "./AuditTablePanel.css";

type AuditTablePanelProps = {
  logs: AdminAuditLog[];
};

export function AuditTablePanel({ logs }: AuditTablePanelProps) {
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
            <th>Usuário</th>
            <th>Data</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log) => (
            <tr key={log.id}>
              <td>{log.action}</td>
              <td>{log.context || "-"}</td>
              <td>{log.userId || "-"}</td>
              <td>{new Date(log.createdAt).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
