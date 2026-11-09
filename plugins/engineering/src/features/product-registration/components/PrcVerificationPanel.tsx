/** Verificação oficial TOTVS — tabela única + encaminhamento (PRC-REF-021).
 * O MFE nunca compara valores nem aprova MATCH; só apresenta evidências e
 * registra decisões de encaminhamento autorizadas pelo backend. */

import { useEffect, useMemo, useState } from "react";

import {
  EngineeringActionButton,
  EngineeringEmptyState,
  EngineeringHostDialog,
  EngineeringSegmentToggle,
  EngineeringStateBanner,
  EngineeringStatusBadge,
} from "../../../ui/engineeringUi";
import type { DataTableColumn } from "../../lmps/components/dataTableUi";
import { DataTableSection } from "../../lmps/components/DataTableSection";
import type {
  PrcDivergenceRouting,
  PrcDivergenceRouteDecision,
  PrcFieldResult,
  PrcRequestDetail,
  PrcVerification,
} from "../api/productRegistrationApi";
import {
  newPrcIdempotencyKey,
  routeDivergence,
} from "../api/productRegistrationApi";
import {
  PRC_COPY,
  PRC_RESULT_LABELS,
  PRC_RESULT_VARIANTS,
} from "../prcCopy";
import {
  diagnosisItemRoutingKey,
  formatDiagnosticValue,
  pickActiveFieldResults,
  summarizeDiagnosis,
  technicalTargetElementId,
  type DiagnosisItem,
} from "../prcVerificationDiagnosis";

const ROUTE_OPTIONS: Array<{
  value: PrcDivergenceRouteDecision;
  label: string;
  hint: string;
}> = [
  {
    value: "REQUESTER_CORRECTION",
    label: "Solicitar correção ao solicitante",
    hint:
      "Devolve o campo ao autor para correção ou confirmação. Não é rejeição. A escrita estruturada da ficha pelo solicitante permanece pendente de decisão Core (PENDING_OWNER).",
  },
  {
    value: "ERP_MANUAL_CORRECTION",
    label: "Ajuste manual TOTVS",
    hint:
      "Encaminha correção externa no ERP por operador autorizado. O Portal não escreve no TOTVS; a conclusão exige nova leitura oficial.",
  },
  {
    value: "NEEDS_CLARIFICATION",
    label: "Pedir esclarecimento",
    hint:
      "Registra necessidade de esclarecimento antes de determinar o valor correto. Reutilize as rodadas REF-019 para perguntas e respostas.",
  },
];

const ROUTE_LABELS: Record<PrcDivergenceRouteDecision, string> = {
  REQUESTER_CORRECTION: "Correção ao solicitante",
  ERP_MANUAL_CORRECTION: "Ajuste TOTVS",
  NEEDS_CLARIFICATION: "Esclarecimento",
};

function resultBadge(result: string | undefined) {
  const key = result || "unverifiable";
  return (
    <EngineeringStatusBadge
      label={PRC_RESULT_LABELS[key] || key}
      variant={PRC_RESULT_VARIANTS[key] || "neutral"}
    />
  );
}

function statusHeadline(
  summary: ReturnType<typeof summarizeDiagnosis>,
  requestStatus: string,
): string {
  if (requestStatus === "completed") {
    return "Conclusão publicada";
  }
  if (summary.isInfra) {
    return "Leitura oficial indisponível — conclusão bloqueada";
  }
  if (summary.problems > 0) {
    return `Conclusão bloqueada — ${summary.problems} problema${summary.problems === 1 ? "" : "s"}`;
  }
  if (summary.globalResult === "matched" || summary.totalChecks > 0) {
    return "Verificação sem problemas nesta tentativa";
  }
  return "Aguardando verificação oficial";
}

function latestRoutingForItem(
  item: DiagnosisItem,
  routings: PrcDivergenceRouting[],
  verificationId: string | null | undefined,
): PrcDivergenceRouting | null {
  const key = diagnosisItemRoutingKey(item);
  const matches = routings.filter((r) => {
    if (verificationId && r.verificationId && r.verificationId !== verificationId) {
      return false;
    }
    return r.targetKey === key;
  });
  return matches.length ? matches[matches.length - 1] : null;
}

export type PrcVerificationNavigateTarget = {
  item: DiagnosisItem;
  elementId: string | null;
};

