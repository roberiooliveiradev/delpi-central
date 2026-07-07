import {
  MultiSelectField as BaseMultiSelectField,
  multiSelectBemClasses,
  type DashboardMultiSelectFieldProps,
  type MultiSelectFieldLabels,
  type MultiSelectOption,
} from "@delpi/plugin-ui";

const LABELS = {
  emptyLabel: "Todos",
  searchPlaceholder: "Buscar…",
  selectVisible: "Marcar visíveis",
  clear: "Limpar",
  emptyOptions: "Nenhuma opção encontrada.",
  multipleSelected: (count: number) => `${count} selecionado(s)`,
} satisfies MultiSelectFieldLabels;

const CLASS_NAMES = {
  ...multiSelectBemClasses("ds"),
  fieldLabel: "tm-field__label",
};

export function MultiSelectField(props: DashboardMultiSelectFieldProps) {
  return <BaseMultiSelectField classNames={CLASS_NAMES} labels={LABELS} {...props} />;
}

export type { MultiSelectOption };
export type MultiSelectFieldProps = DashboardMultiSelectFieldProps;
