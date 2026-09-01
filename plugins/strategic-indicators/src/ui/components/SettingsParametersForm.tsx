import type { SettingsParameterItem } from "../../data/types/settings";
import { SI_HELP } from "../../content/helpTooltips";
import { SiAdminFormField } from "./SiAdminFormField";
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
            <SiAdminFormField label="Chave" hint={SI_HELP.system.parameterKey}>
              <SiNativeTextControl
                value={item.key}
                onChange={(value) => updateItem(index, "key", value)}
              />
            </SiAdminFormField>

            <SiAdminFormField label="Rótulo" hint={SI_HELP.system.parameterLabel}>
              <SiNativeTextControl
                value={item.label}
                onChange={(value) => updateItem(index, "label", value)}
              />
            </SiAdminFormField>

            <SiAdminFormField label="Valor" hint={SI_HELP.system.parameterValue}>
              <SiNativeTextControl
                value={item.value}
                onChange={(value) => updateItem(index, "value", value)}
              />
            </SiAdminFormField>
          </div>
        </article>
      ))}
    </div>
  );
}