export function PrcVerificationPanel({
  detail,
  verifications,
  routings = [],
  lastError,
  verifying,
  onNavigateToTarget,
  onRetryComplete,
  onRouted,
}: {
  detail: PrcRequestDetail;
  verifications: PrcVerification[];
  routings?: PrcDivergenceRouting[];
  lastError?: Record<string, PrcFieldResult> | null;
  verifying?: boolean;
  onNavigateToTarget?: (target: PrcVerificationNavigateTarget) => void;
  onRetryComplete?: () => void;
  onRouted?: () => void | Promise<void>;
}) {
  const { fieldResults, verification, staleError } = useMemo(
    () =>
      pickActiveFieldResults({
        verifications,
        lastError,
        status: detail.status,
      }),
    [verifications, lastError, detail.status],
  );

  const summary = useMemo(
    () =>
      summarizeDiagnosis({
        fieldResults,
        verification,
        globalResult:
          verification?.result || detail.verificationSummary?.result || null,
        officialCode: detail.officialCode,
      }),
    [fieldResults, verification, detail.officialCode, detail.verificationSummary],
  );

  const [filter, setFilter] = useState<"problems" | "all">("problems");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [routeItem, setRouteItem] = useState<DiagnosisItem | null>(null);
  const [routeDecision, setRouteDecision] =
    useState<PrcDivergenceRouteDecision>("NEEDS_CLARIFICATION");
  const [routeReason, setRouteReason] = useState("");
  const [routeBusy, setRouteBusy] = useState(false);
  const [routeError, setRouteError] = useState<string | null>(null);
  const [routeNotice, setRouteNotice] = useState<string | null>(null);

  useEffect(() => {
    setFilter(summary.problems > 0 ? "problems" : "all");
    setExpandedId(null);
  }, [summary.verificationId, summary.problems, summary.globalResult]);

  const visibleItems =
    filter === "problems" ? summary.problemItems : summary.items;
  const canComplete =
    detail.status === "in_progress" || detail.status === "under_review";
  const canRoute = detail.allowedActions.includes("route_divergence");
  const showBlocked =
    detail.status !== "completed" &&
    !summary.isInfra &&
    summary.problems > 0;

  const expanded = visibleItems.find((i) => i.id === expandedId) || null;

  const columns: DataTableColumn<DiagnosisItem>[] = [
    {
      key: "label",
      header: "Campo",
      render: (r) => (
        <button
          type="button"
          className="engineering-prc__verify-expand"
          aria-expanded={expandedId === r.id}
          id={`prc-verify-item-${r.id}`}
          onClick={() =>
            setExpandedId((cur) => (cur === r.id ? null : r.id))
          }
        >
          <span
            className={
              r.isProblem ? "engineering-prc__field-mismatch" : undefined
            }
          >
            {r.label}
          </span>
        </button>
      ),
    },
    {
      key: "expected",
      header: "Solicitado",
      render: (r) => (
        <span className="engineering-prc__value-cell">
          {formatDiagnosticValue(r.expected)}
        </span>
      ),
    },
    {
      key: "observed",
      header: "TOTVS",
      render: (r) => (
        <span className="engineering-prc__value-cell">
          {formatDiagnosticValue(r.observed)}
        </span>
      ),
    },
    {
      key: "result",
      header: "Situação",
      render: (r) => resultBadge(r.result),
    },
    {
      key: "routing",
      header: "Encaminhamento",
      render: (r) => {
        const existing = latestRoutingForItem(
          r,
          routings,
          summary.verificationId,
        );
        if (existing) {
          return (
            <span className="engineering-prc__route-chip">
              {ROUTE_LABELS[existing.decision] || existing.decision}
            </span>
          );
        }
        if (!r.isProblem || !canRoute || !summary.verificationId) {
          return <span className="engineering-prc__muted">—</span>;
        }
        return (
          <EngineeringActionButton
            variant="ghost"
            onClick={() => {
              setRouteItem(r);
              setRouteDecision("NEEDS_CLARIFICATION");
              setRouteReason("");
              setRouteError(null);
              setRouteNotice(null);
            }}
          >
            Definir
          </EngineeringActionButton>
        );
      },
    },
  ];

  const attemptColumns: DataTableColumn<PrcVerification>[] = [
    {
      key: "checked_at",
      header: "Verificado em",
      render: (v) => new Date(v.checked_at).toLocaleString("pt-BR"),
    },
    {
      key: "official_product_code",
      header: "Código oficial",
      render: (v) => v.official_product_code,
    },
    {
      key: "result",
      header: "Resultado",
      render: (v) => resultBadge(v.result),
    },
    {
      key: "error_code",
      header: "Detalhe",
      render: (v) => v.error_code || "—",
    },
  ];

  const submitRoute = async () => {
    if (!routeItem || !summary.verificationId || routeBusy) return;
    const reason = routeReason.trim();
    if (reason.length < 3) {
      setRouteError("Informe uma justificativa (mín. 3 caracteres).");
      return;
    }
    setRouteBusy(true);
    setRouteError(null);
    setRouteNotice(null);
    try {
      const body = {
        expectedVersion: detail.caseVersion,
        verificationId: summary.verificationId,
        targetType:
          routeItem.kind === "field" ? ("FIELD" as const) : ("SUPPLIER_LINK" as const),
        targetPath:
          routeItem.kind === "field" ? routeItem.path || null : "suppliers",
        supplierKey:
          routeItem.kind === "field"
            ? null
            : {
                supplierCode: routeItem.supplierCode || "",
                store: routeItem.store || "",
              },
        targetAttribute: routeItem.attribute || null,
        decision: routeDecision,
        reason,
      };
      const res = await routeDivergence(
        detail.id,
        body,
        newPrcIdempotencyKey(`prc-route-${detail.id}`),
      );
      const pending = res.data.requesterWrite;
      if (pending?.status === "PENDING_OWNER") {
        setRouteNotice(
          pending.message ||
            "Encaminhamento registrado. Escrita estruturada do solicitante aguarda decisão Core.",
        );
      }
      setRouteItem(null);
      await onRouted?.();
    } catch (e) {
      const err = e as { message?: string };
      setRouteError(err.message || "Falha ao registrar encaminhamento.");
    } finally {
      setRouteBusy(false);
    }
  };

  const hasEvidence = Boolean(verification || fieldResults || verifying);

  return (
    <div className="engineering-prc__verification">
      <header className="engineering-prc__verify-head">
        <div className="engineering-prc__verify-head-main">
          <h2 className="engineering-prc__verify-title">Verificação TOTVS</h2>
          <span className="engineering-prc__verify-meta">
            Produto{" "}
            <strong>{summary.officialCode || PRC_COPY.awaitingCode}</strong>
          </span>
          {summary.checkedAt ? (
            <span className="engineering-prc__verify-meta">
              {new Date(summary.checkedAt).toLocaleString("pt-BR")}
            </span>
          ) : null}
          {summary.globalResult ? resultBadge(summary.globalResult) : null}
        </div>
        <p className="engineering-prc__verify-status-line">
          {statusHeadline(summary, detail.status)}
          {detail.status !== "completed" && !summary.isInfra && summary.totalChecks
            ? ` · Em ${detail.status === "in_progress" ? "atendimento" : detail.status}`
            : null}
        </p>
        {verifying ? (
          <EngineeringStateBanner>
            {PRC_COPY.verifyingNow}
          </EngineeringStateBanner>
        ) : null}
        {summary.isInfra && detail.status !== "completed" ? (
          <EngineeringStateBanner variant="error">
            {summary.globalResult === "not_found"
              ? "Produto não encontrado na fonte oficial. Nenhuma conclusão foi realizada."
              : summary.globalResult === "forbidden"
                ? "Sem permissão para consultar o cadastro oficial. Nenhuma conclusão foi realizada."
                : summary.globalResult === "contract_error"
                  ? "Problema de integração com a fonte oficial. Nenhuma conclusão foi realizada."
                  : PRC_COPY.officialUnavailable}
          </EngineeringStateBanner>
        ) : null}
        {routeNotice ? (
          <EngineeringStateBanner variant="success">{routeNotice}</EngineeringStateBanner>
        ) : null}
        {staleError && detail.status === "completed" ? null : null}
      </header>

      {!hasEvidence ? (
        <EngineeringEmptyState message={PRC_COPY.neverVerified} />
      ) : null}

      {summary.items.length ? (
        <div id="prc-verify-problems" className="engineering-prc__verify-list">
          <div className="engineering-prc__verify-filter">
            <EngineeringSegmentToggle
              ariaLabel="Filtro de resultados da verificação"
              value={filter}
              onChange={setFilter}
              options={[
                {
                  value: "problems",
                  label: `Problemas (${summary.problems})`,
                },
                {
                  value: "all",
                  label: `Todos (${summary.totalChecks})`,
                },
              ]}
            />
          </div>

          <DataTableSection
            title="Comparação SB1 e SA5"
            hint="Resultado oficial da Engineering API — o Portal não compara localmente"
            columns={columns}
            rows={visibleItems}
            rowKey={(r) => r.id}
            hideSearch
            emptyMessage={
              filter === "problems"
                ? "Nenhum problema nesta tentativa."
                : "Sem campos comparados."
            }
            getRowClassName={(r) =>
              [
                r.isProblem ? "engineering-prc__row-mismatch" : "",
                expandedId === r.id ? "engineering-prc__row-expanded" : "",
              ]
                .filter(Boolean)
                .join(" ") || undefined
            }
          />

          {expanded ? (
            <div
              className="engineering-prc__verify-row-detail"
              role="region"
              aria-label={`Detalhe de ${expanded.label}`}
            >
              <p>{expanded.observation}</p>
              <div className="engineering-prc__verify-row-detail-actions">
                {expanded.isProblem ? (
                  <EngineeringActionButton
                    variant="ghost"
                    onClick={() =>
                      onNavigateToTarget?.({
                        item: expanded,
                        elementId: technicalTargetElementId(expanded),
                      })
                    }
                  >
                    {expanded.kind === "field"
                      ? "Ir para ficha técnica"
                      : "Ir para vínculo na ficha"}
                  </EngineeringActionButton>
                ) : null}
                {showBlocked && canComplete && onRetryComplete ? (
                  <EngineeringActionButton
                    variant="ghost"
                    softDisabled={Boolean(verifying)}
                    onClick={onRetryComplete}
                  >
                    Nova tentativa oficial
                  </EngineeringActionButton>
                ) : null}
              </div>
            </div>
          ) : null}
        </div>
      ) : null}

      {verifications.length ? (
        <div className="engineering-prc__verify-history">
          <button
            type="button"
            className="engineering-prc__verify-history-toggle"
            aria-expanded={historyOpen}
            onClick={() => setHistoryOpen((v) => !v)}
          >
            Histórico de tentativas ({verifications.length}){" "}
            {historyOpen ? "▴" : "▾"}
          </button>
          {historyOpen ? (
            <DataTableSection
              title=""
              columns={attemptColumns}
              rows={verifications}
              rowKey={(v) => v.id}
              hideSearch
              emptyMessage="Sem verificações registradas."
            />
          ) : null}
        </div>
      ) : null}

      {canComplete && !verifications.length && !verifying && !showBlocked ? (
        <EngineeringStateBanner>
          Use {PRC_COPY.verifyCta} para validar a ficha contra o cadastro
          oficial em tempo real. A solicitação só será concluída se todos os
          campos verificáveis corresponderem.
        </EngineeringStateBanner>
      ) : null}

      <EngineeringHostDialog
        open={Boolean(routeItem)}
        title="Definir encaminhamento"
        onClose={() => {
          if (!routeBusy) setRouteItem(null);
        }}
        className="engineering-prc-route-dialog"
      >
        {routeItem ? (
          <div className="engineering-prc__route-form">
            <p>
              <strong>{routeItem.label}</strong>
            </p>
            <p className="engineering-prc__muted">
              Solicitado: {formatDiagnosticValue(routeItem.expected)} · TOTVS:{" "}
              {formatDiagnosticValue(routeItem.observed)}
            </p>
            <fieldset className="engineering-prc__route-options">
              <legend>Decisão da Engenharia</legend>
              {ROUTE_OPTIONS.map((opt) => (
                <label key={opt.value} className="engineering-prc__route-option">
                  <input
                    type="radio"
                    name="prc-route-decision"
                    value={opt.value}
                    checked={routeDecision === opt.value}
                    onChange={() => setRouteDecision(opt.value)}
                    disabled={routeBusy}
                  />
                  <span>
                    <strong>{opt.label}</strong>
                    <small>{opt.hint}</small>
                  </span>
                </label>
              ))}
            </fieldset>
            <label className="engineering-prc__route-reason">
              Justificativa
              <textarea
                value={routeReason}
                onChange={(e) => setRouteReason(e.target.value)}
                rows={3}
                maxLength={1000}
                disabled={routeBusy}
                required
              />
            </label>
            {routeError ? (
              <EngineeringStateBanner variant="error">
                {routeError}
              </EngineeringStateBanner>
            ) : null}
            <div className="engineering-prc__route-actions">
              <EngineeringActionButton
                variant="ghost"
                softDisabled={routeBusy}
                onClick={() => setRouteItem(null)}
              >
                Cancelar
              </EngineeringActionButton>
              <EngineeringActionButton
                variant="primary"
                softDisabled={routeBusy}
                onClick={() => void submitRoute()}
              >
                Registrar encaminhamento
              </EngineeringActionButton>
            </div>
          </div>
        ) : null}
      </EngineeringHostDialog>
    </div>
  );
}
