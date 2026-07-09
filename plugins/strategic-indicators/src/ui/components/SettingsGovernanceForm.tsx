import type { SettingsGovernanceItem } from "../../data/types/settings";
import { SiNativeTextAreaControl } from "./siNativeFormFields";
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
              <input
                value={item.key}
                onChange={(e) => updateItem(index, "key", e.target.value)}
              />
            </Field>

            <Field label="Rótulo">
              <input
                value={item.label}
                onChange={(e) => updateItem(index, "label", e.target.value)}
              />
            </Field>

            <Field label="Valor">
              <input
                value={item.value}
                onChange={(e) => updateItem(index, "value", e.target.value)}
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