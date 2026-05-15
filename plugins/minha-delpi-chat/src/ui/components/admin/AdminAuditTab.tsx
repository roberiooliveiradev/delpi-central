import { useMemo, useState } from "react";

import type { AdminAuditLog } from "../../../data/api/adminTypes";
import "./AdminAuditTab.css";

type AdminAuditTabProps = {
  auditLogs: AdminAuditLog[];
};

const PAGE_SIZE = 10;

export function AdminAuditTab({ auditLogs }: AdminAuditTabProps) {
  const [page, setPage] = useState(0);

  const pageCount = Math.max(1, Math.ceil(auditLogs.length / PAGE_SIZE));
  const safePage = Math.min(page, pageCount - 1);

  const visibleLogs = useMemo(() => {
    const start = safePage * PAGE_SIZE;
    return auditLogs.slice(start, start + PAGE_SIZE);
  }, [auditLogs, safePage]);

  return (
    <article className="mdc-admin-audit">
      <div className="mdc-admin-audit__header">
        <div>
          <h2>Auditoria recente</h2>
          <p className="mdc-chat-muted">
            Eventos operacionais, ingestões, exclusões, mensagens e uso administrativo.
          </p>
        </div>

        <span className="mdc-admin-audit__pill">{auditLogs.length} evento(s)</span>
      </div>

      {auditLogs.length === 0 ? (
        <p className="mdc-chat-muted">Nenhum evento encontrado.</p>
      ) : (
        <>
          <div className="mdc-admin-table-wrap mdc-admin-audit-table-wrap">
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
                {visibleLogs.map((log) => (
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

          <div className="mdc-admin-pagination">
            <span>
              Página {safePage + 1} de {pageCount}
            </span>

            <div>
              <button
                type="button"
                disabled={safePage === 0}
                onClick={() => setPage((current) => Math.max(0, current - 1))}
              >
                Anterior
              </button>
              <button
                type="button"
                disabled={safePage >= pageCount - 1}
                onClick={() =>
                  setPage((current) => Math.min(pageCount - 1, current + 1))
                }
              >
                Próxima
              </button>
            </div>
          </div>
        </>
      )}
    </article>
  );
}
