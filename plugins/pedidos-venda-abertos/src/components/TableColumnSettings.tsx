import {
  TableColumnVisibilityMenu,
  type TableColumnVisibilityMenuLabels,
} from "@delpi/plugin-ui/index";

import type { TableColumnKey } from "../utils/tableColumns";
import { TABLE_COLUMNS } from "../utils/tableColumns";

type TableColumnSettingsProps = {
  visibility: Record<TableColumnKey, boolean>;
  onToggleColumn: (key: TableColumnKey, visible: boolean) => void;
  onReset: () => void;
};

const LABELS = {
  trigger: "Colunas",
  panelTitle: "Exibir colunas",
  reset: "Restaurar",
  hint: "Escolha quais colunas exibir. A preferência é salva neste navegador.",
  columnAriaLabel: (columnLabel: string) => `Exibir coluna ${columnLabel}`,
  panelAriaLabel: "Colunas visíveis",
} satisfies TableColumnVisibilityMenuLabels;

export function TableColumnSettings({
  visibility,
  onToggleColumn,
  onReset,
}: TableColumnSettingsProps) {
  return (
    <TableColumnVisibilityMenu
      columns={TABLE_COLUMNS}
      visibility={visibility}
      onToggleColumn={(key, visible) => onToggleColumn(key as TableColumnKey, visible)}
      onReset={onReset}
      labels={LABELS}
    />
  );
}
