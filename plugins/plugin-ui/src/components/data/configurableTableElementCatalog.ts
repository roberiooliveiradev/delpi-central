import type { ConfigurableTableOptions } from "./configurableTableOptions";

export type ConfigurableTableElementId = "tableTitle" | "header" | "borders" | "zebraStripe";

export type ConfigurableTableElementDefinition = {
  id: ConfigurableTableElementId;
  label: string;
  hint?: string;
};

export const CONFIGURABLE_TABLE_ELEMENT_CATALOG: ConfigurableTableElementDefinition[] = [
  { id: "tableTitle", label: "Título da tabela", hint: "Título acima da grade de dados." },
  { id: "header", label: "Cabeçalho", hint: "Linha com nomes das colunas." },
  { id: "borders", label: "Bordas", hint: "Linhas separadoras entre células." },
  { id: "zebraStripe", label: "Listras alternadas", hint: "Destaque em linhas pares do corpo." },
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
    case "borders":
      return options.showBorders !== false;
    case "zebraStripe":
      return Boolean(options.zebraStripe);
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
    case "borders":
      return { showBorders: enabled };
    case "zebraStripe":
      return { zebraStripe: enabled };
    default:
      return {};
  }
}
