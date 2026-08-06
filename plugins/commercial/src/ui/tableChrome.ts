import { dataTableBemClasses, delpiUiClass } from "@delpi/plugin-ui/index";

/** Dual-class canônico da tabela Pedidos de Venda em Aberto. */
export const PVA_TABLE = dataTableBemClasses("pva");

export const PVA_COL_NUMERIC = delpiUiClass(
  "pva-table__col--numeric",
  "delpi-ui-table__col--numeric",
);

export const PVA_COL_COMPACT = delpiUiClass(
  "pva-table__col--compact",
  "delpi-ui-table__col--compact",
);
