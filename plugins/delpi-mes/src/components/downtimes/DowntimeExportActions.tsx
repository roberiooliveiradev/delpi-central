import { Download, FileSpreadsheet, FileText, ListChecks } from "lucide-react";
import { useState } from "react";

import {
  exportDowntimeExecutiveReport,
  exportDowntimePendencies,
  exportDowntimes,
} from "../../api/mesApi";
import type { DowntimeAnalyticsQuery } from "../../types/mes";
import { triggerBrowserDownload } from "../../utils/downloadFile";

type ExportKind = "csv" | "xlsx" | "pendencies" | "executive";

const EXPORT_LABELS: Record<ExportKind, string> = {
  csv: "CSV",
  xlsx: "Excel",
  pendencies: "Relatório de pendências",
  executive: "PDF executivo",
};

export function DowntimeExportActions({
  query,
  canExport,
}: {
  query: DowntimeAnalyticsQuery;
  canExport: boolean;
}) {
  const [busy, setBusy] = useState<ExportKind | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [capped, setCapped] = useState(false);

  if (!canExport) return null;

  const runExport = async (kind: ExportKind) => {
    setBusy(kind);
    setError(null);
    setCapped(false);
    try {
      const file =
        kind === "executive"
          ? await exportDowntimeExecutiveReport(query)
          : kind === "pendencies"
            ? await exportDowntimePendencies(query, "xlsx")
            : await exportDowntimes(query, kind);
      triggerBrowserDownload(file.blob, file.filename);
      setCapped(file.capped);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível gerar o arquivo.");
    } finally {
      setBusy(null);
    }
  };

  const button = (kind: ExportKind, icon: React.ReactNode) => (
    <button
      type="button"
      className="delpi-mes-refresh-btn"
      onClick={() => void runExport(kind)}
      disabled={busy !== null}
    >
      {icon}
      {busy === kind ? "Gerando…" : EXPORT_LABELS[kind]}
    </button>
  );

  return (
    <div className="delpi-mes-downtimes__export" aria-label="Exportação de paradas">
      <span className="delpi-mes-downtimes__export-title">Exportar:</span>
      {button("csv", <Download aria-hidden="true" />)}
      {button("xlsx", <FileSpreadsheet aria-hidden="true" />)}
      {button("pendencies", <ListChecks aria-hidden="true" />)}
      {button("executive", <FileText aria-hidden="true" />)}
      {error ? (
        <p className="delpi-mes-downtimes__options-warning" role="alert">
          {error}
        </p>
      ) : null}
      {capped ? (
        <p className="delpi-mes-downtimes__options-warning" role="status">
          O arquivo foi gerado parcialmente: o volume excedeu o limite de exportação.
          Refine os filtros para obter o conjunto completo.
        </p>
      ) : null}
    </div>
  );
}
