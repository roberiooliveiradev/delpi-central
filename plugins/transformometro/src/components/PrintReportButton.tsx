import { printScopedWindow } from "@delpi/plugin-ui/index";
import { Printer } from "lucide-react";

import { DS_GHOST_BTN } from "./ghostChrome";

type PrintReportButtonProps = {
  disabled?: boolean;
  label?: string;
};

export function PrintReportButton({
  disabled = false,
  label = "PDF / Imprimir",
}: PrintReportButtonProps) {
  return (
    <button
      type="button"
      className={`${DS_GHOST_BTN} ds-no-print`}
      onClick={() =>
        printScopedWindow({
          rootClassName: "ds-printing",
          dispatchResize: true,
        })
      }
      disabled={disabled}
      aria-label="Imprimir ou salvar relatório em PDF"
    >
      <Printer size={16} aria-hidden />
      <span>{label}</span>
    </button>
  );
}
