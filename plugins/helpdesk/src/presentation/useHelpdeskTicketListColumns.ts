import { useMemo } from "react";
import { useTableColumnVisibility } from "@delpi/plugin-ui/index";

import {
  preferencesFromVisibility,
  TICKET_LIST_COLUMN_CATALOG,
  type TicketListColumnPreference,
} from "../presentation/ticketListViewModel";

/** v2 — defaults requester enxutos; urgência/requerente via picker ou density assignable. */
const STORAGE_KEY = "helpdesk:ticket-list:columns:v2";

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
      if (canAssign && (column.key === "urgency" || column.key === "requester")) {
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
