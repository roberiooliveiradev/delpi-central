/** Verificação oficial TOTVS — tabela única (PRC-REF-021-REF-01).
 * O MFE nunca compara valores nem aprova MATCH. Sem modal/coluna de
 * encaminhamento: a Engenharia trata divergências pelos fluxos
 * operacionais já existentes (REF-019 / edição / ajuste TOTVS externo). */

import { useEffect, useMemo, useState } from "react";

import {
  EngineeringActionButton,
  EngineeringEmptyState,
  EngineeringSegmentToggle,
  EngineeringStateBanner,
  EngineeringStatusBadge,
} from "../../../ui/engineeringUi";
import type { DataTableColumn } from "../../lmps/components/dataTableUi";
import { DataTableSection } from "../../lmps/components/DataTableSection";
import type {
  PrcFieldResult,
  PrcRequestDetail,
  PrcVerification,
} from "../api/productRegistrationApi";
import {
  PRC_COPY,
  PRC_RESULT_LABELS,
  PRC_RESULT_VARIANTS,
} from "../prcCopy";
import {
  formatDiagnosticValue,
  pickActiveFieldResults,
  summarizeDiagnosis,
  technicalTargetElementId,
  type DiagnosisItem,
} from "../prcVerificationDiagnosis";

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

export type PrcVerificationNavigateTarget = {
  item: DiagnosisItem;
  elementId: string | null;
};

export function PrcVerificationPanel({
  detail,
  verifications,
  lastError,
  verifying,
  onNavigateToTarget,
  onRetryComplete,
}: {
  detail: PrcRequestDetail;
  verifications: PrcVerification[];
  lastError?: Record<string, PrcFieldResult> | null;
  verifying?: boolean;
  onNavigateToTarget?: (target: PrcVerificationNavigateTarget) => void;
  onRetryComplete?: () => void;
}) {
  const { fieldResults, verification } = useMemo(
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

  useEffect(() => {
    setFilter(summary.problems > 0 ? "problems" : "all");
    setExpandedId(null);
  }, [summary.verificationId, summary.problems, summary.globalResult]);

  const visibleItems =
    filter === "problems" ? summary.problemItems : summary.items;
  const canComplete =
    detail.status === "in_progress" || detail.status === "under_review";
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
      key: "actions",
      header: "Ação",
      render: (r) =>
        r.isProblem ? (
          <EngineeringActionButton
            variant="ghost"
            onClick={() =>
              onNavigateToTarget?.({
                item: r,
                elementId: technicalTargetElementId(r),
              })
            }
          >
            Revisar
          </EngineeringActionButton>
        ) : (
          <span className="engineering-prc__muted">—</span>
        ),
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
    </div>
  );
}
