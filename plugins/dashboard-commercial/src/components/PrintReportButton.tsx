import { Printer } from "lucide-react";

type PrintReportButtonProps = {
  disabled?: boolean;
  label?: string;
};

function triggerPrint() {
  const cleanup = () => {
    document.documentElement.classList.remove("dc-printing");
    window.removeEventListener("afterprint", cleanup);
  };

  window.addEventListener("afterprint", cleanup);
  document.documentElement.classList.add("dc-printing");
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
      className="dc-ghost-btn dc-no-print"
      onClick={triggerPrint}
      disabled={disabled}
      aria-label="Imprimir relatório da página"
    >
      <Printer size={16} aria-hidden />
      <span>{label}</span>
    </button>
  );
}
