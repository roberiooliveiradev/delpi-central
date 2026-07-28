import { NumberStepperControl } from "@delpi/plugin-ui/index";
import {
  DECIMAL_PLACES_MAX,
  DECIMAL_PLACES_MIN,
  defaultDecimalPlacesForFormat,
  formatSupportsDecimalPlaces,
  type DecimalPlacesFormat,
} from "@delpi/tv-dashboard-presentation";

import { DeckField } from "./deck/DeckField";

const DECIMAL_PLACE_OPTIONS = [0, 1, 2, 3, 4, 5, 6] as const;
const DECIMAL_PLACE_STEP = 1;

type Props = {
  format: string | null | undefined;
  value: number | null | undefined;
  onChange: (next: number | undefined) => void;
  compactClassName?: string;
  /** Quando false, renderiza só o controle (sem DeckField). */
  asField?: boolean;
};

function clampDecimalPlaces(n: number): number {
  return Math.min(DECIMAL_PLACES_MAX, Math.max(DECIMAL_PLACES_MIN, Math.trunc(n)));
}

/**
 * Controle de casas decimais — mesmo padrão visual do tamanho de fonte (− / valor / +).
 * Visível só para Número / Percentual / Moeda.
 */
export function DecimalPlacesField({
  format,
  value,
  onChange,
  compactClassName,
  asField = true,
}: Props) {
  if (!formatSupportsDecimalPlaces(format)) return null;
  const fmt = format as DecimalPlacesFormat;
  const effective =
    typeof value === "number" && Number.isFinite(value)
      ? value
      : defaultDecimalPlacesForFormat(fmt);

  const control = (
    <NumberStepperControl
      className={compactClassName}
      compact
      square={false}
      groupAriaLabel="Casas decimais"
      aria-label="Casas decimais"
      min={DECIMAL_PLACES_MIN}
      max={DECIMAL_PLACES_MAX}
      value={effective}
      options={DECIMAL_PLACE_OPTIONS}
      clamp={clampDecimalPlaces}
      portalScopeClassName="dashboard-tv-dashboard"
      onChange={(n) => onChange(clampDecimalPlaces(n))}
      onStepDown={() => onChange(clampDecimalPlaces(effective - DECIMAL_PLACE_STEP))}
      onStepUp={() => onChange(clampDecimalPlaces(effective + DECIMAL_PLACE_STEP))}
      stepDownDisabled={effective <= DECIMAL_PLACES_MIN}
      stepUpDisabled={effective >= DECIMAL_PLACES_MAX}
      stepDownAriaLabel="Diminuir casas decimais"
      stepUpAriaLabel="Aumentar casas decimais"
    />
  );

  if (!asField) return control;

  return <DeckField label="Casas decimais">{control}</DeckField>;
}
