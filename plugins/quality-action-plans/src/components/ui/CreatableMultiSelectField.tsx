import {
  MultiSelectField as BaseMultiSelectField,
  multiSelectBemClasses,
  type MultiSelectFieldClassNames,
  type MultiSelectFieldLabels,
} from "@delpi/plugin-ui";

import type { SelectOption } from "./types";

const PAC_CREATABLE_CLASS_NAMES: MultiSelectFieldClassNames = {
  ...multiSelectBemClasses("pac"),
  root: "pac-field pac-field--creatable-multi",
  tagList: "pac-tag-list",
  tagChip: "pac-tag-chip",
  tagRemove: "pac-tag-chip__remove",
};

const LABELS = {
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

type CreatableMultiSelectFieldProps = {
  id?: string;
  label: string;
  hint?: string;
  options?: SelectOption[];
  selectedValues: string[];
  onChange: (values: string[]) => void;
  emptyLabel?: string;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
};

export function CreatableMultiSelectField({
  hint,
  options = [],
  emptyLabel,
  placeholder,
  ...props
}: CreatableMultiSelectFieldProps) {
  return (
    <BaseMultiSelectField
      labelHint={hint}
      options={options}
      searchable
      creatable
      showSelectedTags
      includeSelectedInOptions
      showBulkActions={false}
      emptyLabel={emptyLabel}
      classNames={PAC_CREATABLE_CLASS_NAMES}
      labels={{
        ...LABELS,
        searchPlaceholder: placeholder ?? LABELS.searchPlaceholder,
      }}
      {...props}
    />
  );
}
