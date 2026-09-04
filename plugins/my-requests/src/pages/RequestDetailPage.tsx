import { useCallback, useEffect, useState } from "react";

import { getRequest, transitionRequest } from "../api/requestsApi";
import { ActionBar } from "../components/ActionBar";
import { AppShell } from "../components/AppShell";
import { ArtifactsPanel } from "../components/ArtifactsPanel";
import { AttachmentsPanel } from "../components/AttachmentsPanel";
import { CommentsPanel } from "../components/CommentsPanel";
import {
  ReasonConfirmModal,
  type ReasonConfirmKind,
} from "../components/ReasonConfirmModal";
import { TimelinePanel } from "../components/TimelinePanel";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { InvoiceIssuancePayloadPanel } from "../features/invoice-issuance/ui/InvoiceIssuancePayloadPanel";
import { useRequestsPermissions } from "../security/RequestsPermissionsContext";
import { canCreateAnyRequest, canProcessAnyRequest } from "../security/requestsAccess";
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
  const [reasonKind, setReasonKind] = useState<ReasonConfirmKind | null>(null);

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

  async function runTransition(
    action: string,
    options?: { returnReason?: string; cancelJustification?: string },
  ) {
    if (!request) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await transitionRequest(request.id, action, {
        version: request.version,
        idempotencyKey: crypto.randomUUID(),
        returnReason: options?.returnReason,
        cancelJustification: options?.cancelJustification,
      });
      setRequest(updated);
      setReasonKind(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha na transição");
    } finally {
      setBusy(false);
    }
  }

  async function onAction(action: string) {
    if (!request) return;
    if (action === "return" || action === "cancel") {
      setReasonKind(action);
      return;
    }
    await runTransition(action);
  }

  function onReasonConfirm(reason: string) {
    if (!reasonKind) return;
    if (reasonKind === "return") {
      void runTransition("return", { returnReason: reason });
      return;
    }
    void runTransition("cancel", { cancelJustification: reason });
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
      <ArtifactsPanel
        requestId={requestId}
        canUpload={canProcessAnyRequest(access)}
      />
      {reasonKind ? (
        <ReasonConfirmModal
          open
          kind={reasonKind}
          busy={busy}
          onClose={() => {
            if (!busy) setReasonKind(null);
          }}
          onConfirm={onReasonConfirm}
        />
      ) : null}
    </AppShell>
  );
}
