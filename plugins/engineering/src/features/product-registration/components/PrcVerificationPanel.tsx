/** Verificação oficial TOTVS — diagnóstico orientado (PRC-REF-020-UX-01).
 * O MFE nunca compara valores; apenas apresenta evidências tipadas. */

import { useEffect, useMemo, useState } from "react";

import {
  EngineeringActionButton,
  EngineeringDetailCard,
  EngineeringEmptyState,
  EngineeringSectionCard,
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
  useEffect(() => {
    setFilter(summary.problems > 0 ? "problems" : "all");
  }, [summary.verificationId, summary.problems, summary.globalResult]);

  const visibleItems =
    filter === "problems" ? summary.problemItems : summary.items;
  const isUpdate = detail.requestType === "update";
  const canComplete =
    detail.status === "in_progress" || detail.status === "under_review";
  const showBlocked =
    detail.status !== "completed" &&
    !summary.isInfra &&
    summary.problems > 0;

  const fieldColumns: DataTableColumn<DiagnosisItem>[] = [
    {
      key: "label",
      header: "Campo",
      render: (r) => (
        <span
          className={r.isProblem ? "engineering-prc__field-mismatch" : undefined}
          id={`prc-verify-item-${r.id}`}
        >
          {r.label}
        </span>
      ),
    },
    ...(isUpdate
      ? [
          {
            key: "previous",
            header: "Anterior",
            render: (r: DiagnosisItem) => formatDiagnosticValue(r.previous),
          } satisfies DataTableColumn<DiagnosisItem>,
        ]
      : []),
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
      header: "Resultado",
      render: (r) => resultBadge(r.result),
    },
    {
      key: "observation",
      header: "Observação",
      render: (r) => r.observation || "—",
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
            {r.kind === "field" ? "Revisar campo" : "Revisar vínculo"}
          </EngineeringActionButton>
        ) : (
          "—"
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

  return (
    <div className="engineering-prc__verification">
      <EngineeringDetailCard
        title="VERIFICAÇÃO OFICIAL"
        hint={`Fonte: Engineering API → api-delpi → TOTVS · ${PRC_COPY.verifyExplain}`}
      >
        {verifying ? (
          <EngineeringStateBanner variant="info">
            {PRC_COPY.verifyingNow}
          </EngineeringStateBanner>
        ) : null}

        {staleError && detail.status === "completed" ? null : null}

        {showBlocked ? (
          <EngineeringStateBanner variant="error">
            <div className="engineering-prc__verify-block-summary">
              <strong>Não foi possível concluir o atendimento.</strong>
              <p>
                {summary.problems} problema
                {summary.problems === 1 ? "" : "s"} encontrado
                {summary.problems === 1 ? "" : "s"} em {summary.totalChecks}{" "}
                verificaç{summary.totalChecks === 1 ? "ão" : "ões"}.
              </p>
              <p>
                {summary.totalChecks} verificaç
                {summary.totalChecks === 1 ? "ão" : "ões"} · {summary.matched}{" "}
                conforme{summary.matched === 1 ? "" : "s"} · {summary.problems}{" "}
                problema{summary.problems === 1 ? "" : "s"}
              </p>
              <p>{PRC_COPY.conclusionBlocked}</p>
              <p>Nenhuma revisão foi publicada.</p>
              <p>
                Produto:{" "}
                <strong>
                  {summary.officialCode || PRC_COPY.awaitingCode}
                </strong>
              </p>
              <p>Fonte: Engineering API → api-delpi → TOTVS</p>
              {summary.checkedAt ? (
                <p>
                  Data e hora da verificação:{" "}
                  {new Date(summary.checkedAt).toLocaleString("pt-BR")}
                </p>
              ) : null}
              <EngineeringActionButton
                variant="ghost"
                onClick={() => {
                  document
                    .getElementById("prc-verify-problems")
                    ?.scrollIntoView({ behavior: "smooth", block: "start" });
                }}
              >
                Ver campos com problemas
              </EngineeringActionButton>
            </div>
          </EngineeringStateBanner>
        ) : null}

        {summary.isInfra && detail.status !== "completed" ? (
          <EngineeringStateBanner variant="warning">
            {summary.globalResult === "not_found"
              ? "O produto informado não foi encontrado na fonte oficial. Nenhuma conclusão foi realizada."
              : summary.globalResult === "forbidden"
                ? "Sem permissão para consultar o cadastro oficial. Nenhuma conclusão foi realizada."
                : summary.globalResult === "contract_error"
                  ? "Problema de integração com a fonte oficial. Nenhuma conclusão foi realizada."
                  : PRC_COPY.officialUnavailable}
          </EngineeringStateBanner>
        ) : null}

        {!showBlocked && !summary.isInfra && (verification || detail.verificationSummary) ? (
          <div className="engineering-prc__verify-summary">
            {resultBadge(summary.globalResult || "")}
            <span>
              Código oficial:{" "}
              <strong>
                {summary.officialCode || PRC_COPY.awaitingCode}
              </strong>
            </span>
            {summary.checkedAt ? (
              <span>
                Verificado em:{" "}
                {new Date(summary.checkedAt).toLocaleString("pt-BR")}
              </span>
            ) : null}
            {summary.totalChecks ? (
              <span>
                {summary.matched} conforme(s) / {summary.problems} problema(s)
              </span>
            ) : null}
          </div>
        ) : null}

        {!verification && !fieldResults && !verifying ? (
          <p className="engineering-prc__muted">{PRC_COPY.neverVerified}</p>
        ) : null}
      </EngineeringDetailCard>

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
                  label: `Somente problemas (${summary.problems})`,
                },
                {
                  value: "all",
                  label: `Todos os campos (${summary.totalChecks})`,
                },
              ]}
            />
          </div>

          <DataTableSection
            title="Comparação campo a campo"
            hint="Resultado calculado pela Engineering API — o Portal não compara localmente"
            columns={fieldColumns}
            rows={visibleItems.filter(
              (i) => i.kind === "field" || i.kind === "supplier_link",
            )}
            rowKey={(r) => r.id}
            hideSearch
            emptyMessage={
              filter === "problems"
                ? "Nenhum problema de campo nesta tentativa."
                : "Sem campos comparados."
            }
            getRowClassName={(r) =>
              r.isProblem ? "engineering-prc__row-mismatch" : undefined
            }
          />

          {visibleItems.some(
            (i) =>
              i.kind === "supplier_attribute" ||
              (i.kind === "supplier_link" && i.isProblem),
          ) ? (
            <EngineeringSectionCard
              title="Vínculos de fornecedores (SA5)"
              subtitle="Diagnóstico por código, loja e atributo — evidência do backend"
            >
              <ul className="engineering-prc__supplier-diff engineering-prc__supplier-diff--detailed">
                {visibleItems
                  .filter(
                    (i) =>
                      i.kind === "supplier_attribute" ||
                      (i.kind === "supplier_link" && i.isProblem),
                  )
                  .map((item) => (
                    <li
                      key={item.id}
                      className={
                        item.isProblem
                          ? "engineering-prc__supplier-mismatch"
                          : undefined
                      }
                      id={`prc-verify-sa5-${item.id}`}
                    >
                      <div>
                        <strong>{item.label}</strong> —{" "}
                        {PRC_RESULT_LABELS[item.result] || item.result}
                      </div>
                      <div>
                        Solicitado: {formatDiagnosticValue(item.expected)}
                      </div>
                      <div>TOTVS: {formatDiagnosticValue(item.observed)}</div>
                      <p>{item.observation}</p>
                      {item.isProblem ? (
                        <EngineeringActionButton
                          variant="ghost"
                          onClick={() =>
                            onNavigateToTarget?.({
                              item,
                              elementId: technicalTargetElementId(item),
                            })
                          }
                        >
                          Revisar vínculo
                        </EngineeringActionButton>
                      ) : null}
                    </li>
                  ))}
              </ul>
            </EngineeringSectionCard>
          ) : null}
        </div>
      ) : null}

      {showBlocked || summary.isInfra ? (
        <EngineeringSectionCard
          title="Próximas ações"
          subtitle="A decisão sobre o valor correto pertence ao processo autorizado de Engenharia"
        >
          <ul className="engineering-prc__next-actions">
            <li>
              <strong>Revisar ficha técnica</strong> — confira ou ajuste o valor
              solicitado quando autorizado.
            </li>
            <li>
              <strong>Solicitar informações</strong> — use esclarecimentos
              (REF-019) quando a definição depender do solicitante.
            </li>
            <li>
              <strong>Corrigir cadastro TOTVS</strong> — apenas pelo procedimento
              manual autorizado; o Portal não escreve no ERP.
            </li>
            <li>
              <strong>Tentar novamente</strong> — nova conclusão com leitura
              oficial fresca.
            </li>
          </ul>
          {canComplete && onRetryComplete ? (
            <EngineeringActionButton
              variant="primary"
              softDisabled={Boolean(verifying)}
              onClick={onRetryComplete}
            >
              {PRC_COPY.verifyCta} novamente
            </EngineeringActionButton>
          ) : null}
        </EngineeringSectionCard>
      ) : null}

      {verifications.length ? (
        <DataTableSection
          title="Histórico de tentativas"
          columns={attemptColumns}
          rows={verifications}
          rowKey={(v) => v.id}
          hideSearch
          emptyMessage="Sem verificações registradas."
        />
      ) : !verification && !fieldResults ? (
        <EngineeringEmptyState message={PRC_COPY.neverVerified} />
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
