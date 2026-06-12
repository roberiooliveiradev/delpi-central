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
        <label htmlFor="tm-setor-codigo">Código de negócio *</label>
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
        <label htmlFor="tm-setor-nome">Nome do setor *</label>
        <input
          id="tm-setor-nome"
          required
          value={form.nome_setor}
          onChange={(e) => set({ nome_setor: e.target.value })}
        />
      </div>
      <div className="ds-filter-box">
        <label htmlFor="tm-setor-status">Status *</label>
        <select
          id="tm-setor-status"
          value={form.status_setor}
          onChange={(e) => set({ status_setor: e.target.value })}
        >
          {(options.status_setor ?? ["ativo", "inativo"]).map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </select>
      </div>
      <div className="ds-filter-box ds-filter-box--wide">
        <span className="ds-filter-box__label">Filiais vinculadas *</span>
        <div className="ds-filters-row">
          {options.filiais.map((filial) => (
            <label key={filial.id} className="ds-filter-box ds-filter-box--checkbox">
              <input
                type="checkbox"
                checked={form.filiais.includes(filial.id)}
                onChange={() => toggleFilial(filial.id)}
              />
              {filial.id} — {filial.label}
            </label>
          ))}
        </div>
      </div>
    </div>
  );
}
