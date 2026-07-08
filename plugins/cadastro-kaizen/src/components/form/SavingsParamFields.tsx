import type { ReactNode } from "react";

import { TextField } from "../ui";
import { ReadOnlyField } from "../ui/ReadOnlyField";
import { KAIZEN_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { visibleSavingsParamFields, type SavingsParamField } from "../../constants/kaizen";
import type { KaizenFormValues } from "../../types/kaizen";

const PARAM_META: Record<SavingsParamField, { label: string; hint: string }> = {
  seconds_per_occurrence: {
    label: "Segundos por ocorrência",
    hint: KAIZEN_HELP_TOOLTIPS.savingsParams.seconds_per_occurrence,
  },
  occurrences_per_day: {
    label: "Ocorrências por dia",
    hint: KAIZEN_HELP_TOOLTIPS.savingsParams.occurrences_per_day,
  },
  hourly_cost: {
    label: "Custo hora (R$)",
    hint: KAIZEN_HELP_TOOLTIPS.savingsParams.hourly_cost,
  },
  quantity_saved_per_day: {
    label: "Quantidade economizada/dia",
    hint: KAIZEN_HELP_TOOLTIPS.savingsParams.quantity_saved_per_day,
  },
  unit_material_cost: {
    label: "Custo unitário material (R$)",
    hint: KAIZEN_HELP_TOOLTIPS.savingsParams.unit_material_cost,
  },
  fixed_daily_savings: {
    label: "Economia fixa/dia (R$)",
    hint: KAIZEN_HELP_TOOLTIPS.savingsParams.fixed_daily_savings,
  },
};

type Props = {
  savingsType: KaizenFormValues["savings_type"];
  values: KaizenFormValues;
  onChange: (key: SavingsParamField, value: string) => void;
  idPrefix?: string;
};

/**
 * Campos de parâmetros de economia exibidos dinamicamente conforme o tipo escolhido.
 * Fonte única usada tanto no cadastro novo quanto na edição da ficha.
 */
export function SavingsParamFields({ savingsType, values, onChange, idPrefix = "kz-sp" }: Props) {
  return (
    <>
      {visibleSavingsParamFields(savingsType).map((field) => (
        <TextField
          key={field}
          id={`${idPrefix}-${field.replace(/_/g, "-")}`}
          label={PARAM_META[field].label}
          hint={PARAM_META[field].hint}
          inputMode="decimal"
          value={values[field]}
          onChange={(value) => onChange(field, value)}
        />
      ))}
    </>
  );
}

type ReadProps = {
  savingsType: KaizenFormValues["savings_type"];
  record: Record<SavingsParamField, ReactNode>;
};

/** Versão somente-leitura: mostra apenas os parâmetros do tipo escolhido (mesmo padrão da edição). */
export function SavingsParamReadFields({ savingsType, record }: ReadProps) {
  return (
    <>
      {visibleSavingsParamFields(savingsType).map((field) => (
        <ReadOnlyField
          key={field}
          label={PARAM_META[field].label}
          hint={PARAM_META[field].hint}
          value={record[field]}
        />
      ))}
    </>
  );
}
