/** Detalhe da solicitação PRC — header com status/ações, andamento do
 * workflow, cards de identificação e abas por URL
 * (Visão geral · Ficha técnica · Verificação TOTVS · Histórico ·
 * Revisões). allowedActions é a única autoridade de ações; CAS via
 * expectedVersion; nenhuma conclusão otimista. */

import { useCallback, useEffect, useMemo, useState } from "react";

import { HomeApiError } from "../../../api/httpClient";
import {
  EngineeringActionButton,
  EngineeringDetailCard,
  EngineeringDetailFieldGrid,
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
  type PrcFieldResult,
  type PrcFieldSpec,
  type PrcRequestDetail,
  type PrcRevisionSummary,
  type PrcTimelineEvent,
  type PrcVerification,
} from "../api/productRegistrationApi";
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
  PRC_TYPE_LABELS,
  prcFieldLabel,
  prcPersonLabel,
  prcRequesterLabel,
  prcShortId,
  prcStatusLabel,
} from "../prcCopy";
import { PrcActionBar } from "../components/PrcActionBar";
import { PRC_ACTION_SPECS } from "../components/prcActionSpecs";
import { PrcRevisionsSection } from "../components/PrcRevisionsSection";
import { PrcStatusBadge } from "../components/PrcStatusBadge";
import { PrcTechnicalSheet } from "../components/PrcTechnicalSheet";
import { PrcTimelineSection } from "../components/PrcTimelineSection";
import { PrcVerificationPanel } from "../components/PrcVerificationPanel";
import { PrcWorkflowProgress } from "../components/PrcWorkflowProgress";

const TABS: { key: PrcTabKey; label: string }[] = [
  { key: "overview", label: "Visão geral" },
  { key: "draft", label: "Ficha técnica" },
  { key: "verification", label: "Verificação TOTVS" },
  { key: "history", label: "Histórico" },
  { key: "revisions", label: "Revisões" },
];

