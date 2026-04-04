import type { SettingsWeightItem } from "../../data/types/settings";

type SettingsWeightsFormProps = {
  items: SettingsWeightItem[];
  onChange: (items: SettingsWeightItem[]) => void;
};

export function SettingsWeightsForm({
  items,
  onChange,
}: SettingsWeightsFormProps) {
  function updateItem(
    index: number,
    field: keyof SettingsWeightItem,
    value: string | number,
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
        <article key={item.department_id} className="si-settings-form-card">
          <div className="si-settings-form-card__grid">
            <Field label="Departamento">
              <input
                value={item.department_name}
                onChange={(e) =>
                  updateItem(index, "department_name", e.target.value)
                }
              />
            </Field>

            <Field label="ID do departamento">
              <input
                value={item.department_id}
                onChange={(e) =>
                  updateItem(index, "department_id", e.target.value)
                }
              />
            </Field>

            <Field label="Peso (%)">
              <input
                type="number"
                value={item.weight_pct}
                onChange={(e) =>
                  updateItem(index, "weight_pct", Number(e.target.value))
                }
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