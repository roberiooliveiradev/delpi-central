/** Verificação oficial TOTVS — apresenta o resultado calculado pelo
 * backend (field_results): esperado × oficial × resultado por campo.
 * O MFE nunca compara valores localmente. */

import { EngineeringDetailCard, EngineeringEmptyState, EngineeringSectionCard, EngineeringStateBanner } from "../../../ui/engineeringUi";
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
  expected: string;
  observed: string;
  result: string;
  note?: string;
};

function toFieldRows(fieldResults: Record<string, PrcFieldResult>): FieldRow[] {
  return Object.entries(fieldResults).map(([path, r]) => ({
    path,
    expected: fmtValue(r.expected),
    observed: fmtValue(r.observed),
    result: r.result || "unverifiable",
    note: r.reason || undefined,
  }));
}

export function PrcVerificationPanel({
  detail,
  verifications,
  lastError,
}: {
  detail: PrcRequestDetail;
  verifications: PrcVerification[];
  /** fieldResults do erro 409/422 mais recente (erp_mismatch). */
  lastError?: Record<string, PrcFieldResult> | null;
}) {
  const last = verifications.length
    ? verifications[verifications.length - 1]
    : null;
  const fieldResults =
    lastError || (last?.field_results && Object.keys(last.field_results).length
      ? last.field_results
      : null);
  const rows = fieldResults ? toFieldRows(fieldResults) : [];

  const fieldColumns: DataTableColumn<FieldRow>[] = [
    {
      key: "path",
      header: "Campo",
      render: (r) => prcFieldLabel(r.path),
    },
    { key: "expected", header: "Esperado", render: (r) => r.expected },
    { key: "observed", header: "Oficial TOTVS", render: (r) => r.observed },
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

  return (
    <div className="engineering-prc__verification">
      <EngineeringDetailCard
        title="Verificação oficial TOTVS"
        hint={`Fonte: Engineering API → api-delpi → TOTVS · ${PRC_COPY.verifyExplain}`}
      >
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
          </div>
        ) : (
          <p className="engineering-prc__muted">{PRC_COPY.neverVerified}</p>
        )}
      </EngineeringDetailCard>

      {rows.length ? (
        <DataTableSection
          title="Comparação campo a campo"
          hint="Resultado calculado pela Engineering API"
          columns={fieldColumns}
          rows={rows}
          rowKey={(r) => r.path}
          hideSearch
          emptyMessage="Sem campos comparados."
        />
      ) : null}

      {supplierDetail.length ? (
        <EngineeringSectionCard
          title="Vínculos de fornecedores"
          subtitle="Resultado por vínculo (código + loja) informado pelo backend"
        >
          <ul className="engineering-prc__supplier-diff">
            {supplierDetail.map((d, i) => (
              <li key={i}>
                <strong>{d.key}</strong> —{" "}
                {PRC_RESULT_LABELS[d.result] || d.result}
                {d.fields?.length ? ` · campos: ${d.fields.join(", ")}` : ""}
              </li>
            ))}
          </ul>
        </EngineeringSectionCard>
      ) : null}

      {verifications.length ? (
        <DataTableSection
          title="Tentativas de verificação"
          columns={attemptColumns}
          rows={verifications}
          rowKey={(v) => v.id}
          hideSearch
          emptyMessage="Sem verificações registradas."
        />
      ) : !last && !fieldResults ? (
        <EngineeringEmptyState message={PRC_COPY.neverVerified} />
      ) : null}

      {detail.status !== "under_review" && !verifications.length ? (
        <EngineeringStateBanner>
          A verificação oficial fica disponível quando a solicitação chega à
          revisão.
        </EngineeringStateBanner>
      ) : null}
    </div>
  );
}
