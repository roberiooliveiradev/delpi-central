import { ExcelExportButton as SharedExcelExportButton } from "@delpi/plugin-ui";

type ExportExcelButtonProps = {
  disabled?: boolean;
  exporting?: boolean;
  onExport: () => void | Promise<void>;
  label?: string;
};

export function ExportExcelButton({
  disabled = false,
  exporting = false,
  onExport,
  label = "Excel",
}: ExportExcelButtonProps) {
  return (
    <SharedExcelExportButton
      disabled={disabled}
      exporting={exporting}
      onExport={onExport}
      className="cr-export-actions"
      buttonClassName="cr-btn cr-btn--secondary"
      label={label}
    />
  );
}
