/** Detalhe da solicitação PRC — header com status/ações, andamento do
 * workflow, cards de identificação e abas por URL
 * (Ficha técnica · Verificação TOTVS · Histórico · Revisões).
 * allowedActions é a única autoridade de ações; CAS via
 * expectedVersion; nenhuma conclusão otimista. */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { HomeApiError } from "../../../api/httpClient";
import { usePrcCaseSync } from "../../../app/EngineeringRealtimeProvider";
import { getSubjectFromAccessToken } from "../../../app/authDisplayName";
import { Info, TriangleAlert } from "lucide-react";
import {
  ENGINEERING_PORTAL_SCOPE,
  EngineeringActionButton,
  EngineeringAnchoredPanel,
  EngineeringLoadingActivityCard,
  EngineeringPageHero,
  EngineeringPagePath,
  EngineeringStateBanner,
  EngineeringTabs,
} from "../../../ui/engineeringUi";
import {
  fetchPrcReferenceData,
  fetchPrcRequest,
  fetchPrcRevisions,
  fetchPrcTimeline,
  fetchPrcVerifications,
  prcAction,
  prcUpdateDraft,
  prcUpdateReturnedFields,
  type PrcFieldResult,
  type PrcReturnedFieldChange,
  type PrcFieldSpec,
  type PrcRequestDetail,
  type PrcRevisionSummary,
  type PrcTimelineEvent,
  type PrcVerification,
} from "../api/productRegistrationApi";
import {
  mapApiFieldsToCorrectionErrors,
  type PrcCorrectionTargetErrors,
} from "@delpi/plugin-ui/index";
import {
  buildPrcQueueUrl,
  EMPTY_PRC_QUEUE_URL,
  navigatePrcHref,
  parsePrcTab,
  prcDetailTabHref,
  useLocationSearch,
  type PrcTabKey,
} from "../prcNavigate";
import {
  PRC_COPY,
  PRC_RESULT_LABELS,
  PRC_RESULT_VARIANTS,
  PRC_TYPE_LABELS,
  prcPersonLabel,
  prcRequesterLabel,
  prcShortId,
  prcSourceLabel,
} from "../prcCopy";
import { PrcActionBar } from "../components/PrcActionBar";
import { PrcAttachmentsSection } from "../components/PrcAttachmentsSection";
import {
  PRC_ACTION_SPECS,
  isPrcCompleteAction,
  type PrcActionExtras,
} from "../components/prcActionSpecs";
import { PrcInformationExchangePanel } from "../components/PrcInformationExchangePanel";
import { PrcPersonCell } from "../components/PrcPersonCell";
import { supplierOptionsFromTechnicalDraft } from "../prcInformationExchange";
import { PrcRevisionsSection } from "../components/PrcRevisionsSection";
import { PrcStatusBadge } from "../components/PrcStatusBadge";
import { PrcTechnicalSheet } from "../components/PrcTechnicalSheet";
import { PrcTimelineSection } from "../components/PrcTimelineSection";
import { PrcVerificationPanel } from "../components/PrcVerificationPanel";
import { PrcWorkflowProgress } from "../components/PrcWorkflowProgress";
import { summarizeDiagnosis } from "../prcVerificationDiagnosis";

const TABS: { key: PrcTabKey; label: string }[] = [
  { key: "draft", label: "Ficha técnica" },
  { key: "verification", label: "Verificação TOTVS" },
  { key: "history", label: "Histórico" },
  { key: "revisions", label: "Revisões" },
];

function newIdemKey(prefix: string): string {
  const uuid =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  return `${prefix}-${uuid}`;
}

