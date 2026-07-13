import { NativeCheckboxControl } from "@delpi/plugin-ui/index";
import {
  normalizeSelectedValueFields,
  type ComunicadoDataBinding,
} from "@delpi/tv-dashboard-presentation";

export type ValueFieldOption = {
  field: string;
  label: string;
};

type Props = {
  idPrefix: string;
  options: ValueFieldOption[];
  /** Seleção atual; undefined/vazio = todas marcadas. */
  selectedValueFields?: string[] | null;
  valueField?: string | null;
  onChange: (next: {
    selectedValueFields?: string[];
    valueField?: string;
  }) => void;
  compact?: boolean;
};

/** Resolve quais checkboxes estão marcados (vazio = todas). */
export function resolveCheckedValueFields(
  options: ValueFieldOption[],
  selectedValueFields?: string[] | null,
  valueField?: string | null,
): Set<string> {
  const catalog = options.map((item) => item.field);
  const multi = normalizeSelectedValueFields(selectedValueFields);
  if (multi) {
    return new Set(multi.filter((field) => catalog.includes(field)));
  }
  const single = valueField?.trim();
  if (single && catalog.includes(single)) {
    return new Set([single]);
  }
  return new Set(catalog);
}

export function patchValueFieldSelection(
  options: ValueFieldOption[],
  currentChecked: Set<string>,
  field: string,
  checked: boolean,
): { selectedValueFields?: string[]; valueField?: string } {
  const catalog = options.map((item) => item.field);
  const next = new Set(currentChecked);
  if (checked) next.add(field);
  else next.delete(field);

  // Nada marcado → volta ao automático (todas).
  if (next.size === 0 || next.size === catalog.length) {
    return {};
  }
  const ordered = catalog.filter((item) => next.has(item));
  return {
    selectedValueFields: ordered,
    valueField: ordered[0],
  };
}

/**
 * Multi-seleção de métricas escalares da rota (KPI/gráfico/tabela).
 * Vazio = todas as métricas do catálogo.
 */
export function ValueFieldsMultiSelect({
  idPrefix,
  options,
  selectedValueFields,
  valueField,
  onChange,
  compact = false,
}: Props) {
  if (options.length === 0) return null;

  const checked = resolveCheckedValueFields(options, selectedValueFields, valueField);

  return (
    <div
      className={
        compact
          ? "td-deck-inspector__value-fields td-deck-inspector__value-fields--compact"
          : "td-deck-inspector__value-fields"
      }
      role="group"
      aria-label="Campos de valor"
    >
      <p className="td-deck-inspector__hint">
        {checked.size === options.length
          ? "Todas as métricas (marque para filtrar)"
          : `${checked.size} de ${options.length} métricas`}
      </p>
      {options.map((option) => (
        <NativeCheckboxControl
          key={option.field}
          id={`${idPrefix}-${option.field}`}
          className="td-deck-inspector__checkbox"
          checked={checked.has(option.field)}
          label={option.label}
          onChange={(nextChecked) => {
            onChange(patchValueFieldSelection(options, checked, option.field, nextChecked));
          }}
        />
      ))}
    </div>
  );
}

/** Aplica patch de seleção ao dataBinding (fonte). */
export function applyValueFieldSelectionToBinding(
  binding: ComunicadoDataBinding,
  patch: { selectedValueFields?: string[]; valueField?: string },
): ComunicadoDataBinding {
  const next: ComunicadoDataBinding = { ...binding };
  if (!patch.selectedValueFields || patch.selectedValueFields.length === 0) {
    delete next.selectedValueFields;
    delete next.valueField;
  } else {
    next.selectedValueFields = patch.selectedValueFields;
    next.valueField = patch.valueField ?? patch.selectedValueFields[0];
  }
  return next;
}
