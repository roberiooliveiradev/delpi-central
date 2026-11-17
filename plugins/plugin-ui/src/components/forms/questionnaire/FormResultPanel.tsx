import { Check } from "lucide-react";
import type { ReactNode } from "react";

import { delpiUiClass } from "../../../utils/delpiUiClass";

import { FormCard } from "./FormCard";

export type FormResultPanelTone = "success" | "info" | "warning" | "error";

export type FormResultPanelProps = {
  tone: FormResultPanelTone;
  title: ReactNode;
  message: ReactNode;
  hint?: ReactNode;
  /** Ação final (ex.: FormButton) — opcional. */
  action?: ReactNode;
  logo?: ReactNode;
  /** Prefixo BEM do consumidor (dual-class). */
  prefix?: string;
  className?: string;
};

/**
 * Tela de resultado/fechamento sobre `FormCard`, centralizada. `success`
 * mostra o círculo de 72 px com check; `role="status"` em sucesso/info e
 * `role="alert"` em erro (warning mantém `status` — não é falha bloqueante).
 */
export function FormResultPanel({
  tone,
  title,
  message,
  hint,
  action,
  logo,
  prefix = "ds",
  className,
}: FormResultPanelProps) {
  const cn = (suffix: string) =>
    delpiUiClass(
      `${prefix}-form-result${suffix}`,
      `delpi-ui-form-result${suffix}`,
    );

  return (
    <FormCard
      className={[cn(""), cn(`--${tone}`), className]
        .filter(Boolean)
        .join(" ")}
      role={tone === "error" ? "alert" : "status"}
    >
      <div className={cn("__inner")}>
        {logo != null && <div className={cn("__logo")}>{logo}</div>}
        {tone === "success" && (
          <span className={cn("__circle")} aria-hidden="true">
            <Check size={36} strokeWidth={3} />
          </span>
        )}
        <h2 className={cn("__title")}>{title}</h2>
        <p className={cn("__message")}>{message}</p>
        {hint != null && <p className={cn("__hint")}>{hint}</p>}
        {action != null && <div className={cn("__action")}>{action}</div>}
      </div>
    </FormCard>
  );
}
