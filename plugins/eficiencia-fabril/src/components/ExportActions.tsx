import { FileSpreadsheet, FileText } from "lucide-react";

type ExportActionsProps = {
  disabled?: boolean;
  exporting?: boolean;
  onExportExcel: () => void | Promise<void>;
  onExportPdf: () => void | Promise<void>;
  excelLabel?: string;
  pdfLabel?: string;
};

export function ExportActions({
  disabled = false,
  exporting = false,
  onExportExcel,
  onExportPdf,
  excelLabel = "Excel",
  pdfLabel = "PDF",
}: ExportActionsProps) {
  const isDisabled = disabled || exporting;

  return (
    <div className="ef-export-actions">
      <button
        type="button"
        className="ef-btn ef-btn--ghost"
        onClick={() => void onExportExcel()}
        disabled={isDisabled}
        aria-busy={exporting}
      >
        <FileSpreadsheet size={16} aria-hidden />
        {exporting ? "Exportando…" : excelLabel}
      </button>
      <button
        type="button"
        className="ef-btn ef-btn--ghost"
        onClick={() => void onExportPdf()}
        disabled={isDisabled}
        aria-busy={exporting}
      >
        <FileText size={16} aria-hidden />
        {pdfLabel}
      </button>
    </div>
  );
}
