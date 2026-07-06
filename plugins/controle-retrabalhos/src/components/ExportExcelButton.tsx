import { FileSpreadsheet } from "lucide-react";

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
  const isDisabled = disabled || exporting;

  return (
    <div className="cr-export-actions">
      <button
        type="button"
        className="cr-btn cr-btn--secondary"
        onClick={() => void onExport()}
        disabled={isDisabled}
        aria-busy={exporting}
      >
        <FileSpreadsheet size={16} aria-hidden />
        {exporting ? "Exportando…" : label}
      </button>
    </div>
  );
}
