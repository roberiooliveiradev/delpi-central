import { useEffect, useState } from "react";

import { listMyRequests } from "../api/requestsApi";
import { AppShell } from "../components/AppShell";
import { useRequestsPermissions } from "../security/RequestsPermissionsContext";
import type { RequestSummary } from "../types/requests";

export function MinePage() {
  const access = useRequestsPermissions();
  const [items, setItems] = useState<RequestSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ac = new AbortController();
    listMyRequests({ signal: ac.signal })
      .then((data) => setItems(data.items || []))
      .catch((err: Error) => {
        if (err.name !== "AbortError") setError(err.message);
      });
    return () => ac.abort();
  }, []);

  return (
    <AppShell
      title="Minhas solicitações"
      canCreate={access.canCreateInvoiceIssuance || access.canManage}
    >
      <section className="dashboard-my-requests__panel" data-help="mine">
        {error ? <p className="dashboard-my-requests__error">{error}</p> : null}
        {!error && items.length === 0 ? (
          <p className="dashboard-my-requests__muted">Você ainda não criou solicitações.</p>
        ) : null}
        <table className="dashboard-my-requests__table">
          <thead>
            <tr>
              <th>Número</th>
              <th>Tipo</th>
              <th>Status</th>
              <th>Filial</th>
            </tr>
          </thead>
          <tbody>
            {items.map((row) => (
              <tr key={row.id}>
                <td>
                  <a href={`/apps/my-requests/requests/${row.id}`}>{row.request_number}</a>
                </td>
                <td>{row.type_code}</td>
                <td>{row.status_alias || row.status}</td>
                <td>{row.branch_code || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </AppShell>
  );
}
