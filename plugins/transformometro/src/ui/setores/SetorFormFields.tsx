import { FieldLabel, NativeCheckboxControl } from "@delpi/plugin-ui/index";
import { SelectField } from "../../components/ui/SelectField";
import { mapSelectOptions } from "../../components/ui/selectTypes";
import { TmNativeTextField } from "../../components/ui/tmNativeFormFields";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { OptionsData } from "../../data/api/transformometroApi";
import type { SetorFormState } from "./setorCatalogForm";

type Props = {
  form: SetorFormState;
  options: OptionsData;
  onChange: (next: SetorFormState) => void;
};

export function SetorFormFields({ form, options, onChange }: Props) {
  const set = (patch: Partial<SetorFormState>) => onChange({ ...form, ...patch });

  function toggleFilial(filialId: string) {
    const selected = new Set(form.filiais);
    if (selected.has(filialId)) {
      selected.delete(filialId);
    } else {
      selected.add(filialId);
    }
    set({ filiais: [...selected].sort() });
  }

  return (
    <div className="ds-filters-row ds-filters-row--extended">
      <TmNativeTextField id="tm-setor-codigo" label="Código de negócio *" hint={TM_HELP_TOOLTIPS.setores.codigo} required placeholder="ex.: engenharia" value={form.codigo_setor} onChange={(codigo_setor) => set({ codigo_setor: codigo_setor.toLowerCase() })} />
      <TmNativeTextField id="tm-setor-nome" label="Nome do departamento *" hint={TM_HELP_TOOLTIPS.setores.nome} className="ds-filter-box--wide" required value={form.nome_setor} onChange={(nome_setor) => set({ nome_setor })} />
      <SelectField
        id="tm-setor-status"
        label="Status *"
        hint={TM_HELP_TOOLTIPS.setores.status}
        value={form.status_setor}
        onChange={(status) => set({ status_setor: status })}
        options={mapSelectOptions(options.status_setor ?? ["ativo", "inativo"])}
      />
      <div className="ds-filter-box ds-filter-box--wide">
        <span className="ds-field-label">
          <FieldLabel className="tm-field__label"
            label="Unidades vinculadas *"
            hint={TM_HELP_TOOLTIPS.setores.unidadesVinculadas}
          />
        </span>
        <div className="tm-inst-setores-grid">
          {options.filiais.map((filial) => (
            <NativeCheckboxControl
              key={filial.id}
              className="tm-inst-setor-option ds-check-label"
              checked={form.filiais.includes(filial.id)}
              onChange={() => toggleFilial(filial.id)}
              label={filial.label}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
