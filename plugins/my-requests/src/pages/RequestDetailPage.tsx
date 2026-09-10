import { ActionButton } from "@delpi/plugin-ui/index";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useMyRequestsFloatingNotice } from "../app/MyRequestsFloatingNoticeProvider";
import { useMyRequestsDetailSync } from "../app/MyRequestsRealtimeProvider";
import { getRequest, transitionRequest } from "../api/requestsApi";
import { ActionBar } from "../components/ActionBar";
import { AppShell } from "../components/AppShell";
import { ArtifactsPanel } from "../components/ArtifactsPanel";
import { AttachmentsPanel } from "../components/AttachmentsPanel";
import { CommentsPanel } from "../components/CommentsPanel";
import { PersonIdentity } from "../components/PersonIdentity";
import {
  ReasonConfirmModal,
  type ReasonConfirmKind,
  type ReasonConfirmResult,
} from "../components/ReasonConfirmModal";
import { TimelinePanel } from "../components/TimelinePanel";
import {
  correctionTargetLabels,
  correctionTargetOptionsForType,
} from "../content/correctionTargets";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  actionSuccessMessage,
  formatDateTimePtBr,
  requestTypeLabel,
  statusLabel,
} from "../content/presentationLabels";
import { InvoiceIssuancePayloadPanel } from "../features/invoice-issuance/ui/InvoiceIssuancePayloadPanel";
import {
  myRequestsEditPath,
  navigateMyRequestsPath,
} from "../hooks/myRequestsNavigation";
import { useParticipantAvatarUrls } from "../hooks/useParticipantAvatarUrls";
import { useViewportMaxWidth } from "../hooks/useViewportMaxWidth";
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
  journeyTrackerCompactSummary,
  mapJourneyStagesToTrackerSteps,
  statusBadgeVariant,
} from "../utils/journeyProgressUi";
import { isTransitionAction } from "../utils/operationalActions";

type RequestDetailPageProps = {
  requestId: string;
};

