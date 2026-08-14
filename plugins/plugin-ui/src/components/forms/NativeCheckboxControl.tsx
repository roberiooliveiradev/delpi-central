import type { ChangeEvent, ReactNode } from "react";

import { HelpTooltip } from "../help/HelpTooltip";

export type NativeCheckboxHintPlacement = "inline" | "tooltip";

export type NativeCheckboxControlProps = {
  id?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  /** Rótulo principal (texto ou bloco rico — ex. título + hint). */
  label?: ReactNode;
  /**
   * Alias de `label` — vários plugins passavam o texto como children;
   * sem isso o checkbox aparece sem rótulo (parece “texto invisível” no tema claro).
   */
  children?: ReactNode;
  /** Texto auxiliar: inline abaixo do label (legado) ou HelpTooltip compacto. */
  hint?: ReactNode;
  /**
   * `inline` (default) — parágrafo sob o label (legado).
   * `tooltip` — ícone HelpTooltip ao lado do label (toolbar de gráfico densa).
   */
  hintPlacement?: NativeCheckboxHintPlacement;
  /** Aria do botão de ajuda quando `hintPlacement="tooltip"`. */
  hintAriaLabel?: string;
  disabled?: boolean;
  className?: string;
  inputClassName?: string;
  boxClassName?: string;
  "aria-label"?: string;
};

/**
 * Checkbox moderno compacto (sem FormFieldShell) — toggles de FormatPane / filtros / admin.
 * Visual canônico em `native-controls.css` (caixa + check); input nativo só para a11y.
 */
export function NativeCheckboxControl({
  id,
  checked,
  onChange,
  label,
  children,
  hint,
  hintPlacement = "inline",
  hintAriaLabel = "Ajuda",
  disabled,
  className,
  inputClassName,
  boxClassName,
  "aria-label": ariaLabel,
}: NativeCheckboxControlProps) {
  const resolvedLabel = label ?? children;
  const useTooltipHint =
    hintPlacement === "tooltip" &&
    typeof hint === "string" &&
    hint.trim().length > 0;

  const copy =
    resolvedLabel || (hint && !useTooltipHint) ? (
      <span className="delpi-ui-native-checkbox__copy">
        {resolvedLabel ? (
          <span className="delpi-ui-native-checkbox__label">
            {resolvedLabel}
            {useTooltipHint ? (
              <HelpTooltip
                content={hint}
                ariaLabel={hintAriaLabel}
                className="delpi-ui-native-checkbox__help"
              />
            ) : null}
          </span>
        ) : null}
        {hint && !useTooltipHint ? (
          <span className="delpi-ui-native-checkbox__hint">{hint}</span>
        ) : null}
      </span>
    ) : useTooltipHint ? (
      <span className="delpi-ui-native-checkbox__copy">
        <span className="delpi-ui-native-checkbox__label">
          <HelpTooltip
            content={hint}
            ariaLabel={hintAriaLabel}
            className="delpi-ui-native-checkbox__help"
          />
        </span>
      </span>
    ) : null;

  return (
    <label
      className={["delpi-ui-native-checkbox", className].filter(Boolean).join(" ")}
      data-checked={checked ? "true" : "false"}
      data-disabled={disabled ? "true" : "false"}
      data-hint-placement={hintPlacement}
    >
      <input
        id={id}
        type="checkbox"
        className={["delpi-ui-native-checkbox__input", inputClassName]
          .filter(Boolean)
          .join(" ")}
        checked={checked}
        disabled={disabled}
        aria-label={ariaLabel}
        onChange={(event: ChangeEvent<HTMLInputElement>) => onChange(event.target.checked)}
      />
      <span
        className={["delpi-ui-native-checkbox__box", boxClassName].filter(Boolean).join(" ")}
        aria-hidden="true"
      />
      {copy}
    </label>
  );
}
