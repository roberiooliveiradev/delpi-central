import type { SettingsGoalItem } from "../../data/types/settings";
import { SiNativeTextAreaControl } from "./siNativeFormFields";
import "./SettingsGoalsForm.css";

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
    <div className="si-settings-goals-form">
      {items.map((item, index) => (
        <article
          key={item.department_id}
          className="si-settings-goals-form__card"
        >
          <div className="si-settings-goals-form__grid">
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
              <SiNativeTextAreaControl
                value={item.supporting_focus}
                aria-label="Foco de apoio"
                onChange={(supporting_focus) =>
                  updateItem(index, "supporting_focus", supporting_focus)
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
    <label className="si-settings-goals-form__field">
      <span className="si-settings-goals-form__label">{label}</span>
      {children}
    </label>
  );
}