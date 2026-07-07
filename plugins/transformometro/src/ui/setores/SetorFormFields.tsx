import { FieldLabel } from "@delpi/plugin-ui";
import { SelectField } from "../../components/ui/SelectField";
import { mapSelectOptions } from "../../components/ui/selectTypes";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { OptionsData } from "../../data/api/transformometroApi";
import type { SetorFormState } from "./setorCatalogForm";

type Props = {
  form: SetorFormState;
  options: OptionsData;
  editing: boolean;
  onChange: (next: SetorFormState) => void;
};

export function SetorFormFields({ form, options, editing, onChange }: Props) {
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
      <div className="ds-filter-box">
        <label htmlFor="tm-setor-codigo">
          <FieldLabel className="tm-field__label" label="Código de negócio *" hint={TM_HELP_TOOLTIPS.setores.codigo} />
        </label>
        <input
          id="tm-setor-codigo"
          required
          readOnly={editing}
          placeholder="ex.: engenharia"
          value={form.codigo_setor}
          onChange={(e) => set({ codigo_setor: e.target.value.toLowerCase() })}
        />
      </div>
      <div className="ds-filter-box ds-filter-box--wide">
        <label htmlFor="tm-setor-nome">
          <FieldLabel className="tm-field__label" label="Nome do departamento *" hint={TM_HELP_TOOLTIPS.setores.nome} />
        </label>
        <input
          id="tm-setor-nome"
          required
          value={form.nome_setor}
          onChange={(e) => set({ nome_setor: e.target.value })}
        />
      </div>
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
            <label key={filial.id} className="tm-inst-setor-option ds-check-label">
              <input
                type="checkbox"
                checked={form.filiais.includes(filial.id)}
                onChange={() => toggleFilial(filial.id)}
              />
              <span>
                {filial.id} — {filial.label}
              </span>
            </label>
          ))}
        </div>
      </div>
    </div>
  );
}
