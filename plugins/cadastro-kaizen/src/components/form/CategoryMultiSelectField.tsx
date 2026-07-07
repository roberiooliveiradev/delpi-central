import { useMemo } from "react";

import {
  createDashboardMultiSelectField,
  type MultiSelectFieldLabels,
} from "@delpi/plugin-ui";

import { KAIZEN_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { buildCategoryOptions, rememberCustomCategories } from "../../utils/kaizenCategories";

const LABELS = {
  emptyLabel: "Nenhuma categoria",
  searchPlaceholder: "Buscar ou criar…",
  selectVisible: "Marcar visíveis",
  clear: "Limpar",
  emptyOptions: "Digite acima para criar uma categoria.",
  multipleSelected: (count: number) => `${count} selecionada(s)`,
  createOption: (query: string) => `Adicionar "${query}"`,
} satisfies MultiSelectFieldLabels;

const MultiSelect = createDashboardMultiSelectField({ prefix: "kz", labels: LABELS });

type CategoryMultiSelectFieldProps = {
  selectedValues: string[];
  onChange: (values: string[]) => void;
  disabled?: boolean;
  className?: string;
};

export function CategoryMultiSelectField({
  selectedValues,
  onChange,
  disabled = false,
  className,
}: CategoryMultiSelectFieldProps) {
  const options = useMemo(() => buildCategoryOptions(selectedValues), [selectedValues]);

  const handleChange = (values: string[]) => {
    onChange(values);
    rememberCustomCategories(values);
  };

  const handleCreateOption = (value: string) => {
    rememberCustomCategories([...selectedValues, value]);
  };

  return (
    <MultiSelect
      label="Categoria"
      labelHint={KAIZEN_HELP_TOOLTIPS.fields.category}
      options={options}
      selectedValues={selectedValues}
      onChange={handleChange}
      onCreateOption={handleCreateOption}
      searchable
      creatable
      maxCreateLength={50}
      disabled={disabled}
      className={className}
    />
  );
}
