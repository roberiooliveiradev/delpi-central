import type { SettingsParameterItem } from "../../data/types/settings";
import { SiNativeTextControl } from "./siNativeFormFields";
import "./SettingsParametersForm.css";

type SettingsParametersFormProps = {
  items: SettingsParameterItem[];
  onChange: (items: SettingsParameterItem[]) => void;
};

export function SettingsParametersForm({
  items,
  onChange,
}: SettingsParametersFormProps) {
  function updateItem(
    index: number,
    field: keyof SettingsParameterItem,
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
    <div className="si-settings-parameters-form">
      {items.map((item, index) => (
        <article key={item.key} className="si-settings-parameters-form__card">
          <div className="si-settings-parameters-form__grid">
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
    <label className="si-settings-parameters-form__field">
      <span className="si-settings-parameters-form__label">{label}</span>
      {children}
    </label>
  );
}