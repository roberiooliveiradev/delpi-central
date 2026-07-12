import { SelectField } from "../../components/ui/SelectField";
import { mapSelectOptions } from "../../components/ui/selectTypes";
import { TmNativeTextField } from "../../components/ui/tmNativeFormFields";
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
      <TmNativeTextField
        id="tm-filial-codigo"
        label="Código TOTVS *"
        hint={TM_HELP_TOOLTIPS.filiais.codigo}
        required
        readOnly={editing}
        placeholder="ex.: 01"
        value={form.codigo_filial}
        onChange={(codigo_filial) => set({ codigo_filial: codigo_filial.trim() })}
      />
      <TmNativeTextField
        id="tm-filial-nome"
        label="Nome da unidade *"
        hint={TM_HELP_TOOLTIPS.filiais.nome}
        className="ds-filter-box--wide"
        required
        value={form.nome_filial}
        onChange={(nome_filial) => set({ nome_filial })}
      />
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
