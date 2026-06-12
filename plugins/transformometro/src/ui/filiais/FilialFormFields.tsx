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
        <label htmlFor="tm-filial-codigo">Código TOTVS *</label>
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
        <label htmlFor="tm-filial-nome">Nome da filial *</label>
        <input
          id="tm-filial-nome"
          required
          value={form.nome_filial}
          onChange={(e) => set({ nome_filial: e.target.value })}
        />
      </div>
      <div className="ds-filter-box">
        <label htmlFor="tm-filial-status">Status *</label>
        <select
          id="tm-filial-status"
          value={form.status_filial}
          onChange={(e) => set({ status_filial: e.target.value })}
        >
          {(options.status_filial ?? ["ativo", "inativo"]).map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
