/** Verificação oficial TOTVS — apresenta o resultado calculado pelo
 * backend (field_results): anterior × esperado × oficial × resultado.
 * O MFE nunca compara valores localmente. PRC-REF-017 / PRC-REF-020. */

import {
  EngineeringDetailCard,
  EngineeringEmptyState,
  EngineeringSectionCard,
  EngineeringStateBanner,
} from "../../../ui/engineeringUi";
import { EngineeringStatusBadge } from "../../../ui/engineeringUi";
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
  prcFieldLabel,
} from "../prcCopy";

function resultBadge(result: string | undefined) {
  const key = result || "unverifiable";
  return (
    <EngineeringStatusBadge
      label={PRC_RESULT_LABELS[key] || key}
      variant={PRC_RESULT_VARIANTS[key] || "neutral"}
    />
  );
}

function fmtValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (Array.isArray(value)) return `${value.length} item(ns)`;
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

type FieldRow = {
  path: string;
  previous: string;
  expected: string;
  observed: string;
  result: string;
  note?: string;
  highlight: boolean;
};

function toFieldRows(fieldResults: Record<string, PrcFieldResult>): FieldRow[] {
  return Object.entries(fieldResults).map(([path, r]) => {
    const result = r.result || "unverifiable";
    return {
      path,
      previous: fmtValue(r.previous),
      expected: fmtValue(r.expected),
      observed: fmtValue(r.observed),
      result,
      note: r.reason || undefined,
      highlight: result === "mismatched" || result === "unverifiable",
    };
  });
}

const INFRA_RESULTS = new Set([
  "timeout",
  "unavailable",
  "forbidden",
  "contract_error",
]);

export function PrcVerificationPanel({
  detail,
  verifications,
  lastError,
  verifying,
}: {
  detail: PrcRequestDetail;
  verifications: PrcVerification[];
  /** fieldResults do erro 409/422 mais recente (erp_mismatch). */
  lastError?: Record<string, PrcFieldResult> | null;
  /** PRC-REF-020 — estado de processamento da conclusão. */
  verifying?: boolean;
}) {
  const last = verifications.length
    ? verifications[verifications.length - 1]
    : null;
  const fieldResults =
    lastError ||
    (last?.field_results && Object.keys(last.field_results).length
      ? last.field_results
      : null);
  const rows = fieldResults ? toFieldRows(fieldResults) : [];
  const isUpdate = detail.requestType === "update";
  const mismatchCount = rows.filter((r) => r.highlight).length;
  const matchCount = rows.filter((r) => r.result === "matched").length;
  const lastResult = last?.result || detail.verificationSummary?.result || "";
  const isInfraFailure = INFRA_RESULTS.has(lastResult);

  const fieldColumns: DataTableColumn<FieldRow>[] = [
    {
      key: "path",
      header: "Campo",
      render: (r) => (
        <span
          className={
            r.highlight ? "engineering-prc__field-mismatch" : undefined
          }
          id={`prc-verify-field-${r.path}`}
        >
          {prcFieldLabel(r.path)}
        </span>
      ),
      headerHint: "Campo solicitado comparado à leitura oficial TOTVS.",
    },
    ...(isUpdate
      ? [
          {
            key: "previous",
            header: "Anterior",
            render: (r: FieldRow) => r.previous,
          } satisfies DataTableColumn<FieldRow>,
        ]
      : []),
    { key: "expected", header: "Solicitado", render: (r) => r.expected },
    { key: "observed", header: "TOTVS", render: (r) => r.observed },
    {
      key: "result",
      header: "Resultado",
      render: (r) => resultBadge(r.result),
    },
    {
      key: "note",
      header: "Observação",
      render: (r) => r.note || "—",
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

  const supplierDetail =
    fieldResults?.suppliers?.detail &&
    Array.isArray(fieldResults.suppliers.detail)
      ? fieldResults.suppliers.detail
      : [];

  const canComplete =
    detail.status === "in_progress" || detail.status === "under_review";

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

        {last || detail.verificationSummary ? (
          <div className="engineering-prc__verify-summary">
            {resultBadge(
              last?.result || detail.verificationSummary?.result || "",
            )}
            <span>
              Código oficial:{" "}
              <strong>
                {last?.official_product_code ||
                  detail.officialCode ||
                  PRC_COPY.awaitingCode}
              </strong>
            </span>
            <span>
              Verificado em:{" "}
              {new Date(
                last?.checked_at ||
                  detail.verificationSummary?.checkedAt ||
                  "",
              ).toLocaleString("pt-BR")}
            </span>
            {rows.length ? (
              <span>
                Resultado: {matchCount} correspondência(s) / {mismatchCount}{" "}
                problema(s)
              </span>
            ) : null}
          </div>
        ) : (
          <p className="engineering-prc__muted">{PRC_COPY.neverVerified}</p>
        )}
      </EngineeringDetailCard>

      {isInfraFailure ? (
        <EngineeringStateBanner variant="warning">
          {PRC_COPY.officialUnavailable}
        </EngineeringStateBanner>
      ) : null}

      {mismatchCount > 0 ? (
        <EngineeringStateBanner variant="error">
          {PRC_COPY.conclusionBlocked} Foram encontrados {mismatchCount}{" "}
          problema(s). Corrija o cadastro no TOTVS (quando autorizado) ou a
          ficha técnica e use {PRC_COPY.verifyCta} novamente. Nenhuma revisão
          foi publicada.
        </EngineeringStateBanner>
      ) : null}

      {rows.length ? (
        <DataTableSection
          title="Comparação campo a campo"
          hint="Resultado calculado pela Engineering API — o Portal não compara localmente"
          columns={fieldColumns}
          rows={rows}
          rowKey={(r) => r.path}
          hideSearch
          emptyMessage="Sem campos comparados."
          getRowClassName={(r) =>
            r.highlight ? "engineering-prc__row-mismatch" : undefined
          }
        />
      ) : null}

      {supplierDetail.length ? (
        <EngineeringSectionCard
          title="Vínculos de fornecedores (SA5)"
          subtitle="Resultado por vínculo (código + loja) informado pelo backend"
        >
          <ul className="engineering-prc__supplier-diff">
            {supplierDetail.map((d, i) => {
              const bad =
                d.result === "mismatched" || d.result === "unverifiable";
              return (
                <li
                  key={i}
                  className={
                    bad ? "engineering-prc__supplier-mismatch" : undefined
                  }
                  id={`prc-verify-sa5-${String(d.key || i)}`}
                >
                  <strong>
                    Fornecedor {d.key}
                    {d.fields?.length
                      ? ` · ${d.fields
                          .map((f) => prcFieldLabel(`suppliers.${f}`))
                          .join(", ")}`
                      : ""}
                  </strong>{" "}
                  — {PRC_RESULT_LABELS[d.result] || d.result}
                </li>
              );
            })}
          </ul>
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
      ) : !last && !fieldResults ? (
        <EngineeringEmptyState message={PRC_COPY.neverVerified} />
      ) : null}

      {canComplete && !verifications.length && !verifying ? (
        <EngineeringStateBanner>
          Use {PRC_COPY.verifyCta} para validar a ficha contra o cadastro
          oficial em tempo real. A solicitação só será concluída se todos os
          campos verificáveis corresponderem.
        </EngineeringStateBanner>
      ) : null}
    </div>
  );
}
