import { ExcelExportButton as SharedExcelExportButton } from "@delpi/plugin-ui/index";

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
      className="pa-export-actions"
      buttonClassName="pa-btn pa-btn--secondary"
      label={label}
    />
  );
}
