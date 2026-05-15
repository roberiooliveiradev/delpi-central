import type { AdminAuditLog } from "../../../../data/api/adminTypes";

import "./AuditSummaryPanel.css";

type AuditSummaryPanelProps = {
  auditLogs: AdminAuditLog[];
};

function countUnique(values: Array<string | null | undefined>) {
  return new Set(values.filter(Boolean)).size;
}

export function AuditSummaryPanel({ auditLogs }: AuditSummaryPanelProps) {
  const contexts = countUnique(auditLogs.map((log) => log.context));
  const users = countUnique(auditLogs.map((log) => log.userId));
  const actions = countUnique(auditLogs.map((log) => log.action));

  return (
    <section className="mdc-audit-summary" aria-label="Resumo da auditoria">
      <article>
        <span>Eventos</span>
        <strong>{auditLogs.length}</strong>
      </article>

      <article>
        <span>Ações</span>
        <strong>{actions}</strong>
      </article>

      <article>
        <span>Contextos</span>
        <strong>{contexts}</strong>
      </article>

      <article>
        <span>Usuários</span>
        <strong>{users}</strong>
      </article>
    </section>
  );
}
