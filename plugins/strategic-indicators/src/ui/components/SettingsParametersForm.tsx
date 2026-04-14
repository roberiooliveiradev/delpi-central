import type { SettingsParameterItem } from "../../data/types/settings";

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
    <div className="si-settings-form-list">
      {items.map((item, index) => (
        <article key={item.key} className="si-settings-form-card">
          <div className="si-settings-form-card__grid">
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
    <label className="si-settings-form-field">
      <span className="si-settings-form-field__label">{label}</span>
      {children}
    </label>
  );
}