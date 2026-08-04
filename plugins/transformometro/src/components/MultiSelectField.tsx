import {
  MultiSelectField as BaseMultiSelectField,
  createDashboardCreatableMultiSelectField,
  multiSelectBemClasses,
  multiSelectCreatablePacClasses,
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

const CREATABLE_LABELS = {
  emptyLabel: "Nenhuma tag",
  searchPlaceholder: "Buscar ou criar tag…",
  selectVisible: "Marcar visíveis",
  clear: "Limpar",
  emptyOptions: "Digite acima para criar uma tag.",
  emptyOptionsCreatable: "Pressione Enter ou use a opção «Adicionar».",
  multipleSelected: (count: number) => `${count} tag(s)`,
  selectedCountLabel: (count: number) => `${count} tag(s) selecionada(s)`,
  createOption: (query: string) => `Adicionar «${query.trim()}»`,
  searchAriaLabel: (label: string) => `Buscar ou adicionar em ${label}`,
  removeTagAriaLabel: (value: string) => `Remover ${value}`,
} satisfies MultiSelectFieldLabels;

const CLASS_NAMES = {
  ...multiSelectBemClasses("ds"),
  fieldLabel: "tm-field__label",
};

const CreatableBase = createDashboardCreatableMultiSelectField({
  classNames: {
    ...multiSelectCreatablePacClasses("ds"),
    fieldLabel: "tm-field__label",
  },
  labels: CREATABLE_LABELS,
  showSelectedTags: true,
  includeSelectedInOptions: true,
  showBulkActions: false,
});

export function MultiSelectField(props: DashboardMultiSelectFieldProps) {
  return <BaseMultiSelectField classNames={CLASS_NAMES} labels={LABELS} {...props} />;
}

/** Tags creatable (1 valor por campo de processo — família / agrupador). */
export const CreatableMultiSelectField = CreatableBase;

export type { MultiSelectOption };
export type MultiSelectFieldProps = DashboardMultiSelectFieldProps;

export function buildProcessoTagOptions(
  catalog: string[] | undefined,
  selected: string,
): MultiSelectOption[] {
  const seen = new Set<string>();
  const out: MultiSelectOption[] = [];
  for (const raw of [...(catalog ?? []), selected]) {
    const label = raw.trim();
    if (!label) continue;
    const key = label.toLocaleLowerCase("pt-BR");
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({ value: label, label });
  }
  return out.sort((a, b) => a.label.localeCompare(b.label, "pt-BR"));
}
