import { useCallback, useEffect, useState } from "react";

import { getRequest, transitionRequest } from "../api/requestsApi";
import { ActionBar } from "../components/ActionBar";
import { AppShell } from "../components/AppShell";
import { ArtifactsPanel } from "../components/ArtifactsPanel";
import { AttachmentsPanel } from "../components/AttachmentsPanel";
import { CommentsPanel } from "../components/CommentsPanel";
import { TimelinePanel } from "../components/TimelinePanel";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { InvoiceIssuancePayloadPanel } from "../features/invoice-issuance/ui/InvoiceIssuancePayloadPanel";
import { useRequestsPermissions } from "../security/RequestsPermissionsContext";
import { canCreateAnyRequest } from "../security/requestsAccess";
import type { RequestDetail } from "../types/requests";
import {
  DetailFields,
  MyRequestsLoadingState,
  MyRequestsSectionCard,
  MyRequestsStateBanner,
} from "../ui/mrUi";

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
      let returnReason: string | undefined;
      let cancelJustification: string | undefined;
      if (action === "return") {
        returnReason = window.prompt("Motivo da devolução") || undefined;
        if (!returnReason) {
          setBusy(false);
          return;
        }
      }
      if (action === "cancel") {
        cancelJustification = window.prompt("Justificativa do cancelamento") || undefined;
        if (!cancelJustification) {
          setBusy(false);
          return;
        }
      }
      const updated = await transitionRequest(request.id, action, {
        version: request.version,
        idempotencyKey: crypto.randomUUID(),
        returnReason,
        cancelJustification,
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
      canCreate={canCreateAnyRequest(access)}
    >
      <MyRequestsSectionCard title="Solicitação">
        <div data-help="detail" title={MY_REQUESTS_HELP_TOOLTIPS.detail.section}>
          {error ? (
            <MyRequestsStateBanner variant="error">{error}</MyRequestsStateBanner>
          ) : null}
          {!request && !error ? <MyRequestsLoadingState /> : null}
          {request ? (
            <>
              <DetailFields
                fields={[
                  { label: "Tipo", value: request.type_code },
                  { label: "Status", value: request.status_alias || request.status },
                  { label: "Filial", value: request.branch_code || "—" },
                  { label: "Solicitante", value: request.created_by_name },
                ]}
              />
              <div title={MY_REQUESTS_HELP_TOOLTIPS.detail.actions}>
                <ActionBar
                  actions={request.allowed_actions || []}
                  busy={busy}
                  onAction={onAction}
                />
              </div>
            </>
          ) : null}
        </div>
      </MyRequestsSectionCard>
      {request?.type_code === "invoice-issuance" ? (
        <InvoiceIssuancePayloadPanel payload={request.payload} />
      ) : null}
      <TimelinePanel requestId={requestId} />
      <CommentsPanel requestId={requestId} />
      <AttachmentsPanel requestId={requestId} />
      <ArtifactsPanel requestId={requestId} />
    </AppShell>
  );
}
