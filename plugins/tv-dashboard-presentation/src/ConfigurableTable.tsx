import type { ReactNode } from "react";
import {
  ConfigurablePresentationTable as PluginUiConfigurablePresentationTable,
  ConfigurableTableClassesProvider,
  configurableTableTvClasses,
  type ConfigurablePresentationTableProps as PluginUiConfigurablePresentationTableProps,
} from "@delpi/plugin-ui/index";

import type { ComunicadoTableOptions } from "./comunicadoTableOptions";
import type { ComunicadoTablePreset } from "./comunicadoTypes";
import type { TvDataTableColumn } from "./tvDataPresentation";

export type ConfigurableTableProps = Omit<PluginUiConfigurablePresentationTableProps, "columns" | "options" | "preset"> & {
  columns: TvDataTableColumn[];
  options?: ComunicadoTableOptions | null;
  preset?: ComunicadoTablePreset;
};

export function ConfigurableTable({
  columns,
  rows,
  options,
  preset = "grid",
  emptyMessage = "Sem linhas",
  className,
}: ConfigurableTableProps) {
  return (
    <ConfigurableTableClassesProvider classNames={configurableTableTvClasses()}>
      <PluginUiConfigurablePresentationTable
        columns={columns}
        rows={rows}
        options={options}
        preset={preset}
        emptyMessage={emptyMessage}
        className={className}
      />
    </ConfigurableTableClassesProvider>
  );
}

export function ConfigurableTableWithProvider({
  children,
  classNames = configurableTableTvClasses(),
}: {
  children: ReactNode;
  classNames?: ReturnType<typeof configurableTableTvClasses>;
}) {
  return <ConfigurableTableClassesProvider classNames={classNames}>{children}</ConfigurableTableClassesProvider>;
}
