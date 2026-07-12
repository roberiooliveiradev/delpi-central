import type { SettingsGovernanceItem } from "../../data/types/settings";
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
            <Field label="Chave">
              <SiNativeTextControl
                value={item.key}
                onChange={(value) => updateItem(index, "key", value)}
              />
            </Field>

            <Field label="Rótulo">
              <SiNativeTextControl
                value={item.label}
                onChange={(value) => updateItem(index, "label", value)}
              />
            </Field>

            <Field label="Valor">
              <SiNativeTextControl
                value={item.value}
                onChange={(value) => updateItem(index, "value", value)}
              />
            </Field>

            <Field label="Observação">
              <SiNativeTextAreaControl
                value={item.observation}
                aria-label="Observação"
                onChange={(observation) => updateItem(index, "observation", observation)}
              />
            </Field>
          </div>
        </article>
      ))}
    </div>
  );
}

type FieldProps = {
  label: string;
  children: React.ReactNode;
};

function Field({ label, children }: FieldProps) {
  return (
    <label className="si-settings-governance-form__field">
      <span className="si-settings-governance-form__label">{label}</span>
      {children}
    </label>
  );
}