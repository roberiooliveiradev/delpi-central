import { DocumentExportActions } from "@delpi/plugin-ui";

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
  return (
    <DocumentExportActions
      disabled={disabled}
      exporting={exporting}
      onExportExcel={onExportExcel}
      onExportPdf={onExportPdf}
      className="ef-export-actions"
      buttonClassName="ef-btn ef-btn--ghost"
      excelLabel={excelLabel}
      pdfLabel={pdfLabel}
    />
  );
}
