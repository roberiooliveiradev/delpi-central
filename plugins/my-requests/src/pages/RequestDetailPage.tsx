import { useCallback, useEffect, useMemo, useState } from "react";

import { useMyRequestsFloatingNotice } from "../app/MyRequestsFloatingNoticeProvider";
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
import {
  actionLabel,
  formatDateTimePtBr,
  requestTypeLabel,
  statusLabel,
} from "../content/presentationLabels";
import { InvoiceIssuancePayloadPanel } from "../features/invoice-issuance/ui/InvoiceIssuancePayloadPanel";
import { useRequestsPermissions } from "../security/RequestsPermissionsContext";
import { canCreateAnyRequest } from "../security/requestsAccess";
import type { RequestDetail } from "../types/requests";
import {
  DetailFields,
  MyRequestsJourneyProgressBar,
  MyRequestsLoadingState,
  MyRequestsProgressTracker,
  MyRequestsSectionCard,
  MyRequestsStateBanner,
  MyRequestsStatusBadge,
} from "../ui/mrUi";
import {
  journeyBarSummary,
  mapJourneyStagesToTrackerSteps,
  statusBadgeVariant,
} from "../utils/journeyProgressUi";
import { isTransitionAction } from "../utils/operationalActions";

type RequestDetailPageProps = {
  requestId: string;
};

export function RequestDetailPage({ requestId }: RequestDetailPageProps) {
  const access = useRequestsPermissions();
  const { notifyError, notifySuccess, notifyInfo } = useMyRequestsFloatingNotice();
  const [request, setRequest] = useState<RequestDetail | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [reasonKind, setReasonKind] = useState<ReasonConfirmKind | null>(null);

  const reload = useCallback(
    async (signal?: AbortSignal) => {
      const data = await getRequest(requestId, { signal });
      setRequest(data);
      setLoadError(null);
    },
    [requestId],
  );

  useEffect(() => {
    const ac = new AbortController();
    reload(ac.signal).catch((err: Error) => {
      if (err.name !== "AbortError") setLoadError(err.message);
    });
    return () => ac.abort();
  }, [reload]);

  async function runTransition(
    action: string,
    options?: { returnReason?: string; cancelJustification?: string },
  ) {
    if (!request) return;
    if (!isTransitionAction(action)) {
      notifyInfo("Esta ação não altera o andamento da solicitação.");
      return;
    }
    setBusy(true);
    try {
      const updated = await transitionRequest(request.id, action, {
        version: request.version,
        idempotencyKey: crypto.randomUUID(),
        returnReason: options?.returnReason,
        cancelJustification: options?.cancelJustification,
      });
      setRequest(updated);
      setReasonKind(null);
      notifySuccess(`${actionLabel(action)} concluído.`);
    } catch (err) {
      notifyError(
        err instanceof Error ? err.message : "Não foi possível aplicar a ação.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function onAction(action: string) {
    if (!request) return;
    if (action === "view") {
      return;
    }
    if (action === "edit") {
      notifyInfo(
        "Ajuste os dados quando a solicitação estiver aguardando informação e use Reenviar para continuar.",
        { title: "Editar solicitação" },
      );
      return;
    }
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

  const journey = request?.journey_progress ?? null;
  const trackerSteps = useMemo(
    () => (journey ? mapJourneyStagesToTrackerSteps(journey.stages) : []),
    [journey],
  );
  const capabilities = request?.capabilities ?? null;

  return (
    <AppShell
      title={request ? request.request_number : "Detalhe"}
      canCreate={canCreateAnyRequest(access)}
    >
      <div className="my-requests-detail-layout">
        {loadError ? (
          <MyRequestsStateBanner variant="error">{loadError}</MyRequestsStateBanner>
        ) : null}
        {!request && !loadError ? <MyRequestsLoadingState /> : null}

        {request ? (
          <>
            <header className="my-requests-detail-header">
              <MyRequestsStatusBadge
                label={statusLabel(request.status, request.status_alias)}
                variant={statusBadgeVariant(request.status, journey?.outcome)}
              />
            </header>

            {journey ? (
              <MyRequestsSectionCard
                title="Progresso do atendimento"
                hint={MY_REQUESTS_HELP_TOOLTIPS.detail.progress}
              >
                <div className="my-requests-detail-progress">
                  <MyRequestsProgressTracker
                    steps={trackerSteps}
                    currentStepId={journey.current_stage_id || trackerSteps[0]?.id}
                    density="compact"
                    ariaLabel="Etapas do atendimento"
                  />
                  <MyRequestsJourneyProgressBar
                    value={journey.percentage}
                    label="Progresso do atendimento"
                    summary={journeyBarSummary(journey)}
                    ariaLabel="Percentual do atendimento"
                  />
                </div>
              </MyRequestsSectionCard>
            ) : null}

            {request.return_reason ? (
              <MyRequestsStateBanner variant="error">
                Motivo da devolução: {request.return_reason}
              </MyRequestsStateBanner>
            ) : null}
            {request.cancel_justification ? (
              <MyRequestsStateBanner variant="error">
                Motivo do cancelamento: {request.cancel_justification}
              </MyRequestsStateBanner>
            ) : null}

            <div className="my-requests-detail-split">
              <MyRequestsSectionCard
                title="Dados da solicitação"
                hint={MY_REQUESTS_HELP_TOOLTIPS.detail.section}
              >
                <DetailFields
                  fields={[
                    {
                      label: "Tipo",
                      hint: MY_REQUESTS_HELP_TOOLTIPS.detail.type,
                      value: requestTypeLabel(request.type_code),
                    },
                    {
                      label: "Status",
                      hint: MY_REQUESTS_HELP_TOOLTIPS.detail.status,
                      value: statusLabel(request.status, request.status_alias),
                    },
                    {
                      label: "Filial",
                      hint: MY_REQUESTS_HELP_TOOLTIPS.detail.branch,
                      value: request.branch_code || "—",
                    },
                    {
                      label: "Solicitante",
                      hint: MY_REQUESTS_HELP_TOOLTIPS.detail.requester,
                      value: request.created_by_name,
                    },
                    {
                      label: "Criada em",
                      hint: MY_REQUESTS_HELP_TOOLTIPS.detail.createdAt,
                      value: formatDateTimePtBr(request.created_at),
                    },
                  ]}
                />
              </MyRequestsSectionCard>

              <MyRequestsSectionCard
                title="Ações disponíveis"
                hint={MY_REQUESTS_HELP_TOOLTIPS.detail.actions}
              >
                <ActionBar
                  actions={request.allowed_actions || []}
                  busy={busy}
                  onAction={onAction}
                />
              </MyRequestsSectionCard>
            </div>

            {request.type_code === "invoice-issuance" ? (
              <InvoiceIssuancePayloadPanel payload={request.payload} />
            ) : null}

            <div className="my-requests-detail-history">
              <TimelinePanel requestId={requestId} />
              <CommentsPanel
                requestId={requestId}
                canComment={capabilities?.can_comment ?? false}
              />
            </div>

            <section className="my-requests-detail-docs" aria-label="Documentos">
              <AttachmentsPanel
                requestId={requestId}
                canUpload={capabilities?.can_upload_attachment ?? false}
              />
              <ArtifactsPanel
                requestId={requestId}
                canUpload={capabilities?.can_upload_artifact ?? false}
              />
            </section>
          </>
        ) : null}
      </div>

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
