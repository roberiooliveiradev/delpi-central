import { printScopedWindow } from "@delpi/plugin-ui/index";
import { Printer } from "lucide-react";

import { GHOST_BTN } from "../ui/ghostChrome";

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
      className={`${GHOST_BTN} dq-no-print`}
      onClick={() =>
        printScopedWindow({
          rootClassName: "dq-printing",
          dispatchResize: true,
        })
      }
      disabled={disabled}
      aria-label="Imprimir relatório da página"
    >
      <Printer size={16} aria-hidden />
      <span>{label}</span>
    </button>
  );
}
