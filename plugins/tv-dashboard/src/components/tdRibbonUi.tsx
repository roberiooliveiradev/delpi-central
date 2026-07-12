import {
  FormSelectControl,
  HintAction,
  mergeClassNames,
  type NativeSelectOption,
} from "@delpi/plugin-ui/index";
import type { ReactNode } from "react";

type TdRibbonSelectProps = {
  id?: string;
  value: string;
  onChange: (value: string) => void;
  options: readonly NativeSelectOption[];
  disabled?: boolean;
  className?: string;
  "aria-label"?: string;
};

/** Select compacto da ribbon do deck — visual FormSelectControl (painel DELPI). */
export function TdRibbonSelect({
  id,
  value,
  onChange,
  options,
  disabled,
  className,
  "aria-label": ariaLabel,
}: TdRibbonSelectProps) {
  return (
    <FormSelectControl
      id={id}
      value={value}
      onChange={onChange}
      options={options}
      disabled={disabled}
      className={mergeClassNames("td-deck-ribbon__select", "delpi-ui-select--compact", className)}
      ariaLabel={ariaLabel}
    />
  );
}

type TdRibbonIconButtonProps = {
  hint: string;
  ariaLabel: string;
  active?: boolean;
  disabled?: boolean;
  onClick: () => void;
  children: ReactNode;
};

/** Botão compacto da ribbon com balão explicativo. */
export function TdRibbonIconButton({
  hint,
  ariaLabel,
  active,
  disabled,
  onClick,
  children,
}: TdRibbonIconButtonProps) {
  return (
    <HintAction hint={hint} ariaLabel={ariaLabel} placement="bottom">
      <button
        type="button"
        className={[
          "td-btn",
          "td-btn--sm",
          "td-btn--icon",
          active ? "td-btn--active" : null,
        ]
          .filter(Boolean)
          .join(" ")}
        aria-label={ariaLabel}
        disabled={disabled}
        onClick={onClick}
      >
        {children}
      </button>
    </HintAction>
  );
}
