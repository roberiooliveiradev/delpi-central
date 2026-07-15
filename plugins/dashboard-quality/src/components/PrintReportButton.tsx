import { GHOST_BTN } from "../ui/ghostChrome";
import { Printer } from "lucide-react";

type PrintReportButtonProps = {
  disabled?: boolean;
  label?: string;
};

function triggerPrint() {
  const cleanup = () => {
    document.documentElement.classList.remove("dq-printing");
    window.removeEventListener("afterprint", cleanup);
  };

  window.addEventListener("afterprint", cleanup);
  document.documentElement.classList.add("dq-printing");
  window.dispatchEvent(new Event("resize"));

  requestAnimationFrame(() => {
    requestAnimationFrame(() => window.print());
  });
}

export function PrintReportButton({
  disabled = false,
  label = "Imprimir",
}: PrintReportButtonProps) {
  return (
    <button
      type="button"
      className={`${GHOST_BTN} dq-no-print`}
      onClick={triggerPrint}
      disabled={disabled}
      aria-label="Imprimir relatório da página"
    >
      <Printer size={16} aria-hidden />
      <span>{label}</span>
    </button>
  );
}
