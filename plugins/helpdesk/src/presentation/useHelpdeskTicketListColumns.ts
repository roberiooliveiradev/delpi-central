import { useMemo } from "react";
import { useTableColumnVisibility } from "@delpi/plugin-ui/index";

import {
  preferencesFromVisibility,
  TICKET_LIST_COLUMN_CATALOG,
  type TicketListColumnPreference,
} from "../presentation/ticketListViewModel";

const STORAGE_KEY = "helpdesk:ticket-list:columns:v1";

const COLUMN_ITEMS = TICKET_LIST_COLUMN_CATALOG.filter((column) => column.solicitante).map(
  (column) => ({
    key: column.key,
    label: column.header,
  }),
);

const DEFAULT_VISIBILITY = Object.fromEntries(
  TICKET_LIST_COLUMN_CATALOG.filter((column) => column.solicitante).map((column) => [
    column.key,
    column.defaultVisible || column.fixed,
  ]),
);

export function useHelpdeskTicketListColumns() {
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
    defaultVisibility: DEFAULT_VISIBILITY,
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
