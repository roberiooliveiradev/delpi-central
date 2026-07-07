import {
  createDashboardCreatableMultiSelectField,
  createDashboardMultiSelectField,
  multiSelectCreatablePacClasses,
  multiSelectPacClasses,
  type MultiSelectFieldLabels,
  type MultiSelectOption,
} from "@delpi/plugin-ui";

const MULTI_LABELS = {
  emptyLabel: "Todos",
  searchPlaceholder: "Buscar…",
  selectVisible: "Marcar visíveis",
  clear: "Limpar",
  emptyOptions: "Nenhuma opção encontrada.",
  multipleSelected: (count: number) => `${count} selecionado(s)`,
  searchAriaLabel: (label: string) => `Buscar ${label}`,
} satisfies MultiSelectFieldLabels;

const CREATABLE_LABELS = {
  emptyLabel: "Selecione ou digite…",
  searchPlaceholder: "Buscar ou adicionar…",
  selectVisible: "Marcar visíveis",
  clear: "Limpar",
  emptyOptions: "Nenhuma opção encontrada.",
  emptyOptionsCreatable: "Pressione Enter ou use o botão acima.",
  multipleSelected: (count: number) => `${count} item(ns) selecionado(s)`,
  selectedCountLabel: (count: number) => `${count} item(ns) selecionado(s)`,
  createOption: (value: string) => `Adicionar «${value.trim()}»`,
  searchAriaLabel: (label: string) => `Buscar ou adicionar em ${label}`,
  removeTagAriaLabel: (value: string) => `Remover ${value}`,
} satisfies MultiSelectFieldLabels;

export const MultiSelectField = createDashboardMultiSelectField({
  classNames: multiSelectPacClasses("pac"),
  labels: MULTI_LABELS,
});

export const CreatableMultiSelectField = createDashboardCreatableMultiSelectField({
  classNames: multiSelectCreatablePacClasses("pac"),
  labels: CREATABLE_LABELS,
});

export type { MultiSelectOption };
