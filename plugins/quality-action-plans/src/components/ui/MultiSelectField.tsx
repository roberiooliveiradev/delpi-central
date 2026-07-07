import {
  MultiSelectField as BaseMultiSelectField,
  multiSelectBemClasses,
  type DashboardMultiSelectFieldProps,
  type MultiSelectFieldClassNames,
  type MultiSelectFieldLabels,
  type MultiSelectOption,
} from "@delpi/plugin-ui";

import type { SelectOption } from "./types";

const PAC_MULTI_SELECT_CLASS_NAMES: MultiSelectFieldClassNames = {
  ...multiSelectBemClasses("pac"),
  root: "pac-field pac-field--multi",
};

const LABELS = {
  emptyLabel: "Todos",
  searchPlaceholder: "Buscar…",
  selectVisible: "Marcar visíveis",
  clear: "Limpar",
  emptyOptions: "Nenhuma opção encontrada.",
  multipleSelected: (count: number) => `${count} selecionado(s)`,
  searchAriaLabel: (label: string) => `Buscar ${label}`,
} satisfies MultiSelectFieldLabels;

type MultiSelectFieldProps = Omit<DashboardMultiSelectFieldProps, "labelHint" | "options"> & {
  hint?: string;
  options: SelectOption[];
};

export function MultiSelectField({
  hint,
  options,
  searchable = true,
  ...props
}: MultiSelectFieldProps) {
  return (
    <BaseMultiSelectField
      labelHint={hint}
      options={options}
      searchable={searchable}
      classNames={PAC_MULTI_SELECT_CLASS_NAMES}
      labels={LABELS}
      {...props}
    />
  );
}

export type { MultiSelectOption };
