import { Printer } from "lucide-react";

type PrintReportButtonProps = {
  disabled?: boolean;
  label?: string;
};

export function PrintReportButton({
  disabled = false,
  label = "Imprimir",
}: PrintReportButtonProps) {
  return (
    <button
      type="button"
      className="dq-ghost-btn dq-no-print"
      onClick={() => window.print()}
      disabled={disabled}
      aria-label="Imprimir relatório da página"
    >
      <Printer size={16} aria-hidden />
      <span>{label}</span>
    </button>
  );
}
