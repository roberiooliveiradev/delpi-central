import { NativeTextControl } from "@delpi/plugin-ui/index";
import {
  lookupFieldLabel,
  patchFieldLabels,
  suggestEditableFields,
  type ComunicadoDataResolved,
  type FieldLabelsMap,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";

type Props = {
  resolved?: ComunicadoDataResolved;
  catalogFields?: Array<{ field: string; label: string }>;
  fieldLabels?: FieldLabelsMap;
  onChange: (next: FieldLabelsMap | undefined) => void;
  pane?: boolean;
  compact?: boolean;
};

/**
 * Editor do registro de rótulos da fonte — chave API estável, só muda o display.
 */
export function FieldLabelsEditor({
  resolved,
  catalogFields,
  fieldLabels,
  onChange,
  pane = false,
  compact = false,
}: Props) {
  const fields = suggestEditableFields(resolved, catalogFields, fieldLabels);
  if (fields.length === 0) return null;

  const compactNative = compact ? "delpi-ui-native-control--compact" : undefined;

  return (
    <DeckPropertySection
      title="Rótulos dos campos"
      hint={TV_DASHBOARD_HELP_TOOLTIPS.data.fieldLabels}
      pane={pane}
      defaultOpen
    >
      <p className="td-deck-inspector__hint">
        Renomeie colunas e métricas sem alterar a chave da API. Tabelas, gráficos, KPI e texto
        ligados a esta fonte herdam o rótulo.
      </p>
      <div className="td-field-labels-editor">
        {fields.map((item) => {
          const custom = lookupFieldLabel(fieldLabels, item.field) ?? "";
          return (
            <div key={item.field} className="td-field-labels-editor__row">
              <DeckField label={item.field}>
                <NativeTextControl
                  className={compactNative}
                  value={custom}
                  placeholder={item.defaultLabel}
                  onChange={(value) => {
                    onChange(patchFieldLabels(fieldLabels, item.field, value));
                  }}
                />
              </DeckField>
            </div>
          );
        })}
      </div>
    </DeckPropertySection>
  );
}
