import type { SettingsGovernanceItem } from "../../data/types/settings";
import { SI_HELP } from "../../content/helpTooltips";
import { SiAdminFormField } from "./SiAdminFormField";
import { SiNativeTextAreaControl, SiNativeTextControl } from "./siNativeFormFields";
import "./SettingsGovernanceForm.css";

type SettingsGovernanceFormProps = {
  items: SettingsGovernanceItem[];
  onChange: (items: SettingsGovernanceItem[]) => void;
};

export function SettingsGovernanceForm({
  items,
  onChange,
}: SettingsGovernanceFormProps) {
  function updateItem(
    index: number,
    field: keyof SettingsGovernanceItem,
    value: string,
  ) {
    const next = [...items];
    next[index] = {
      ...next[index],
      [field]: value,
    };
    onChange(next);
  }

  return (
    <div className="si-settings-governance-form">
      {items.map((item, index) => (
        <article key={item.key} className="si-settings-governance-form__card">
          <div className="si-settings-governance-form__grid">
            <SiAdminFormField label="Chave">
              <SiNativeTextControl
                value={item.key}
                onChange={(value) => updateItem(index, "key", value)}
              />
            </SiAdminFormField>

            <SiAdminFormField label="Rótulo" hint={SI_HELP.system.governanceLabel}>
              <SiNativeTextControl
                value={item.label}
                onChange={(value) => updateItem(index, "label", value)}
              />
            </SiAdminFormField>

            <SiAdminFormField label="Valor" hint={SI_HELP.system.governanceValue}>
              <SiNativeTextControl
                value={item.value}
                onChange={(value) => updateItem(index, "value", value)}
              />
            </SiAdminFormField>

            <SiAdminFormField
              label="Observação"
              hint={SI_HELP.system.governanceObservation}
              fullWidth
            >
              <SiNativeTextAreaControl
                value={item.observation}
                aria-label="Observação"
                onChange={(observation) => updateItem(index, "observation", observation)}
              />
            </SiAdminFormField>
          </div>
        </article>
      ))}
    </div>
  );
}
