import { FormSelectControl } from "@delpi/plugin-ui/index";

import { DeckField } from "./deck/DeckField";
import type { ValueFieldOption } from "./ValueFieldsMultiSelect";

type Props = {
  id: string;
  label: string;
  value: string | undefined;
  fieldOptions: ValueFieldOption[];
  noneLabel?: string;
  onChange: (field: string | undefined) => void;
};

/** Select de campo do DataModel (ou «nenhum») para bindings dinâmicos do KPI. */
export function KpiDynamicFieldSelect({
  id,
  label,
  value,
  fieldOptions,
  noneLabel = "Nenhum (fixo / literal)",
  onChange,
}: Props) {
  return (
    <DeckField id={id} label={label}>
      <FormSelectControl
        id={id}
        ariaLabel={label}
        value={value?.trim() || ""}
        onChange={(next) => onChange(next.trim() || undefined)}
        options={[
          { value: "", label: noneLabel },
          ...fieldOptions.map((opt) => ({
            value: opt.field,
            label: opt.label?.trim() || opt.field,
          })),
        ]}
      />
    </DeckField>
  );
}
