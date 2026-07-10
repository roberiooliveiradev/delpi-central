import {
  CONFIGURABLE_TABLE_TEXT_ALIGN_OPTIONS,
  CONFIGURABLE_TABLE_VALUE_FORMAT_OPTIONS,
  DEFAULT_CONFIGURABLE_TABLE_OPTIONS,
  configurableTableOptionsCssVars,
  configurableTableOptionsModifierClasses,
  configurableTableTvClasses,
  formatConfigurableTableCellValue,
  mergeConfigurableTableOptions,
  presetDefaultConfigurableTableOptions,
  resolveConfigurableTableDisplayOptions,
  type ConfigurableTableOptions,
  type ConfigurableTableTextAlign,
  type ConfigurableTableValueFormat,
} from "@delpi/plugin-ui/index";

import type { ComunicadoTablePreset } from "./comunicadoTypes";

export type ComunicadoTableTextAlign = ConfigurableTableTextAlign;
export type ComunicadoTableValueFormat = ConfigurableTableValueFormat;
export type ComunicadoTableOptions = ConfigurableTableOptions;

export const TABLE_VALUE_FORMAT_OPTIONS = CONFIGURABLE_TABLE_VALUE_FORMAT_OPTIONS;
export const TABLE_TEXT_ALIGN_OPTIONS = CONFIGURABLE_TABLE_TEXT_ALIGN_OPTIONS;
export const DEFAULT_COMUNICADO_TABLE_OPTIONS = DEFAULT_CONFIGURABLE_TABLE_OPTIONS;
export const formatTableCellValue = formatConfigurableTableCellValue;
export const mergeComunicadoTableOptions = mergeConfigurableTableOptions;
export const presetDefaultTableOptions = presetDefaultConfigurableTableOptions;
export const resolveTableDisplayOptions = resolveConfigurableTableDisplayOptions;

const tvTableClasses = configurableTableTvClasses();

/** CSS vars com prefixo TV (`--tdp-table-*`). */
export function tableOptionsCssVars(options: ConfigurableTableOptions): Record<string, string | number> {
  return configurableTableOptionsCssVars(options, tvTableClasses.cssVarPrefix);
}

/** Modificadores com classes TV (`tdp-configurable-table--*`). */
export function tableOptionsModifierClasses(options: ConfigurableTableOptions): string[] {
  return configurableTableOptionsModifierClasses(options, tvTableClasses);
}

export type { ComunicadoTablePreset };
