import { useEffect, useMemo, useState } from "react";
import {
  createDashboardCreatableMultiSelectField,
  multiSelectCreatablePacClasses,
  type MultiSelectFieldLabels,
} from "@delpi/plugin-ui/index";

import { fetchLmpProblemTags } from "../api/lmpNonconformityApi";
import { LMPS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { buildProblemTagOptions } from "../utils/ncProblemTags";

const LABELS = {
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

const CreatableMultiSelect = createDashboardCreatableMultiSelectField({
  classNames: multiSelectCreatablePacClasses("lmps"),
  labels: LABELS,
  showSelectedTags: true,
  includeSelectedInOptions: true,
  showBulkActions: false,
});

type NcProblemTagsFieldProps = {
  id?: string;
  selectedValues: string[];
  onChange: (values: string[]) => void;
  disabled?: boolean;
  className?: string;
};

export function NcProblemTagsField({
  id = "nc-problem-tags",
  selectedValues,
  onChange,
  disabled = false,
  className,
}: NcProblemTagsFieldProps) {
  const [catalogLabels, setCatalogLabels] = useState<string[]>([]);

  useEffect(() => {
    let cancelled = false;
    fetchLmpProblemTags()
      .then((data) => {
        if (cancelled) return;
        setCatalogLabels(data.items.map((item) => item.label));
      })
      .catch(() => {
        if (!cancelled) setCatalogLabels([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const options = useMemo(
    () => buildProblemTagOptions(catalogLabels, selectedValues),
    [catalogLabels, selectedValues],
  );

  const handleChange = (values: string[]) => {
    onChange(values);
    setCatalogLabels((prev) => {
      const next = new Set(prev.map((v) => v.toLocaleLowerCase("pt-BR")));
      const merged = [...prev];
      for (const value of values) {
        const key = value.toLocaleLowerCase("pt-BR");
        if (!next.has(key)) {
          next.add(key);
          merged.push(value);
        }
      }
      return merged;
    });
  };

  return (
    <CreatableMultiSelect
      id={id}
      label="Problema identificado"
      hint={LMPS_HELP_TOOLTIPS.nonconformities.form.problemTags}
      options={options}
      selectedValues={selectedValues}
      onChange={handleChange}
      maxCreateLength={60}
      disabled={disabled}
      className={className}
      emptyLabel="Adicionar tags do problema…"
    />
  );
}
