import { Printer } from "lucide-react";
import { DS_GHOST_BTN } from "./ghostChrome";

type PrintReportButtonProps = {
  disabled?: boolean;
  label?: string;
};

function triggerPrint() {
  const cleanup = () => {
    document.documentElement.classList.remove("ds-printing");
    window.removeEventListener("afterprint", cleanup);
  };

  window.addEventListener("afterprint", cleanup);
  document.documentElement.classList.add("ds-printing");
  window.dispatchEvent(new Event("resize"));

  requestAnimationFrame(() => {
    requestAnimationFrame(() => window.print());
  });
}

export function PrintReportButton({
  disabled = false,
  label = "PDF / Imprimir",
}: PrintReportButtonProps) {
  return (
    <button
      type="button"
      className={`${DS_GHOST_BTN} ds-no-print`}
      onClick={triggerPrint}
      disabled={disabled}
      aria-label="Imprimir ou salvar relatório em PDF"
    >
      <Printer size={16} aria-hidden />
      <span>{label}</span>
    </button>
  );
}
