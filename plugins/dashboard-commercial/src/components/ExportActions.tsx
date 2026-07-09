import { DocumentExportActions } from "@delpi/plugin-ui";

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
  return (
    <DocumentExportActions
      disabled={disabled}
      exporting={exporting}
      onExportExcel={onExportExcel}
      onExportPdf={onExportPdf}
      className={`dc-export-actions${className ? ` ${className}` : ""}`}
      buttonClassName="dc-ghost-btn"
      excelLabel={excelLabel}
      pdfLabel={pdfLabel}
    />
  );
}
