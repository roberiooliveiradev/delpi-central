import { useCallback, useState } from "react";
import type { DataTableColumnWidths } from "@delpi/plugin-ui/index";

function loadWidths(storageKey: string): DataTableColumnWidths {
  try {
    const raw = window.localStorage.getItem(storageKey);
    if (!raw) return {};
    const data = JSON.parse(raw) as Record<string, unknown>;
    const widths: DataTableColumnWidths = {};
    for (const [key, value] of Object.entries(data)) {
      if (typeof value === "number" && Number.isFinite(value) && value > 0) {
        widths[key] = value;
      }
    }
    return widths;
  } catch {
    return {};
  }
}

/**
 * Larguras de coluna persistidas por página — com `resizableColumns`, o
 * usuário ajusta a largura pelo handle do cabeçalho e a preferência
 * sobrevive à navegação/recarregamento.
 */
export function useTableColumnWidths(storageKey: string) {
  const [widths, setWidths] = useState<DataTableColumnWidths>(() =>
    loadWidths(storageKey)
  );

  const onColumnWidthsChange = useCallback(
    (next: DataTableColumnWidths) => {
      setWidths(next);
      try {
        window.localStorage.setItem(storageKey, JSON.stringify(next));
      } catch {
        // localStorage indisponível — resize continua funcional na sessão.
      }
    },
    [storageKey]
  );

  return { columnWidths: widths, onColumnWidthsChange };
}
