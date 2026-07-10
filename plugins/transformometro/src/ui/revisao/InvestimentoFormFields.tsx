import type { OptionsData } from "../../data/api/transformometroApi";
import { FieldLabel } from "@delpi/plugin-ui/index";
import { SelectField } from "../../components/ui/SelectField";
import { mapSelectOptions } from "../../components/ui/selectTypes";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { InvestimentoFormState } from "./investimentoForm";

const I = TM_HELP_TOOLTIPS.investimentos;

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
      <SelectField
        id={`${idPrefix}-tipo`}
        label="Tipo"
        hint={I.tipo}
        value={form.tipo_investimento}
        onChange={(tipo) => set({ tipo_investimento: tipo })}
        options={mapSelectOptions(options.tipo_investimento)}
      />
      <label className="ds-filter-box ds-filter-box--wide">
        <FieldLabel className="tm-field__label" label="Descrição *" hint={I.descricao} />
        <input
          id={`${idPrefix}-desc`}
          required
          value={form.descricao_item}
          onChange={(e) => set({ descricao_item: e.target.value })}
        />
      </label>
      <label className="ds-filter-box">
        <FieldLabel className="tm-field__label" label="Qtd" hint={I.quantidade} />
        <input
          type="number"
          min={0}
          step="any"
          value={form.quantidade}
          onChange={(e) => set({ quantidade: Number(e.target.value) })}
        />
      </label>
      <label className="ds-filter-box">
        <FieldLabel className="tm-field__label" label="Valor unit. (R$)" hint={I.valorUnitario} />
        <input
          type="number"
          min={0}
          step="any"
          value={form.valor_unitario}
          onChange={(e) => set({ valor_unitario: Number(e.target.value) })}
        />
      </label>
      <SelectField
        label="Recorrência"
        hint={I.recorrencia}
        value={form.recorrencia}
        onChange={(recorrencia) => set({ recorrencia })}
        options={mapSelectOptions(options.recorrencias)}
      />
      <SelectField
        label="Categoria"
        hint={I.categoria}
        value={form.categoria_investimento}
        onChange={(categoria) => set({ categoria_investimento: categoria })}
        allowEmpty
        options={mapSelectOptions(options.categorias)}
      />
      <label className="ds-filter-box">
        <FieldLabel className="tm-field__label" label="Data" hint={I.data} />
        <input
          type="date"
          value={form.data_investimento}
          onChange={(e) => set({ data_investimento: e.target.value })}
        />
      </label>
      <label className="ds-filter-box">
        <FieldLabel className="tm-field__label" label="Meses vigência" hint={I.mesesVigencia} />
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
