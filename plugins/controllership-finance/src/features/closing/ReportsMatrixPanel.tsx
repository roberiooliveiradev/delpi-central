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
  type ReportMatrixEntry,
  type ReportSourceKind,
} from "../../api/reportsApi";
import {
  CfQueryErrorBanner,
} from "../../app/cfFeedbackUi";
import {
  CfSectionCard,
  CfStatusBadge,
  CfTitleWithHelp,
} from "../../app/controllershipFinanceUi";
import { CF_HELP } from "../../content/helpTooltips";

type PanelError = { status: number; code: string | null; message: string };

export const SOURCE_LABELS: Record<ReportSourceKind, string> = {
  OPERATIONAL_VIEW: "Consulta operacional",
  MANUAL_EVIDENCE: "Evidência manual",
  EXTERNAL: "Fonte externa",
  PENDING_CONTRACT: "Contrato pendente",
};

export const COVERAGE_LABELS = {
  validated: "Coberto",
  partial: "Parcial",
  pending: "Pendente",
} as const;

export const COVERAGE_VARIANTS = {
  validated: "success",
  partial: "info",
  pending: "warning",
} as const;

export const PARITY_LABELS: Record<string, string> = {
  PENDING: "Paridade pendente",
};

/** Tabela R01–R15 — dimensões separadas: disponibilidade da consulta
 *  operacional, paridade oficial e cobertura documental (P2). Nunca
 *  promove consulta implementada a relatório homologado. */
export function ReportsMatrixTable({
  reports,
}: {
  reports: ReportMatrixEntry[];
}) {
  return (
    <table className="cf-p3-table" aria-label="Matriz R01–R15">
      <thead>
        <tr>
          <th>R-ID</th>
          <th>Relatório</th>
          <th>Fonte</th>
          <th>
            <CfTitleWithHelp
              title="Consulta"
              hint={CF_HELP.reports.columns.consulta}
            />
          </th>
          <th>
            <CfTitleWithHelp
              title="Paridade oficial"
              hint={CF_HELP.reports.columns.parity}
            />
          </th>
          <th>Itens</th>
          <th>Validados</th>
          <th>
            <CfTitleWithHelp
              title="Cobertura"
              hint={CF_HELP.reports.columns.coverage}
            />
          </th>
        </tr>
      </thead>
      <tbody>
        {reports.map((entry) => (
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
            <td>
              {entry.operational_view ? (
                <CfStatusBadge variant="info" label="Implementada" />
              ) : (
                "—"
              )}
            </td>
            <td>
              {entry.official_parity ? (
                <CfStatusBadge
                  variant="warning"
                  label={
                    PARITY_LABELS[entry.official_parity] ??
                    entry.official_parity
                  }
                />
              ) : (
                "—"
              )}
            </td>
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
  );
}

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
      <ReportsMatrixTable reports={matrix.reports} />
    </CfSectionCard>
  );
}
