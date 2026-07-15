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
  label = "Exportar Excel",
}: ExportExcelButtonProps) {
  return (
    <SharedExcelExportButton
      disabled={disabled}
      exporting={exporting}
      onExport={onExport}
      className="sm-export-actions"
      buttonClassName="sm-btn sm-btn--secondary"
      label={label}
    />
  );
}
