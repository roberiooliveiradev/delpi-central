import type { AdminAuditLog, AdminRbacSummary } from "../../../../data/api/adminTypes";

import "./AdminAuditTab.css";

type AdminAuditTabProps = {
  auditLogs: AdminAuditLog[];
  rbac?: AdminRbacSummary | null;
};

function formatDate(value?: string | null): string {
  if (!value) {
    return "—";
  }

  try {
    return new Intl.DateTimeFormat("pt-BR", {
      dateStyle: "short",
      timeStyle: "medium",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

function formatJson(value: unknown): string {
  if (!value) {
    return "—";
  }

  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function shortValue(value?: string | null, size = 22): string {
  if (!value) {
    return "—";
  }

  if (value.length <= size) {
    return value;
  }

  return `${value.slice(0, Math.floor(size / 2))}...${value.slice(-8)}`;
}

export function AdminAuditTab({ auditLogs, rbac }: AdminAuditTabProps) {
  if (rbac && !rbac.capabilities.canViewAudit) {
    return (
      <section className="mdc-admin-audit-tab">
        <article className="mdc-admin-audit-empty">
          <p className="mdc-chat-eyebrow">Auditoria</p>
          <h2>Acesso bloqueado</h2>
          <p>Você não tem permissão para visualizar auditoria.</p>
        </article>
      </section>
    );
  }

  return (
    <section className="mdc-admin-audit-tab">
      <header className="mdc-admin-audit-hero">
        <div>
          <p className="mdc-chat-eyebrow">Auditoria</p>
          <h2>Eventos administrativos</h2>
          <p>
            Consulte ações registradas pelo Minha DELPI Chat para rastreabilidade operacional.
          </p>
        </div>

        <strong>{auditLogs.length} evento(s)</strong>
      </header>

      {auditLogs.length === 0 ? (
        <article className="mdc-admin-audit-empty">
          <h3>Nenhum evento encontrado</h3>
          <p>Os eventos administrativos aparecerão aqui conforme o chat for utilizado.</p>
        </article>
      ) : (
        <div className="mdc-admin-audit-list">
          {auditLogs.map((log) => (
            <article className="mdc-admin-audit-card" key={log.id}>
              <div className="mdc-admin-audit-card__header">
                <div>
                  <p className="mdc-chat-eyebrow">{log.context || "geral"}</p>
                  <h3>{log.action}</h3>
                </div>

                <time>{formatDate(log.createdAt)}</time>
              </div>

              <dl className="mdc-admin-audit-card__meta">
                <div>
                  <dt>Usuário</dt>
                  <dd title={log.userId || undefined}>{shortValue(log.userId, 28)}</dd>
                </div>

                <div>
                  <dt>Hash</dt>
                  <dd title={log.promptHash || undefined}>{shortValue(log.promptHash, 30)}</dd>
                </div>
              </dl>

              <details className="mdc-admin-audit-card__details">
                <summary>Ver metadata</summary>
                <pre>{formatJson(log.metadata)}</pre>
              </details>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
