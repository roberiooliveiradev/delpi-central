import { useCallback, useEffect, useState } from "react";

import { getRequest, transitionRequest } from "../api/requestsApi";
import { ActionBar } from "../components/ActionBar";
import { AppShell } from "../components/AppShell";
import { ArtifactsPanel } from "../components/ArtifactsPanel";
import { AttachmentsPanel } from "../components/AttachmentsPanel";
import { CommentsPanel } from "../components/CommentsPanel";
import { TimelinePanel } from "../components/TimelinePanel";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useRequestsPermissions } from "../security/RequestsPermissionsContext";
import type { RequestDetail } from "../types/requests";

type RequestDetailPageProps = {
  requestId: string;
};

export function RequestDetailPage({ requestId }: RequestDetailPageProps) {
  const access = useRequestsPermissions();
  const [request, setRequest] = useState<RequestDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const reload = useCallback(
    async (signal?: AbortSignal) => {
      const data = await getRequest(requestId, { signal });
      setRequest(data);
    },
    [requestId],
  );

  useEffect(() => {
    const ac = new AbortController();
    reload(ac.signal).catch((err: Error) => {
      if (err.name !== "AbortError") setError(err.message);
    });
    return () => ac.abort();
  }, [reload]);

  async function onAction(action: string) {
    if (!request) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await transitionRequest(request.id, action, {
        version: request.version,
        idempotencyKey: crypto.randomUUID(),
      });
      setRequest(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha na transição");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell
      title={request ? request.request_number : "Detalhe"}
      canCreate={access.canCreateInvoiceIssuance || access.canManage}
    >
      <section
        className="dashboard-my-requests__panel"
        data-help="detail"
        title={MY_REQUESTS_HELP_TOOLTIPS.detail.section}
      >
        {error ? <p className="dashboard-my-requests__error">{error}</p> : null}
        {!request && !error ? (
          <p className="dashboard-my-requests__muted">Carregando…</p>
        ) : null}
        {request ? (
          <>
            <dl className="dashboard-my-requests__meta">
              <div>
                <dt>Tipo</dt>
                <dd>{request.type_code}</dd>
              </div>
              <div>
                <dt>Status</dt>
                <dd>{request.status_alias || request.status}</dd>
              </div>
              <div>
                <dt>Filial</dt>
                <dd>{request.branch_code || "—"}</dd>
              </div>
              <div>
                <dt>Solicitante</dt>
                <dd>{request.created_by_name}</dd>
              </div>
            </dl>
            <div title={MY_REQUESTS_HELP_TOOLTIPS.detail.actions}>
              <ActionBar
                actions={request.allowed_actions || []}
                busy={busy}
                onAction={onAction}
              />
            </div>
          </>
        ) : null}
      </section>
      <TimelinePanel requestId={requestId} />
      <CommentsPanel requestId={requestId} />
      <AttachmentsPanel requestId={requestId} />
      <ArtifactsPanel requestId={requestId} />
    </AppShell>
  );
}
