import { SelectField } from "../../components/ui/SelectField";
import { mapSelectOptions } from "../../components/ui/selectTypes";
import { TmNativeTextField } from "../../components/ui/tmNativeFormFields";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { OptionsData } from "../../data/api/transformometroApi";
import type { FilialFormState } from "./filialCatalogForm";
import { DS_FILTERS_ROW_EXTENDED, DS_FILTER_BOX_WIDE_MOD } from "../../components/filterChrome";

type Props = {
  form: FilialFormState;
  options: OptionsData;
  editing: boolean;
  onChange: (next: FilialFormState) => void;
};

export function FilialFormFields({ form, options, editing, onChange }: Props) {
  const set = (patch: Partial<FilialFormState>) => onChange({ ...form, ...patch });

  return (
    <div className={DS_FILTERS_ROW_EXTENDED}>
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
        className={DS_FILTER_BOX_WIDE_MOD}
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
