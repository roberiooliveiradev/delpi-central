import { ComboboxNumberControl } from "@delpi/plugin-ui/index";
import {
  DECIMAL_PLACES_MAX,
  DECIMAL_PLACES_MIN,
  defaultDecimalPlacesForFormat,
  formatSupportsDecimalPlaces,
  type DecimalPlacesFormat,
} from "@delpi/tv-dashboard-presentation";

import { DeckField } from "./deck/DeckField";

const DECIMAL_PLACE_OPTIONS = [0, 1, 2, 3, 4, 5, 6] as const;

type Props = {
  format: string | null | undefined;
  value: number | null | undefined;
  onChange: (next: number | undefined) => void;
  compactClassName?: string;
  /** Quando false, renderiza só o controle (sem DeckField). */
  asField?: boolean;
};

/**
 * Controle de casas decimais — visível só para Número / Percentual / Moeda.
 * Valor omitido usa o default do formato; ao alterar, grava e arredonda na exibição.
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
    <ComboboxNumberControl
      className={compactClassName}
      compact={Boolean(compactClassName)}
      square={false}
      min={DECIMAL_PLACES_MIN}
      max={DECIMAL_PLACES_MAX}
      value={effective}
      options={DECIMAL_PLACE_OPTIONS}
      clamp={(n) =>
        Math.min(DECIMAL_PLACES_MAX, Math.max(DECIMAL_PLACES_MIN, Math.trunc(n)))
      }
      portalScopeClassName="dashboard-tv-dashboard"
      aria-label="Casas decimais"
      onChange={(n) =>
        onChange(
          Math.min(DECIMAL_PLACES_MAX, Math.max(DECIMAL_PLACES_MIN, Math.trunc(n))),
        )
      }
    />
  );

  if (!asField) return control;

  return <DeckField label="Casas decimais">{control}</DeckField>;
}
