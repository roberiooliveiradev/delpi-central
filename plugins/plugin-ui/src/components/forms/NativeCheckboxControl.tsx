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
   * `tooltip` — HelpTooltip no próprio rótulo (sem ícone `?`; toolbar densa).
   */
  hintPlacement?: NativeCheckboxHintPlacement;
  /** Aria da ajuda quando `hintPlacement="tooltip"` (wrap no label). */
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

  const labelNode = resolvedLabel ? (
    useTooltipHint ? (
      <HelpTooltip
        content={hint}
        ariaLabel={hintAriaLabel}
        wrap
        placement="bottom"
        className="delpi-ui-native-checkbox__help"
      >
        <span className="delpi-ui-native-checkbox__label">{resolvedLabel}</span>
      </HelpTooltip>
    ) : (
      <span className="delpi-ui-native-checkbox__label">{resolvedLabel}</span>
    )
  ) : null;

  const copy =
    labelNode || (hint && !useTooltipHint) ? (
      <span className="delpi-ui-native-checkbox__copy">
        {labelNode}
        {hint && !useTooltipHint ? (
          <span className="delpi-ui-native-checkbox__hint">{hint}</span>
        ) : null}
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
