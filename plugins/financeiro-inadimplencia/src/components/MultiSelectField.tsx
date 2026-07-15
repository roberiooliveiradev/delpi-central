import {
  MultiSelectField as PluginMultiSelectField,
  multiSelectBemClasses,
  type DashboardMultiSelectFieldProps,
  type MultiSelectFieldLabels,
  type MultiSelectOption,
} from "@delpi/plugin-ui/index";

const CLASS_NAMES = multiSelectBemClasses("fi");

const BASE_LABELS = {
  emptyLabel: "Nenhum cliente",
  searchPlaceholder: "Buscar cliente…",
  selectVisible: "Marcar visíveis",
  clear: "Limpar",
  emptyOptions: "Nenhuma opção encontrada.",
  multipleSelected: (count: number) => `${count} cliente(s)`,
} satisfies MultiSelectFieldLabels;

export type MultiSelectFieldProps = Omit<DashboardMultiSelectFieldProps, never> & {
  /** Quando informado, o gatilho mostra "Todos os clientes" se a seleção estiver completa. */
  totalOptionsCount?: number;
};

export function MultiSelectField({
  totalOptionsCount,
  emptyLabel,
  hint,
  placeholder,
  labelHint,
  ...props
}: MultiSelectFieldProps) {
  const labels: MultiSelectFieldLabels = {
    ...BASE_LABELS,
    searchPlaceholder: placeholder ?? BASE_LABELS.searchPlaceholder,
    multipleSelected: (count) =>
      totalOptionsCount != null && totalOptionsCount > 0 && count >= totalOptionsCount
        ? "Todos os clientes"
        : `${count} cliente(s)`,
  };

  return (
    <PluginMultiSelectField
      classNames={CLASS_NAMES}
      labels={labels}
      emptyLabel={emptyLabel ?? BASE_LABELS.emptyLabel}
      labelHint={hint ?? labelHint}
      {...props}
    />
  );
}

export type { MultiSelectOption };
