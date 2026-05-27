import type { OptionsData } from "../../data/api/transformometroApi";
import type { InvestimentoFormState } from "./investimentoForm";

type Props = {
  form: InvestimentoFormState;
  options: OptionsData;
  onChange: (next: InvestimentoFormState) => void;
  idPrefix?: string;
};

export function InvestimentoFormFields({ form, options, onChange, idPrefix = "tm-inv" }: Props) {
  const set = (patch: Partial<InvestimentoFormState>) => onChange({ ...form, ...patch });

  return (
    <div className="ds-filters-row">
      <label className="ds-filter-box">
        Tipo
        <select
          id={`${idPrefix}-tipo`}
          value={form.tipo_investimento}
          onChange={(e) => set({ tipo_investimento: e.target.value })}
        >
          {options.tipo_investimento.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </label>
      <label className="ds-filter-box ds-filter-box--wide">
        Descrição *
        <input
          id={`${idPrefix}-desc`}
          required
          value={form.descricao_item}
          onChange={(e) => set({ descricao_item: e.target.value })}
        />
      </label>
      <label className="ds-filter-box">
        Qtd
        <input
          type="number"
          min={0}
          step="any"
          value={form.quantidade}
          onChange={(e) => set({ quantidade: Number(e.target.value) })}
        />
      </label>
      <label className="ds-filter-box">
        Valor unit. (R$)
        <input
          type="number"
          min={0}
          step="any"
          value={form.valor_unitario}
          onChange={(e) => set({ valor_unitario: Number(e.target.value) })}
        />
      </label>
      <label className="ds-filter-box">
        Recorrência
        <select
          value={form.recorrencia}
          onChange={(e) => set({ recorrencia: e.target.value })}
        >
          {options.recorrencias.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
      </label>
      <label className="ds-filter-box">
        Categoria
        <select
          value={form.categoria_investimento}
          onChange={(e) => set({ categoria_investimento: e.target.value })}
        >
          <option value="">—</option>
          {options.categorias.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </label>
      <label className="ds-filter-box">
        Data
        <input
          type="date"
          value={form.data_investimento}
          onChange={(e) => set({ data_investimento: e.target.value })}
        />
      </label>
      <label className="ds-filter-box">
        Meses vigência
        <input
          type="number"
          min={1}
          step={1}
          placeholder="Opcional"
          value={form.meses_vigencia}
          onChange={(e) => set({ meses_vigencia: e.target.value })}
        />
      </label>
    </div>
  );
}