export function RequestDetailPage({ requestId }: RequestDetailPageProps) {
  const { notifyError, notifySuccess, notifyInfo } = useMyRequestsFloatingNotice();
  const [request, setRequest] = useState<RequestDetail | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [reasonKind, setReasonKind] = useState<ReasonConfirmKind | null>(null);
  const [timelineEpoch, setTimelineEpoch] = useState(0);
  const compactDensity = useViewportMaxWidth(768);

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

  const onRealtimeChanged = useCallback(() => {
    void reload().catch((err: Error) => {
      if (err.name !== "AbortError") setLoadError(err.message);
    });
    setTimelineEpoch((value) => value + 1);
  }, [reload]);

  const onRealtimeTimeline = useCallback(() => {
    setTimelineEpoch((value) => value + 1);
  }, []);

  useMyRequestsDetailSync(
    requestId,
    { onChanged: onRealtimeChanged, onTimeline: onRealtimeTimeline },
  );

  async function runTransition(
    action: string,
    options?: {
      returnReason?: string;
      cancelJustification?: string;
      correctionTargets?: string[];
    },
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
        correctionTargets: options?.correctionTargets,
      });
      setRequest(updated);
      setReasonKind(null);
      notifySuccess(actionSuccessMessage(action));
    } catch (err) {
      notifyError(
        err instanceof Error ? err.message : "Não foi possível aplicar a ação.",
      );
    } finally {
      setBusy(false);
    }
  }

  function openEdit() {
    navigateMyRequestsPath(myRequestsEditPath(requestId));
  }

  async function onAction(action: string) {
    if (!request) return;
    if (action === "view") {
      return;
    }
    if (action === "edit") {
      openEdit();
      return;
    }
    if (action === "return" || action === "cancel" || action === "reject_fulfillment") {
      setReasonKind(action);
      return;
    }
    await runTransition(action);
  }

  function onReasonConfirm(result: ReasonConfirmResult) {
    if (!reasonKind) return;
    if (reasonKind === "return") {
      void runTransition("return", {
        returnReason: result.reason,
        correctionTargets: result.correctionTargets,
      });
      return;
    }
    if (reasonKind === "reject_fulfillment") {
      void runTransition("reject_fulfillment", {
        returnReason: result.reason,
      });
      return;
    }
    void runTransition("cancel", { cancelJustification: result.reason });
  }

  const journey = request?.journey_progress ?? null;
  const trackerSteps = useMemo(
    () => (journey ? mapJourneyStagesToTrackerSteps(journey.stages) : []),
    [journey],
  );
  const capabilities = request?.capabilities ?? null;
  const canEdit = Boolean(request?.allowed_actions?.includes("edit"));
  const requesterAvatarById = useParticipantAvatarUrls([
    request?.created_by_user_id,
  ]);

  return (
    <AppShell title={request ? request.request_number : "Detalhe"}>
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

            {request.return_reason ? (
              <MyRequestsSectionCard
                title="Motivo da devolução"
                hint={MY_REQUESTS_HELP_TOOLTIPS.detail.returnReason}
                className="my-requests-detail-reason"
              >
                <MyRequestsStateBanner variant="error">
                  {request.return_reason}
                </MyRequestsStateBanner>
                {(request.correction_targets || []).length > 0 ? (
                  <div
                    className="my-requests-detail-reason-targets"
                    data-help="correction-targets"
                  >
                    <p className="my-requests-detail-reason-targets__label">
                      Campos a corrigir
                    </p>
                    <ul className="my-requests-detail-reason-targets__list">
                      {correctionTargetLabels(
                        request.type_code,
                        request.correction_targets,
                      ).map((label) => (
                        <li key={label}>
                          <MyRequestsStatusBadge label={label} variant="warning" />
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {canEdit ? (
                  <div className="my-requests-detail-reason-actions">
                    <ActionButton type="button" variant="primary" onClick={openEdit}>
                      Corrigir dados
                    </ActionButton>
                  </div>
                ) : null}
              </MyRequestsSectionCard>
            ) : null}

            {request.cancel_justification ? (
              <MyRequestsSectionCard
                title="Motivo do cancelamento"
                hint={MY_REQUESTS_HELP_TOOLTIPS.detail.cancelReason}
                className="my-requests-detail-reason"
              >
                <MyRequestsStateBanner variant="error">
                  {request.cancel_justification}
                </MyRequestsStateBanner>
              </MyRequestsSectionCard>
            ) : null}

            <section
              className="my-requests-detail-phase"
              aria-labelledby="my-requests-phase-request"
            >
              <h2
                id="my-requests-phase-request"
                className="my-requests-detail-phase-title"
              >
                O que foi solicitado
              </h2>

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
                      value: (
                        <PersonIdentity
                          name={request.created_by_name}
                          userId={request.created_by_user_id}
                          src={
                            requesterAvatarById.get(request.created_by_user_id) ||
                            null
                          }
                        />
                      ),
                    },
                    {
                      label: "Criada em",
                      hint: MY_REQUESTS_HELP_TOOLTIPS.detail.createdAt,
                      value: formatDateTimePtBr(request.created_at),
                    },
                  ]}
                />
              </MyRequestsSectionCard>

              {request.type_code === "invoice-issuance" ? (
                <InvoiceIssuancePayloadPanel payload={request.payload} />
              ) : null}

              <AttachmentsPanel
                requestId={requestId}
                canUpload={capabilities?.can_upload_attachment ?? false}
                refreshKey={timelineEpoch}
              />
            </section>

            <section
              className="my-requests-detail-phase"
              aria-labelledby="my-requests-phase-service"
            >
              <h2
                id="my-requests-phase-service"
                className="my-requests-detail-phase-title"
              >
                Atendimento
              </h2>

              {journey ? (
                <MyRequestsSectionCard
                  title="Progresso do atendimento"
                  hint={MY_REQUESTS_HELP_TOOLTIPS.detail.progress}
                >
                  <div className="my-requests-detail-progress">
                    <MyRequestsProgressTracker
                      steps={trackerSteps}
                      currentStepId={
                        journey.current_stage_id || trackerSteps[0]?.id
                      }
                      density={compactDensity ? "compact" : "default"}
                      compactSummary={journeyTrackerCompactSummary(journey)}
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

              <CommentsPanel
                requestId={requestId}
                canComment={capabilities?.can_comment ?? false}
                conversationFrozen={
                  request.status === "completed" ||
                  request.status === "cancelled" ||
                  request.status === "rejected"
                }
                refreshKey={timelineEpoch}
              />

              <ArtifactsPanel
                requestId={requestId}
                canUpload={capabilities?.can_upload_artifact ?? false}
                refreshKey={timelineEpoch}
                defaultArtifactKind={
                  request.type_code === "invoice-issuance" ? "invoice_pdf" : "generic"
                }
              />
            </section>

            <section
              className="my-requests-detail-phase"
              aria-labelledby="my-requests-phase-history"
            >
              <h2
                id="my-requests-phase-history"
                className="my-requests-detail-phase-title"
              >
                Histórico
              </h2>
              <TimelinePanel requestId={requestId} refreshKey={timelineEpoch} />
            </section>
          </>
        ) : null}
      </div>

      {reasonKind ? (
        <ReasonConfirmModal
          open
          kind={reasonKind}
          busy={busy}
          correctionOptions={
            reasonKind === "return"
              ? correctionTargetOptionsForType(request?.type_code)
              : []
          }
          onClose={() => {
            if (!busy) setReasonKind(null);
          }}
          onConfirm={onReasonConfirm}
        />
      ) : null}
    </AppShell>
  );
}
