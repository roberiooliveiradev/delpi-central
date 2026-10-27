import {
  AnchoredPanelPortal,
  HelpTooltip,
} from "@delpi/plugin-ui/index";
import {
  ChevronDown,
  Download,
  FileSpreadsheet,
  FileText,
  ListChecks,
} from "lucide-react";
import { useRef, useState } from "react";

import {
  exportDowntimeExecutiveReport,
  exportDowntimePendencies,
  exportDowntimes,
} from "../../api/mesApi";
import { DELPI_MES_COPY } from "../../content/copy";
import type { DowntimeAnalyticsQuery } from "../../types/mes";
import { triggerBrowserDownload } from "../../utils/downloadFile";

type ExportKind = "csv" | "xlsx" | "pendencies" | "executive";

const EXPORT_LABELS: Record<ExportKind, string> = {
  csv: "CSV",
  xlsx: "Excel",
  pendencies: "Relatório de pendências",
  executive: "PDF executivo",
};

const EXPORT_ITEMS: ReadonlyArray<{ kind: ExportKind; icon: React.ReactNode }> = [
  { kind: "csv", icon: <Download aria-hidden="true" /> },
  { kind: "xlsx", icon: <FileSpreadsheet aria-hidden="true" /> },
  { kind: "pendencies", icon: <ListChecks aria-hidden="true" /> },
  { kind: "executive", icon: <FileText aria-hidden="true" /> },
];

/** Ações de exportação da Gestão de Paradas agrupadas em um único menu
 * (overlay via portal — nunca cortado pelos containers do MFE). A geração
 * continua no backend com os filtros vigentes. */
export function DowntimeExportActions({
  query,
  canExport,
}: {
  query: DowntimeAnalyticsQuery;
  canExport: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState<ExportKind | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [capped, setCapped] = useState(false);
  const anchorRef = useRef<HTMLButtonElement | null>(null);
  const panelRef = useRef<HTMLDivElement | null>(null);

  if (!canExport) return null;

  const runExport = async (kind: ExportKind) => {
    setOpen(false);
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

  return (
    <div className="delpi-mes-downtimes__export">
      <button
        type="button"
        ref={anchorRef}
        className="delpi-mes-refresh-btn"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
        disabled={busy !== null}
      >
        <Download aria-hidden="true" />
        {busy ? "Gerando " + EXPORT_LABELS[busy] + "…" : "Exportar"}
        <ChevronDown aria-hidden="true" data-open={open} className="delpi-mes-downtimes__export-caret" />
      </button>
      <HelpTooltip
        content={DELPI_MES_COPY.help.downtimesExport}
        ariaLabel="Ajuda: exportação de paradas"
      />
      <AnchoredPanelPortal
        open={open}
        anchorRef={anchorRef}
        panelRef={panelRef}
        onDismiss={() => setOpen(false)}
        role="menu"
        aria-label="Formatos de exportação"
        variant="bare"
        preferredPlacement="bottom"
        horizontalAlign="end"
        className="delpi-mes-downtimes__export-menu"
      >
        {EXPORT_ITEMS.map(({ kind, icon }) => (
          <button
            key={kind}
            type="button"
            role="menuitem"
            onClick={() => void runExport(kind)}
            disabled={busy !== null}
          >
            {icon}
            {busy === kind ? "Gerando…" : EXPORT_LABELS[kind]}
          </button>
        ))}
      </AnchoredPanelPortal>
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
