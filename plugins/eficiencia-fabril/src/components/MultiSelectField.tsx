import {
  MultiSelectField as BaseMultiSelectField,
  multiSelectBemClasses,
  type DashboardMultiSelectFieldProps,
  type MultiSelectFieldLabels,
  type MultiSelectOption,
} from "@delpi/plugin-ui/index";

const LABELS = {
  emptyLabel: "Todos",
  searchPlaceholder: "Buscar…",
  selectVisible: "Marcar visíveis",
  clear: "Limpar",
  emptyOptions: "Nenhuma opção encontrada.",
  multipleSelected: (count: number) => `${count} selecionado(s)`,
} satisfies MultiSelectFieldLabels;

const CLASS_NAMES = {
  ...multiSelectBemClasses("ef"),
  root: "ef-field ef-field--multi-select",
  actionButton: "ef-btn ef-btn--ghost ef-btn--sm",
};

export function MultiSelectField(props: DashboardMultiSelectFieldProps) {
  return <BaseMultiSelectField classNames={CLASS_NAMES} labels={LABELS} {...props} />;
}

export type { MultiSelectOption };
export type MultiSelectFieldProps = DashboardMultiSelectFieldProps;
