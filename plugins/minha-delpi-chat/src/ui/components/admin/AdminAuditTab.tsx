import type { AdminAuditLog } from "../../../data/api/adminTypes";

type AdminAuditTabProps = {
  auditLogs: AdminAuditLog[];
};

export function AdminAuditTab({ auditLogs }: AdminAuditTabProps) {
  return (
    <article className="mdc-admin-card mdc-admin-card--wide">
      <h2>Auditoria recente</h2>

      {auditLogs.length === 0 ? (
        <p className="mdc-chat-muted">Nenhum evento encontrado.</p>
      ) : (
        <div className="mdc-admin-table-wrap">
          <table className="mdc-admin-table">
            <thead>
              <tr>
                <th>Ação</th>
                <th>Contexto</th>
                <th>Usuário</th>
                <th>Data</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.map((log) => (
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
      )}
    </article>
  );
}
