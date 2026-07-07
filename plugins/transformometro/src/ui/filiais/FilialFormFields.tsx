import { FieldLabel } from "@delpi/plugin-ui";
import { SelectField } from "../../components/ui/SelectField";
import { mapSelectOptions } from "../../components/ui/selectTypes";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { OptionsData } from "../../data/api/transformometroApi";
import type { FilialFormState } from "./filialCatalogForm";

type Props = {
  form: FilialFormState;
  options: OptionsData;
  editing: boolean;
  onChange: (next: FilialFormState) => void;
};

export function FilialFormFields({ form, options, editing, onChange }: Props) {
  const set = (patch: Partial<FilialFormState>) => onChange({ ...form, ...patch });

  return (
    <div className="ds-filters-row ds-filters-row--extended">
      <div className="ds-filter-box">
        <label htmlFor="tm-filial-codigo">
          <FieldLabel className="tm-field__label" label="Código TOTVS *" hint={TM_HELP_TOOLTIPS.filiais.codigo} />
        </label>
        <input
          id="tm-filial-codigo"
          required
          readOnly={editing}
          placeholder="ex.: 01"
          value={form.codigo_filial}
          onChange={(e) => set({ codigo_filial: e.target.value.trim() })}
        />
      </div>
      <div className="ds-filter-box ds-filter-box--wide">
        <label htmlFor="tm-filial-nome">
          <FieldLabel className="tm-field__label" label="Nome da unidade *" hint={TM_HELP_TOOLTIPS.filiais.nome} />
        </label>
        <input
          id="tm-filial-nome"
          required
          value={form.nome_filial}
          onChange={(e) => set({ nome_filial: e.target.value })}
        />
      </div>
      <SelectField
        id="tm-filial-status"
        label="Status *"
        hint={TM_HELP_TOOLTIPS.filiais.status}
        value={form.status_filial}
        onChange={(status) => set({ status_filial: status })}
        options={mapSelectOptions(options.status_filial ?? ["ativo", "inativo"])}
      />
    </div>
  );
}
