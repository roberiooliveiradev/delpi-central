import { FileSpreadsheet, FileText } from "lucide-react";

type ExportActionsProps = {
  disabled?: boolean;
  exporting?: boolean;
  onExportExcel: () => void | Promise<void>;
  onExportPdf: () => void | Promise<void>;
  className?: string;
  excelLabel?: string;
  pdfLabel?: string;
};

export function ExportActions({
  disabled = false,
  exporting = false,
  onExportExcel,
  onExportPdf,
  className,
  excelLabel = "Excel",
  pdfLabel = "PDF",
}: ExportActionsProps) {
  const isDisabled = disabled || exporting;

  return (
    <div className={`dp-export-actions${className ? ` ${className}` : ""}`}>
      <button
        type="button"
        className="dp-ghost-btn"
        onClick={() => void onExportExcel()}
        disabled={isDisabled}
        aria-busy={exporting}
      >
        <FileSpreadsheet size={16} aria-hidden="true" />
        {exporting ? "Exportando…" : excelLabel}
      </button>
      <button
        type="button"
        className="dp-ghost-btn"
        onClick={() => void onExportPdf()}
        disabled={isDisabled}
        aria-busy={exporting}
      >
        <FileText size={16} aria-hidden="true" />
        {pdfLabel}
      </button>
    </div>
  );
}
