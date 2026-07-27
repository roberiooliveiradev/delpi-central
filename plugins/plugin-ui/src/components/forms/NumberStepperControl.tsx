import { Minus, Plus } from "lucide-react";
import type { ReactNode } from "react";

import {
  ComboboxNumberControl,
  type ComboboxNumberControlProps,
} from "./ComboboxNumberControl";
import { mergeClassNames } from "./nativeControlClasses";

export type NumberStepperControlProps = ComboboxNumberControlProps & {
  onStepDown: () => void;
  onStepUp: () => void;
  stepDownDisabled?: boolean;
  stepUpDisabled?: boolean;
  stepDownAriaLabel: string;
  stepUpAriaLabel: string;
  /** Envolve o botão − (ex.: HintAction). */
  renderStepDown?: (button: ReactNode) => ReactNode;
  /** Envolve o botão + (ex.: HintAction). */
  renderStepUp?: (button: ReactNode) => ReactNode;
  /** Envolve o combobox central (ex.: HintAction). */
  renderValue?: (control: ReactNode) => ReactNode;
  groupAriaLabel?: string;
};

/**
 * Grupo unificado − / valor (combobox) / + — visual canônico `.delpi-ui-number-stepper*`.
 * Sem strings PT no pacote (labels via props).
 */
export function NumberStepperControl({
  onStepDown,
  onStepUp,
  stepDownDisabled = false,
  stepUpDisabled = false,
  stepDownAriaLabel,
  stepUpAriaLabel,
  renderStepDown,
  renderStepUp,
  renderValue,
  groupAriaLabel,
  className,
  square = false,
  compact = true,
  ...comboboxProps
}: NumberStepperControlProps) {
  const disabled = Boolean(comboboxProps.disabled);

  const stepDownButton = (
    <button
      type="button"
      className="delpi-ui-number-stepper__step delpi-ui-number-stepper__step--down"
      aria-label={stepDownAriaLabel}
      disabled={disabled || stepDownDisabled}
      onMouseDown={(event) => {
        event.preventDefault();
      }}
      onClick={onStepDown}
    >
      <Minus size={15} strokeWidth={2.25} aria-hidden="true" />
    </button>
  );

  const stepUpButton = (
    <button
      type="button"
      className="delpi-ui-number-stepper__step delpi-ui-number-stepper__step--up"
      aria-label={stepUpAriaLabel}
      disabled={disabled || stepUpDisabled}
      onMouseDown={(event) => {
        event.preventDefault();
      }}
      onClick={onStepUp}
    >
      <Plus size={15} strokeWidth={2.25} aria-hidden="true" />
    </button>
  );

  const valueControl = (
    <ComboboxNumberControl
      {...comboboxProps}
      square={square}
      compact={compact}
      className="delpi-ui-number-stepper__combobox"
    />
  );

  return (
    <div
      className={mergeClassNames(
        "delpi-ui-number-stepper",
        square ? "delpi-ui-number-stepper--square" : null,
        compact ? "delpi-ui-number-stepper--compact" : null,
        className,
      )}
      role="group"
      aria-label={groupAriaLabel}
    >
      {renderStepDown ? renderStepDown(stepDownButton) : stepDownButton}
      {renderValue ? renderValue(valueControl) : valueControl}
      {renderStepUp ? renderStepUp(stepUpButton) : stepUpButton}
    </div>
  );
}
