import { GHOST_BTN } from "../ui/ghostChrome";
import { DocumentExportActions } from "@delpi/plugin-ui/index";

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
      className={`dp-export-actions${className ? ` ${className}` : ""}`}
      buttonClassName={GHOST_BTN}
      excelLabel={excelLabel}
      pdfLabel={pdfLabel}
    />
  );
}
