import type { SettingsGoalItem } from "../../data/types/settings";

type SettingsGoalsFormProps = {
  items: SettingsGoalItem[];
  onChange: (items: SettingsGoalItem[]) => void;
};

export function SettingsGoalsForm({
  items,
  onChange,
}: SettingsGoalsFormProps) {
  function updateItem(
    index: number,
    field: keyof SettingsGoalItem,
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

            <Field label="Meta principal">
              <input
                value={item.headline_goal}
                onChange={(e) =>
                  updateItem(index, "headline_goal", e.target.value)
                }
              />
            </Field>

            <Field label="Foco de apoio">
              <textarea
                value={item.supporting_focus}
                onChange={(e) =>
                  updateItem(index, "supporting_focus", e.target.value)
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