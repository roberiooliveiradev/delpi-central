import type { AdminAuditLog, AdminRbacSummary } from "../../../../data/api/adminTypes";

import "./AdminAuditTab.css";

type AdminAuditTabProps = {
  auditLogs: AdminAuditLog[];
  rbac?: AdminRbacSummary | null;
};

export function AdminAuditTab({ auditLogs, rbac }: AdminAuditTabProps) {
  const canViewAudit = Boolean(rbac?.capabilities.canViewAudit);

  if (!canViewAudit) {
    return (
      <section className="mdc-admin-audit-tab">
        <article className="mdc-admin-audit-tab__empty">
          Você não tem permissão para visualizar auditoria.
        </article>
      </section>
    );
  }

  return (
    <section className="mdc-admin-audit-tab">
      <article className="mdc-admin-audit-tab__header">
        <div>
          <p className="mdc-chat-eyebrow">Auditoria</p>
          <h2>Eventos administrativos</h2>
        </div>

        <span>{auditLogs.length} evento(s)</span>
      </article>

      {auditLogs.length === 0 ? (
        <article className="mdc-admin-audit-tab__empty">
          Nenhum evento de auditoria encontrado.
        </article>
      ) : (
        <div className="mdc-admin-audit-tab__list">
          {auditLogs.map((log) => (
            <article key={log.id} className="mdc-admin-audit-tab__item">
              <div>
                <strong>{log.action}</strong>
                <span>{log.context ?? "sem contexto"}</span>
              </div>

              <dl>
                <div>
                  <dt>Usuário</dt>
                  <dd>{log.userId ?? "sistema"}</dd>
                </div>
                <div>
                  <dt>Hash</dt>
                  <dd>{log.promptHash ?? "—"}</dd>
                </div>
                <div>
                  <dt>Data</dt>
                  <dd>{new Date(log.createdAt).toLocaleString()}</dd>
                </div>
              </dl>

              {log.metadata ? (
                <pre>{JSON.stringify(log.metadata, null, 2)}</pre>
              ) : null}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
