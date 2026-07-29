import type { ReactNode } from "react";

import { ReadOnlyField } from "./ReadOnlyField";

type ReadOnlyChipsFieldProps<T> = {
  label: string;
  hint?: string;
  wide?: boolean;
  items: readonly T[];
  renderChip: (item: T, index: number) => ReactNode;
};

/** Campo somente leitura com lista de chips (categorias, participantes, etc.). */
export function ReadOnlyChipsField<T>({
  label,
  hint,
  wide,
  items,
  renderChip,
}: ReadOnlyChipsFieldProps<T>) {
  return (
    <ReadOnlyField
      label={label}
      hint={hint}
      wide={wide}
      value={
        items.length === 0 ? undefined : (
          <div className="kz-chips">{items.map((item, index) => renderChip(item, index))}</div>
        )
      }
    />
  );
}