export function PrcDetailPage({
  requestId,
  basePath,
  getAccessToken,
}: {
  requestId: string;
  basePath: string;
  /** Getter do host — usado só para escolher a visão solicitante/analista. */
  getAccessToken?: () => string | undefined;
}) {
  const locationSearch = useLocationSearch();
  const tab = parsePrcTab(locationSearch);

  const [detail, setDetail] = useState<PrcRequestDetail | null>(null);
  const [timeline, setTimeline] = useState<PrcTimelineEvent[]>([]);
  const [verifications, setVerifications] = useState<PrcVerification[]>([]);
  const [revisions, setRevisions] = useState<PrcRevisionSummary[]>([]);
  const [fieldSpecs, setFieldSpecs] = useState<PrcFieldSpec[] | null>(null);
  const [editablePaths, setEditablePaths] = useState<string[] | null>(null);
  const [state, setState] = useState<"loading" | "ok" | "error" | "forbidden">(
    "loading",
  );
  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState<{
    kind: "success" | "error" | "blocked";
    text: string;
    problemCount?: number;
  } | null>(null);
  const [busy, setBusy] = useState(false);
  const [verifying, setVerifying] = useState(false);
  /* FIX-12 — erros de campo do PATCH /returned-fields contextualizados
   * no editor compartilhado. */
  const [correctionFieldErrors, setCorrectionFieldErrors] =
    useState<PrcCorrectionTargetErrors>({});
  const [editing, setEditing] = useState(false);
  const [mismatchFields, setMismatchFields] = useState<Record<
    string,
    PrcFieldResult
  > | null>(null);
  const [focusTarget, setFocusTarget] = useState<{
    elementId: string;
    nonce: number;
  } | null>(null);
  const [navFallback, setNavFallback] = useState<string | null>(null);
  /* UX V3 — metadados de auditoria em popover ancorado (sem grade de
   * nove campos no hero). */
  const [infoOpen, setInfoOpen] = useState(false);
  const infoAnchorRef = useRef<HTMLElement>(null);
  const infoPanelRef = useRef<HTMLDivElement>(null);
  /* Alvo estável para "reexecutar conclusão" — substitui o antigo
   * querySelector('.engineering-prc__hero-actions'). */
  const actionsRef = useRef<HTMLDivElement>(null);

  const load = useCallback(async () => {
    try {
      const [d, t, v, ref] = await Promise.all([
        fetchPrcRequest(requestId),
        fetchPrcTimeline(requestId),
        fetchPrcVerifications(requestId),
        fetchPrcReferenceData(),
      ]);
      setDetail(d.data);
      setTimeline(t.data.items);
      setVerifications(v.data.items);
      setFieldSpecs(ref.data.fields);
      setEditablePaths(ref.data.editableDraftPaths);
      if (d.data.status === "completed") {
        setMismatchFields(null);
        setFeedback((prev) =>
          prev?.kind === "blocked" ? null : prev,
        );
      }
      if (d.data.completedRecordId) {
        try {
          const rec = await fetchPrcRevisions(d.data.completedRecordId);
          setRevisions(rec.data.items);
        } catch {
          setRevisions([]);
        }
      } else {
        setRevisions([]);
      }
      setState("ok");
    } catch (e) {
      const err = e as HomeApiError;
      setError(err.message || "Falha ao carregar a solicitação.");
      setState(err.status === 403 ? "forbidden" : "error");
    }
  }, [requestId]);

  useEffect(() => {
    setState("loading");
    void load();
  }, [load]);

  /* ENG-REALTIME-01 — evento do próprio caso invalida e refaz o
   * refetch HTTP oficial. Enquanto `editing`, o refetch é adiado para
   * não sobrescrever o rascunho; ao sair da edição, recarrega. */
  const editingRef = useRef(editing);
  const [remoteChanged, setRemoteChanged] = useState(false);
  useEffect(() => {
    editingRef.current = editing;
  }, [editing]);
  usePrcCaseSync(
    requestId,
    useCallback(() => {
      if (editingRef.current) {
        setRemoteChanged(true);
        return;
      }
      void load();
    }, [load]),
  );
  useEffect(() => {
    if (!editing && remoteChanged) {
      setRemoteChanged(false);
      void load();
    }
  }, [editing, remoteChanged, load]);

  /* `?tab=` inválido → normaliza sem poluir o histórico. */
  useEffect(() => {
    const raw = new URLSearchParams(locationSearch).get("tab");
    if (raw && raw !== tab) {
      navigatePrcHref(prcDetailTabHref(basePath, requestId, tab), {
        replace: true,
      });
    }
  }, [locationSearch, tab, basePath, requestId]);

  const selectTab = useCallback(
    (key: PrcTabKey) => {
      if (key === tab) return;
      navigatePrcHref(prcDetailTabHref(basePath, requestId, key));
    },
    [tab, basePath, requestId],
  );

  const runAction = useCallback(
    async (
      spec: { action: string; path: string },
      extras: PrcActionExtras,
    ) => {
      if (!detail || busy) return;
      const isComplete = isPrcCompleteAction(spec.action);
      setBusy(true);
      setVerifying(isComplete);
      setFeedback(null);
      setMismatchFields(null);
      if (isComplete) {
        selectTab("verification");
        setFeedback({
          kind: "success",
          text: PRC_COPY.verifyingNow,
        });
      }
      try {
        const res = await prcAction(
          requestId,
          spec.path,
          {
            expectedVersion: detail.caseVersion,
            reason: extras.reason,
            officialCode: extras.officialCode,
            ...(extras.questions ? { questions: extras.questions } : {}),
            ...(extras.message ? { message: extras.message } : {}),
            ...(extras.pendingFields?.length
              ? { pendingFields: extras.pendingFields }
              : {}),
            ...(extras.targets?.length ? { targets: extras.targets } : {}),
          },
          newIdemKey(`prc-${spec.action}-${requestId}`),
        );
        setDetail(res.data);
        setEditing(false);
        setFeedback({
          kind: "success",
          text: isComplete
            ? "Atendimento concluído com verificação oficial."
            : spec.action === "return_for_correction"
              ? "Solicitação devolvida para correção."
              : spec.action === "resubmit_correction"
                ? "Correções reenviadas à Engenharia."
                : "Operação aplicada.",
        });
        await load();
      } catch (e) {
        const err = e as HomeApiError & {
          code?: string;
          data?: {
            code?: string;
            fieldResults?: Record<string, PrcFieldResult>;
          } | null;
        };
        if (err.data?.fieldResults) {
          setMismatchFields(err.data.fieldResults);
          selectTab("verification");
        }
        {
          const raw = err.message || "";
          const code = err.data?.code || "";
          const isInfoRound =
            err.status === 409 && /information_round_open/i.test(raw);
          const isOfficialTimeout =
            code === "official_timeout" || err.status === 504;
          const isOfficialUnavailable =
            code === "official_unavailable" || err.status === 503;
          const diagnosis = summarizeDiagnosis({
            fieldResults: err.data?.fieldResults || null,
            globalResult: code || null,
          });
          let text: string;
          let kind: "success" | "error" | "blocked" = "error";
          let problemCount: number | undefined;
          if (isInfoRound) {
            text =
              "Este atendimento ainda possui esclarecimentos pendentes. Aguarde as respostas e conclua a análise antes de retomar.";
          } else if (isOfficialTimeout || isOfficialUnavailable) {
            text = PRC_COPY.officialUnavailable;
          } else if (diagnosis.problems > 0 && !diagnosis.isInfra) {
            kind = "blocked";
            problemCount = diagnosis.problems;
            text = `Conclusão bloqueada — ver ${diagnosis.problems} problema${diagnosis.problems === 1 ? "" : "s"}`;
          } else if (err.status === 409) {
            text = `Conflito — ${raw} Recarregue e revise o estado atual.`;
          } else {
            text = raw || "Falha na operação.";
          }
          setFeedback({ kind, text, problemCount });
        }
        if (
          err.status === 409 ||
          err.status === 422 ||
          err.status === 503 ||
          err.status === 504
        ) {
          await load();
        }
      } finally {
        setBusy(false);
        setVerifying(false);
      }
    },
    [detail, busy, requestId, load, selectTab],
  );

  const saveDraft = useCallback(
    async (
      changes: Array<{ path: string; proposedValue: unknown; reason: string }>,
    ) => {
      if (!detail || busy) return;
      setBusy(true);
      setFeedback(null);
      try {
        const res = await prcUpdateDraft(
          requestId,
          { expectedVersion: detail.caseVersion, changes },
          newIdemKey(`prc-draft-${requestId}`),
        );
        setDetail(res.data);
        setEditing(false);
        setFeedback({ kind: "success", text: "Ficha técnica atualizada." });
        await load();
      } catch (e) {
        const err = e as HomeApiError;
        setFeedback({
          kind: "error",
          text:
            err.status === 409
              ? `Conflito de versão — os dados foram recarregados. ${err.message || ""}`
              : err.message || "Falha ao salvar a ficha.",
        });
        if (err.status === 409) await load();
      } finally {
        setBusy(false);
      }
    },
    [detail, busy, requestId, load],
  );

  const saveReturnedFields = useCallback(
    async (changes: PrcReturnedFieldChange[]) => {
      if (!detail || busy) return;
      setBusy(true);
      setFeedback(null);
      setCorrectionFieldErrors({});
      try {
        const res = await prcUpdateReturnedFields(
          requestId,
          { expectedVersion: detail.caseVersion, changes },
          newIdemKey(`prc-returned-${requestId}`),
        );
        setDetail(res.data);
        setFeedback({
          kind: "success",
          text: "Campos devolvidos atualizados.",
        });
        await load();
      } catch (e) {
        const err = e as HomeApiError;
        /* FIX-12/AC-09 — fields identificáveis do contrato viram
         * erro contextual no editor; o restante permanece global. */
        const { targetErrors } = mapApiFieldsToCorrectionErrors(
          (err as { fields?: Record<string, string> }).fields,
          changes,
        );
        setCorrectionFieldErrors(targetErrors);
        setFeedback({
          kind: "error",
          text:
            err.status === 409
              ? `Conflito de versão — os dados foram recarregados. ${err.message || ""}`
              : err.message || "Falha ao salvar a correção.",
        });
        if (err.status === 409) await load();
      } finally {
        setBusy(false);
      }
    },
    [detail, busy, requestId, load],
  );

  /* Hero: apenas ações sem confirmação/argumentos (start, resume). */
  const primaryAction = useMemo(() => {
    if (!detail) return null;
    for (const key of ["resume", "start"]) {
      if (detail.allowedActions.includes(key)) return PRC_ACTION_SPECS[key];
    }
    return null;
  }, [detail]);

  const infoSuppliers = useMemo(
    () => supplierOptionsFromTechnicalDraft(detail?.technicalDraft),
    [detail?.technicalDraft],
  );
  const currentSubject = getSubjectFromAccessToken(getAccessToken?.());

  const backToQueue = useCallback(() => {
    navigatePrcHref(buildPrcQueueUrl(basePath, EMPTY_PRC_QUEUE_URL));
  }, [basePath]);

  if (state === "loading") {
    return (
      <main className="engineering-prc">
        <EngineeringLoadingActivityCard
          title="Carregando solicitação"
          description="Consultando a Engineering API."
        />
      </main>
    );
  }

  if (state === "forbidden") {
    return (
      <main className="engineering-prc">
        <EngineeringStateBanner variant="error">
          Esta solicitação está fora do seu escopo de acesso.
        </EngineeringStateBanner>
        <EngineeringActionButton variant="primary" onClick={backToQueue}>
          Voltar para a fila
        </EngineeringActionButton>
      </main>
    );
  }

  if (state === "error" || !detail) {
    return (
      <main className="engineering-prc">
        <EngineeringStateBanner variant="error">
          {error || "Solicitação não encontrada."}
        </EngineeringStateBanner>
        <EngineeringActionButton
          variant="primary"
          onClick={() => {
            setState("loading");
            void load();
          }}
        >
          Tentar novamente
        </EngineeringActionButton>
        <EngineeringActionButton variant="ghost" onClick={backToQueue}>
          Voltar para a fila
        </EngineeringActionButton>
      </main>
    );
  }

  /* UX V3 — hero = identidade + estado + próxima ação. Metadados de
   * auditoria/proveniência ficam no popover «Informações»; código
   * oficial na Ficha técnica; verificação na aba dedicada. */
  const productTypeLabel =
    detail.productType === "raw_material"
      ? "matéria-prima"
      : detail.productType;
  const verificationResult = detail.verificationSummary?.result || null;
  const verificationBlocking = verificationResult
    ? PRC_RESULT_VARIANTS[verificationResult] === "danger"
    : false;

  return (
    <main className="engineering-prc">
      <EngineeringPagePath
        back={{
          label: PRC_COPY.detailBreadcrumb,
          href: `${basePath}/${"product-registration"}`,
          onNavigate: (event) => {
            event.preventDefault();
            backToQueue();
          },
        }}
        items={[]}
        current={prcShortId(detail.id)}
      />

      <EngineeringPageHero
        eyebrow={PRC_COPY.breadcrumbRoot}
        title={`Solicitação ${prcShortId(detail.id)}`}
        description={`${PRC_TYPE_LABELS[detail.requestType] || detail.requestType} de ${productTypeLabel}`}
        badge={<PrcStatusBadge status={detail.status} />}
        actions={
          primaryAction ? (
            <EngineeringActionButton
              variant="primary"
              title={primaryAction.help}
              softDisabled={busy}
              onClick={() => runAction(primaryAction, {})}
            >
              {primaryAction.icon ? (
                <primaryAction.icon size={14} aria-hidden />
              ) : null}
              {primaryAction.label}
            </EngineeringActionButton>
          ) : null
        }
      >
        <div className="engineering-prc__hero-identity">
          <div className="engineering-prc__hero-people">
            <div className="engineering-prc__hero-person">
              <span className="engineering-prc__hero-person-label">
                Solicitante
              </span>
              <PrcPersonCell
                subject={detail.requester.subject}
                displayName={detail.requester.displayName}
              />
            </div>
            {detail.assignedTo ? (
              <div className="engineering-prc__hero-person">
                <span className="engineering-prc__hero-person-label">
                  Responsável
                </span>
                <PrcPersonCell
                  subject={detail.assignedTo}
                  displayName={detail.assignedToDisplayName}
                />
              </div>
            ) : null}
          </div>
          <div className="engineering-prc__hero-meta-controls">
            {/* §56 — revisão só é exibida quando a conclusão desta
                solicitação efetivamente a publicou; nunca Vn alheia. */}
            {detail.status === "completed" ? (
              detail.publishedRevision ? (
                <button
                  type="button"
                  className="engineering-prc__hero-chip engineering-prc__hero-chip--link"
                  title="Revisão técnica publicada por esta solicitação"
                  onClick={() => selectTab("revisions")}
                >
                  Revisão técnica gerada: V
                  {detail.publishedRevision.revisionNumber}
                </button>
              ) : (
                <span
                  className="engineering-prc__hero-chip"
                  title="Conclusão sem diferença técnica — nenhuma revisão nova publicada"
                >
                  Concluída sem nova revisão técnica
                </span>
              )
            ) : null}
            <span
              ref={infoAnchorRef}
              className="engineering-prc__info-anchor"
            >
              <EngineeringActionButton
                variant="ghost"
                aria-expanded={infoOpen}
                aria-controls="prc-info-popover"
                onClick={() => setInfoOpen((v) => !v)}
              >
                <Info size={14} aria-hidden /> Informações
              </EngineeringActionButton>
            </span>
          </div>
        </div>
        {infoOpen ? (
          <EngineeringAnchoredPanel
            open={infoOpen}
            anchorRef={infoAnchorRef}
            panelRef={infoPanelRef}
            variant="bare"
            className="engineering-prc__info-pop"
            role="dialog"
            aria-label="Informações da solicitação"
            portalScopeClassName={ENGINEERING_PORTAL_SCOPE}
            preferredPlacement="bottom"
            horizontalAlign="end"
            gap={6}
            onDismiss={() => setInfoOpen(false)}
          >
            <dl className="engineering-prc__info-list">
              <div className="engineering-prc__info-row">
                <dt>Solicitante</dt>
                <dd>{prcRequesterLabel(detail.requester)}</dd>
              </div>
              <div className="engineering-prc__info-row">
                <dt>Responsável</dt>
                <dd>
                  {detail.assignedTo
                    ? prcPersonLabel(
                        detail.assignedTo,
                        detail.assignedToDisplayName,
                      )
                    : PRC_COPY.unassigned}
                </dd>
              </div>
              <div className="engineering-prc__info-row">
                <dt>Abertura</dt>
                <dd>{new Date(detail.createdAt).toLocaleString("pt-BR")}</dd>
              </div>
              <div className="engineering-prc__info-row">
                <dt>Última atualização</dt>
                <dd>{new Date(detail.updatedAt).toLocaleString("pt-BR")}</dd>
              </div>
              <div className="engineering-prc__info-row">
                <dt>Canal</dt>
                <dd>{prcSourceLabel(detail.source)}</dd>
              </div>
              <div className="engineering-prc__info-row">
                <dt>Identificador no canal de origem</dt>
                <dd>{detail.externalRequestId || "—"}</dd>
              </div>
              <div className="engineering-prc__info-row">
                <dt>Versão interna do atendimento</dt>
                <dd>{detail.caseVersion}</dd>
              </div>
            </dl>
            {detail.externalRequestId ? (
              <p className="engineering-prc__info-hint">
                Código usado para rastrear a solicitação no sistema de
                origem — não corresponde necessariamente ao número interno
                do caso.
              </p>
            ) : null}
          </EngineeringAnchoredPanel>
        ) : null}
        <div className="engineering-prc__hero-progress">
          <PrcWorkflowProgress status={detail.status} />
        </div>
        {detail.allowedActions.length ? (
          <div className="engineering-prc__hero-actions" ref={actionsRef}>
            <PrcActionBar
              /* start/resume já saem no `actions` do hero — uma ação principal. */
              allowedActions={detail.allowedActions.filter(
                (action) => action !== "resume" && action !== "start",
              )}
              busy={busy}
              officialCode={detail.officialCode || ""}
              requestType={detail.requestType}
              requesterLabel={prcRequesterLabel(detail.requester)}
              fieldSpecs={fieldSpecs}
              suppliers={infoSuppliers}
              draft={detail.technicalDraft}
              onRunAction={runAction}
              onEditDraft={() => {
                selectTab("draft");
                setEditing(true);
              }}
            />
          </div>
        ) : (
          <p className="engineering-prc__muted">
            Solicitação encerrada — nenhuma ação disponível.
          </p>
        )}
        {verificationBlocking ? (
          <div
            className="engineering-prc__verify-alert"
            role="status"
          >
            <TriangleAlert size={14} aria-hidden />
            <span>
              Verificação oficial:{" "}
              {PRC_RESULT_LABELS[verificationResult!] || verificationResult}
            </span>
            <EngineeringActionButton
              variant="ghost"
              onClick={() => selectTab("verification")}
            >
              Ver diagnóstico
            </EngineeringActionButton>
          </div>
        ) : null}
      </EngineeringPageHero>

      {detail.status === "needs_correction" &&
      detail.correctionExchange?.openReturn ? (
        <EngineeringStateBanner variant="error">
          Devolvida para correção — a Engenharia pediu ajuste em{" "}
          {detail.correctionExchange.openReturn.targets?.length || 0} campo(s).
          Corrija diretamente na ficha técnica.
        </EngineeringStateBanner>
      ) : null}
      {detail.status === "in_progress" &&
      detail.correctionExchange?.lastResubmitted ? (
        <EngineeringStateBanner variant="success">
          Correções recebidas do solicitante — revise a ficha e continue o
          atendimento.
        </EngineeringStateBanner>
      ) : null}
      {remoteChanged && editing ? (
        <EngineeringStateBanner>
          {PRC_COPY.remoteUpdatePending}
        </EngineeringStateBanner>
      ) : null}

      {feedback && feedback.kind === "blocked" && tab !== "verification" ? (
        <EngineeringStateBanner variant="error">
          <div className="engineering-prc__compact-block">
            <span>{feedback.text}</span>
            <EngineeringActionButton
              variant="ghost"
              onClick={() => selectTab("verification")}
            >
              Abrir diagnóstico
            </EngineeringActionButton>
          </div>
        </EngineeringStateBanner>
      ) : null}
      {feedback && feedback.kind !== "blocked" ? (
        <EngineeringStateBanner
          variant={feedback.kind === "error" ? "error" : "success"}
        >
          {feedback.text}
        </EngineeringStateBanner>
      ) : null}
      {navFallback ? (
        <EngineeringStateBanner variant="error">
          {navFallback}
        </EngineeringStateBanner>
      ) : null}

      <EngineeringTabs
        mode="tabs"
        aria-label="Seções da solicitação"
        activeId={tab}
        items={TABS.map((t) => ({
          id: t.key,
          label: t.label,
          controlId: `prc-panel-${t.key}`,
          tabId: `prc-tab-${t.key}`,
          onSelect: () => selectTab(t.key),
        }))}
      />

      <div
        role="tabpanel"
        id={`prc-panel-${tab}`}
        aria-labelledby={`prc-tab-${tab}`}
        className="engineering-prc__tabpanel"
      >
        {tab === "draft" ? (
          <>
            <PrcTechnicalSheet
              detail={detail}
              fieldSpecs={fieldSpecs}
              editablePaths={editablePaths}
              editing={editing}
              busy={busy}
              focusElementId={focusTarget?.elementId || null}
              focusNonce={focusTarget?.nonce || 0}
              onStartEdit={() => setEditing(true)}
              onCancelEdit={() => setEditing(false)}
              onSave={saveDraft}
              onSaveReturned={saveReturnedFields}
              correctionFieldErrors={correctionFieldErrors}
            />
            <PrcAttachmentsSection
              requestId={detail.id}
              refreshToken={`${detail.caseVersion}:${detail.updatedAt}`}
            />
          </>
        ) : null}

        {tab === "verification" ? (
          <PrcVerificationPanel
            detail={detail}
            verifications={verifications}
            lastError={mismatchFields}
            verifying={verifying}
            onNavigateToTarget={({ item, elementId }) => {
              setNavFallback(null);
              if (!elementId) {
                setNavFallback(
                  `Não foi possível localizar o alvo «${item.label}» na ficha técnica.`,
                );
                return;
              }
              setFocusTarget({ elementId, nonce: Date.now() });
              selectTab("draft");
            }}
            onRetryComplete={() => {
              actionsRef.current?.scrollIntoView({
                behavior: "smooth",
                block: "center",
              });
              setFeedback({
                kind: "success",
                text:
                  "Use Concluir atendimento no cabeçalho para uma nova verificação oficial (leitura fresca).",
              });
            }}
          />
        ) : null}

        {tab === "history" ? (
          <>
            <PrcInformationExchangePanel
              requestId={detail.id}
              requestStatus={detail.status}
              requesterSubject={detail.requester.subject}
              currentSubject={currentSubject}
              informationExchange={detail.informationExchange}
              allowedActions={detail.allowedActions}
              refreshToken={`${detail.caseVersion}:${detail.updatedAt}`}
              busy={busy}
              onChanged={load}
            />
            <PrcTimelineSection events={timeline} />
          </>
        ) : null}

        {tab === "revisions" ? (
          <PrcRevisionsSection
            recordId={detail.completedRecordId}
            revisions={revisions}
            basePath={basePath}
          />
        ) : null}
      </div>
    </main>
  );
}
