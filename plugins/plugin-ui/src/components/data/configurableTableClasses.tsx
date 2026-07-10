import { createContext, useContext, type ReactNode } from "react";

export type ConfigurableTableClassNames = {
  root: string;
  rootEmpty: string;
  rootMinimal: string;
  rootBanded: string;
  rootAlignCenter: string;
  rootAlignRight: string;
  rootHeaderNormalCase: string;
  dataTable: string;
  tableFrame: string;
  title: string;
  header: string;
  headerCell: string;
  body: string;
  row: string;
  rowHeader: string;
  cell: string;
  emptyState: string;
  cssVarPrefix: string;
};

export function configurableTableBemClasses(
  prefix = "delpi-ui-config-table",
  cssVarPrefix = prefix,
): ConfigurableTableClassNames {
  return {
    root: prefix,
    rootEmpty: `${prefix}--empty`,
    rootMinimal: `${prefix}--minimal`,
    rootBanded: `${prefix}--banded`,
    rootAlignCenter: `${prefix}--align-center`,
    rootAlignRight: `${prefix}--align-right`,
    rootHeaderNormalCase: `${prefix}--header-normal-case`,
    dataTable: `${prefix}__data-table`,
    tableFrame: `${prefix}__frame`,
    title: `${prefix}__title`,
    header: `${prefix}__header`,
    headerCell: `${prefix}__header-cell`,
    body: `${prefix}__body`,
    row: `${prefix}__row`,
    rowHeader: `${prefix}__row--header`,
    cell: `${prefix}__cell`,
    emptyState: `${prefix}__empty-state`,
    cssVarPrefix,
  };
}

/** TV dashboard: root `tdp-configurable-table`, sub-elementos `tdp-table-*`, vars `--tdp-table-*`. */
export function configurableTableTvClasses(): ConfigurableTableClassNames {
  return {
    root: "tdp-configurable-table",
    rootEmpty: "tdp-configurable-table--empty",
    rootMinimal: "tdp-configurable-table--minimal",
    rootBanded: "tdp-configurable-table--banded",
    rootAlignCenter: "tdp-configurable-table--align-center",
    rootAlignRight: "tdp-configurable-table--align-right",
    rootHeaderNormalCase: "tdp-configurable-table--header-normal-case",
    dataTable: "tdp-data-table",
    tableFrame: "tdp-table-frame",
    title: "tdp-table-title",
    header: "tdp-table-header",
    headerCell: "tdp-table-header-cell",
    body: "tdp-table-body",
    row: "tdp-table-row",
    rowHeader: "tdp-table-row--header",
    cell: "tdp-table-cell",
    emptyState: "tdp-table-empty-state",
    cssVarPrefix: "tdp-table",
  };
}

const ConfigurableTableClassesContext = createContext<ConfigurableTableClassNames | null>(null);

export type ConfigurableTableClassesProviderProps = {
  prefix?: string;
  cssVarPrefix?: string;
  classNames?: ConfigurableTableClassNames;
  children: ReactNode;
};

export function ConfigurableTableClassesProvider({
  prefix,
  cssVarPrefix,
  classNames,
  children,
}: ConfigurableTableClassesProviderProps) {
  const value = classNames ?? configurableTableBemClasses(prefix, cssVarPrefix ?? prefix);
  return (
    <ConfigurableTableClassesContext.Provider value={value}>{children}</ConfigurableTableClassesContext.Provider>
  );
}

export function useConfigurableTableClasses(): ConfigurableTableClassNames {
  return useContext(ConfigurableTableClassesContext) ?? configurableTableBemClasses();
}
