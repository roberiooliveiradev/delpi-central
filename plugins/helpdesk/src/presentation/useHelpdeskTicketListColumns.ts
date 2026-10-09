import { useMemo } from "react";
import { useTableColumnVisibility } from "@delpi/plugin-ui/index";

import {
  preferencesFromVisibility,
  TICKET_LIST_COLUMN_CATALOG,
  type TicketListColumnPreference,
} from "../presentation/ticketListViewModel";

/** v3 — Requerente visível por padrão para todos; v2 migra preservando escolhas. */
const STORAGE_KEY = "helpdesk:ticket-list:columns:v3";
const LEGACY_STORAGE_KEYS = ["helpdesk:ticket-list:columns:v2"] as const;

/** One-shot v2→v3: Requerente passa a defaultVisible — reexibe sem apagar o resto. */
function migrateLegacyColumnPrefs(): void {
  if (typeof window === "undefined") return;
  try {
    if (window.localStorage.getItem(STORAGE_KEY)) return;
    const raw = window.localStorage.getItem(LEGACY_STORAGE_KEYS[0]);
    if (!raw) return;
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === "object") {
      const visibility = (parsed.visibility ?? parsed) as Record<string, unknown>;
      if (typeof visibility === "object" && visibility) visibility["requester"] = true;
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(parsed));
    }
  } catch {
    /* ignore parse / private mode */
  }
}

const COLUMN_ITEMS = TICKET_LIST_COLUMN_CATALOG.filter((column) => column.solicitante).map(
  (column) => ({
    key: column.key,
    label: column.header,
  }),
);

function defaultVisibility(canAssign: boolean): Record<string, boolean> {
  return Object.fromEntries(
    TICKET_LIST_COLUMN_CATALOG.filter((column) => column.solicitante).map((column) => {
      let visible = column.defaultVisible || column.fixed;
      if (canAssign && column.key === "urgency") {
        visible = true;
      }
      return [column.key, visible];
    }),
  );
}

/**
 * Column prefs for Meus Chamados.
 * Pass a stable `canAssign` (resolve capabilities before mount) so defaults densify correctly.
 */
export function useHelpdeskTicketListColumns(options?: { canAssign?: boolean }) {
  const canAssign = options?.canAssign === true;
  migrateLegacyColumnPrefs();
  const {
    visibility,
    order,
    orderedColumns,
    setColumnVisible,
    reorderColumns,
    reset,
  } = useTableColumnVisibility({
    storageKey: STORAGE_KEY,
    columns: COLUMN_ITEMS,
    defaultVisibility: defaultVisibility(canAssign),
    emptyFallbackKeys: ["id", "title"],
    keepAtLeastOne: true,
  });

  const columnPreferences: TicketListColumnPreference[] = useMemo(
    () => preferencesFromVisibility(visibility, order),
    [visibility, order],
  );

  return {
    columnPreferences,
    menuColumns: orderedColumns,
    visibility,
    setColumnVisible: (key: string, visible: boolean) => {
      const definition = TICKET_LIST_COLUMN_CATALOG.find((column) => column.key === key);
      if (definition?.fixed) return;
      setColumnVisible(key, visible);
    },
    reorderColumns,
    resetPreferences: reset,
  };
}
