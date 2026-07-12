import type { ConfigurableTableOptions } from "./configurableTableOptions";

/**
 * Elementos / opções de estilo de tabela — paridade Excel Table Design → Style Options
 * (+ título e bordas DELPI).
 */
export type ConfigurableTableElementId =
  | "tableTitle"
  | "header"
  | "totalRow"
  | "zebraStripe"
  | "firstColumn"
  | "lastColumn"
  | "bandedColumns"
  | "borders";

export type ConfigurableTableElementDefinition = {
  id: ConfigurableTableElementId;
  label: string;
  hint?: string;
};

export const CONFIGURABLE_TABLE_ELEMENT_CATALOG: ConfigurableTableElementDefinition[] = [
  { id: "tableTitle", label: "Título da tabela", hint: "Título acima da grade de dados." },
  { id: "header", label: "Linha de cabeçalho", hint: "Excel: Header Row — nomes das colunas." },
  { id: "totalRow", label: "Linha de totais", hint: "Excel: Total Row — soma colunas numéricas." },
  { id: "zebraStripe", label: "Listras nas linhas", hint: "Excel: Banded Rows — linhas pares destacadas." },
  { id: "firstColumn", label: "Primeira coluna", hint: "Excel: First Column — destaque na 1ª coluna." },
  { id: "lastColumn", label: "Última coluna", hint: "Excel: Last Column — destaque na última coluna." },
  {
    id: "bandedColumns",
    label: "Listras nas colunas",
    hint: "Excel: Banded Columns — colunas pares destacadas.",
  },
  { id: "borders", label: "Bordas", hint: "Linhas separadoras entre células." },
];

export function isConfigurableTableElementEnabled(
  elementId: ConfigurableTableElementId,
  options: ConfigurableTableOptions,
): boolean {
  switch (elementId) {
    case "tableTitle":
      return options.showTitle !== false;
    case "header":
      return options.showHeader !== false;
    case "totalRow":
      return Boolean(options.showTotalRow);
    case "borders":
      return options.showBorders !== false;
    case "zebraStripe":
      return Boolean(options.zebraStripe);
    case "firstColumn":
      return Boolean(options.emphasizeFirstColumn);
    case "lastColumn":
      return Boolean(options.emphasizeLastColumn);
    case "bandedColumns":
      return Boolean(options.bandedColumns);
    default:
      return false;
  }
}

export function setConfigurableTableElementEnabled(
  elementId: ConfigurableTableElementId,
  enabled: boolean,
): Partial<ConfigurableTableOptions> {
  switch (elementId) {
    case "tableTitle":
      return { showTitle: enabled };
    case "header":
      return { showHeader: enabled };
    case "totalRow":
      return { showTotalRow: enabled };
    case "borders":
      return { showBorders: enabled };
    case "zebraStripe":
      return { zebraStripe: enabled };
    case "firstColumn":
      return { emphasizeFirstColumn: enabled };
    case "lastColumn":
      return { emphasizeLastColumn: enabled };
    case "bandedColumns":
      return { bandedColumns: enabled };
    default:
      return {};
  }
}
