/**
 * Matriz R01–R15 (B-δ) — cobertura de evidências por relatório do
 * processo, derivada do snapshot da competência.
 *
 * Nunca apresenta consulta auxiliar (R01/R02 SE5, R03 SB9) como
 * relatório oficial; R-IDs sem contrato/owner confirmado ficam
 * explicitamente pendentes — a captura é manual governada (P2).
 */
import { useCallback, useEffect, useState } from "react";

import { ApiError } from "../../api/httpClient";
import {
  listReportMatrix,
  type ReportMatrix,
  type ReportSourceKind,
} from "../../api/reportsApi";
import {
  CfQueryErrorBanner,
} from "../../app/cfFeedbackUi";
import {
  CfSectionCard,
  CfStatusBadge,
} from "../../app/controllershipFinanceUi";
import { CF_HELP } from "../../content/helpTooltips";

type PanelError = { status: number; code: string | null; message: string };

const SOURCE_LABELS: Record<ReportSourceKind, string> = {
  OPERATIONAL_VIEW: "Consulta operacional",
  MANUAL_EVIDENCE: "Evidência manual",
  EXTERNAL: "Fonte externa",
  PENDING_CONTRACT: "Contrato pendente",
};

const COVERAGE_LABELS = {
  validated: "Coberto",
  partial: "Parcial",
  pending: "Pendente",
} as const;

const COVERAGE_VARIANTS = {
  validated: "success",
  partial: "info",
  pending: "warning",
} as const;

function mapError(error: unknown): PanelError {
  if (error instanceof ApiError) {
    return {
      status: error.status,
      code: error.code ?? null,
      message: error.message,
    };
  }
  return {
    status: 0,
    code: null,
    message: "Falha de comunicação com a API.",
  };
}

export function ReportsMatrixPanel({ period }: { period: string }) {
  const [matrix, setMatrix] = useState<ReportMatrix | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<PanelError | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setMatrix(await listReportMatrix(period));
    } catch (err) {
      setError(mapError(err));
    } finally {
      setLoading(false);
    }
  }, [period]);

  useEffect(() => {
    void reload();
  }, [reload]);

  if (loading && !matrix) {
    return (
      <CfSectionCard title="Relatórios do processo (R01–R15)">
        <p aria-live="polite">Carregando matriz de relatórios…</p>
      </CfSectionCard>
    );
  }

  if (error && !matrix) {
    return (
      <CfSectionCard title="Relatórios do processo (R01–R15)">
        <CfQueryErrorBanner
          error={error}
          dataset="a matriz de relatórios"
          onRetry={reload}
        />
      </CfSectionCard>
    );
  }

  if (!matrix) return null;

  return (
    <CfSectionCard
      title="Relatórios do processo (R01–R15)"
      hint={CF_HELP.reports.panel}
    >
      <table className="cf-p3-table" aria-label="Matriz R01–R15">
        <thead>
          <tr>
            <th>R-ID</th>
            <th>Relatório</th>
            <th>Fonte</th>
            <th>Itens</th>
            <th>Validados</th>
            <th>Cobertura</th>
          </tr>
        </thead>
        <tbody>
          {matrix.reports.map((entry) => (
            <tr key={entry.report_id}>
              <td>{entry.report_id}</td>
              <td>
                {entry.label}
                {entry.note ? (
                  <span
                    className="cf-p3-cutoff-info"
                    title={entry.note}
                  >
                    {" "}
                    — {entry.note}
                  </span>
                ) : null}
              </td>
              <td>{SOURCE_LABELS[entry.source_kind]}</td>
              <td>{entry.checklist_items || "—"}</td>
              <td>
                {entry.checklist_items
                  ? `${entry.items_validated}/${entry.checklist_items}`
                  : "—"}
              </td>
              <td>
                <CfStatusBadge
                  variant={COVERAGE_VARIANTS[entry.coverage]}
                  label={COVERAGE_LABELS[entry.coverage]}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </CfSectionCard>
  );
}