function fmt(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (Array.isArray(value)) return `${value.length} item(ns)`;
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

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
}: {
  requestId: string;
  basePath: string;
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
    kind: "success" | "error";
    text: string;
  } | null>(null);
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState(false);
  const [mismatchFields, setMismatchFields] = useState<Record<
    string,
    PrcFieldResult
  > | null>(null);

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
      extras: { reason?: string; officialCode?: string },
    ) => {
      if (!detail || busy) return;
      setBusy(true);
      setFeedback(null);
      setMismatchFields(null);
      try {
        const res = await prcAction(
          requestId,
          spec.path,
          {
            expectedVersion: detail.caseVersion,
            reason: extras.reason,
            officialCode: extras.officialCode,
          },
          newIdemKey(`prc-${spec.action}-${requestId}`),
        );
        setDetail(res.data);
        setFeedback({ kind: "success", text: "Operação aplicada." });
        await load();
      } catch (e) {
        const err = e as HomeApiError & {
          code?: string;
          data?: { fieldResults?: Record<string, PrcFieldResult> } | null;
        };
        if (err.data?.fieldResults) {
          setMismatchFields(err.data.fieldResults);
        }
        setFeedback({
          kind: "error",
          text:
            err.status === 409
              ? `Conflito — ${err.message} Recarregue e revise o estado atual.`
              : err.message || "Falha na operação.",
        });
        if (err.status === 409 && err.code === "stale_version") {
          await load();
        }
      } finally {
        setBusy(false);
      }
    },
    [detail, busy, requestId, load],
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

  /* Hero: apenas ações sem confirmação/argumentos (start, resume).
   * Ações terminais/com motivo ficam na barra do card — confirmação
   * explícita é obrigatória (verify_and_complete, reject…). */
  const primaryAction = useMemo(() => {
    if (!detail) return null;
    for (const key of ["resume", "start"]) {
      if (detail.allowedActions.includes(key)) return PRC_ACTION_SPECS[key];
    }
    return null;
  }, [detail]);

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

  const identification = [
    {
      label: "Solicitante",
      value: prcRequesterLabel(detail.requester),
    },
    {
      label: "Responsável",
      value: prcPersonLabel(detail.assignedTo),
    },
    {
      label: "Código oficial TOTVS",
      value: detail.officialCode || PRC_COPY.awaitingCode,
    },
    {
      label: "Revisão base",
      value:
        detail.baseRevision != null
          ? `R${detail.baseRevision}`
          : "—",
    },
    {
      label: "Abertura",
      value: new Date(detail.createdAt).toLocaleString("pt-BR"),
    },
    {
      label: "Origem",
      value: detail.source,
    },
  ];

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
        description={`${PRC_TYPE_LABELS[detail.requestType] || detail.requestType} · ${detail.productType === "raw_material" ? "matéria-prima" : detail.productType} · versão ${detail.caseVersion}`}
        badge={<PrcStatusBadge status={detail.status} />}
        actions={
          primaryAction ? (
            <EngineeringActionButton
              variant="primary"
              softDisabled={busy}
              onClick={() => runAction(primaryAction, {})}
            >
              {primaryAction.label}
            </EngineeringActionButton>
          ) : null
        }
      >
        <div className="engineering-prc__hero-meta">
          <EngineeringDetailFieldGrid fields={identification} />
        </div>
        <div className="engineering-prc__hero-progress">
          <PrcWorkflowProgress status={detail.status} />
        </div>
        {detail.allowedActions.length ? (
          <div className="engineering-prc__hero-actions">
            <PrcActionBar
              allowedActions={detail.allowedActions}
              busy={busy}
              officialCode={detail.officialCode || ""}
              requestType={detail.requestType}
              onRunAction={runAction}
              onEditDraft={() => selectTab("draft")}
            />
          </div>
        ) : (
          <p className="engineering-prc__muted">
            Solicitação encerrada — nenhuma ação disponível.
          </p>
        )}
      </EngineeringPageHero>

      {feedback ? (
        <EngineeringStateBanner
          variant={feedback.kind === "error" ? "error" : "success"}
        >
          {feedback.text}
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
      >
        {tab === "overview" ? (
          <div className="engineering-prc__overview">
            <EngineeringDetailCard title="Resumo da solicitação">
              <EngineeringDetailFieldGrid
                fields={[
                  {
                    label: "Tipo",
                    value:
                      PRC_TYPE_LABELS[detail.requestType] ||
                      detail.requestType,
                  },
                  {
                    label: "Status",
                    value: prcStatusLabel(detail.status),
                  },
                  {
                    label: "Última atualização",
                    value: new Date(detail.updatedAt).toLocaleString("pt-BR"),
                  },
                  {
                    label: "Referência externa",
                    value: detail.externalRequestId || "—",
                  },
                  {
                    label: "Verificação oficial",
                    value: detail.verificationSummary
                      ? `${PRC_RESULT_LABELS[detail.verificationSummary.result] || detail.verificationSummary.result} em ${new Date(detail.verificationSummary.checkedAt).toLocaleString("pt-BR")}`
                      : "Nunca verificado",
                  },
                ]}
              />
            </EngineeringDetailCard>

            {detail.requestType === "update" &&
            Object.keys(detail.requestedChanges || {}).length ? (
              <EngineeringDetailCard title="Alterações solicitadas">
                <ul className="engineering-prc__supplier-diff">
                  {(
                    (detail.requestedChanges.changes as Array<{
                      path: string;
                      proposedValue: unknown;
                      reason: string;
                    }>) || []
                  ).map((c, i) => (
                    <li key={i}>
                      <strong>{prcFieldLabel(c.path)}</strong> →{" "}
                      {fmt(c.proposedValue)}
                      {c.reason ? ` — ${c.reason}` : ""}
                    </li>
                  ))}
                </ul>
              </EngineeringDetailCard>
            ) : null}
          </div>
        ) : null}

        {tab === "draft" ? (
          <PrcTechnicalSheet
            detail={detail}
            fieldSpecs={fieldSpecs}
            editablePaths={editablePaths}
            editing={editing}
            busy={busy}
            onStartEdit={() => setEditing(true)}
            onCancelEdit={() => setEditing(false)}
            onSave={saveDraft}
          />
        ) : null}

        {tab === "verification" ? (
          <PrcVerificationPanel
            detail={detail}
            verifications={verifications}
            lastError={mismatchFields}
          />
        ) : null}

        {tab === "history" ? (
          <PrcTimelineSection events={timeline} />
        ) : null}

        {tab === "revisions" ? (
          <PrcRevisionsSection
            recordId={detail.completedRecordId}
            revisions={revisions}
          />
        ) : null}
      </div>
    </main>
  );
}
