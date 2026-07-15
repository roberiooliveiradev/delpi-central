import type { OptionsData } from "../../data/api/transformometroApi";
import { SelectField } from "../../components/ui/SelectField";
import { mapSelectOptions } from "../../components/ui/selectTypes";
import { TmNativeTextField } from "../../components/ui/tmNativeFormFields";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { InvestimentoFormState } from "./investimentoForm";
import { DS_FILTERS_ROW, DS_FILTER_BOX_WIDE_MOD } from "../../components/filterChrome";

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
    <div className={DS_FILTERS_ROW}>
      <SelectField
        id={`${idPrefix}-tipo`}
        label="Tipo"
        hint={I.tipo}
        value={form.tipo_investimento}
        onChange={(tipo) => set({ tipo_investimento: tipo })}
        options={mapSelectOptions(options.tipo_investimento)}
      />
      <TmNativeTextField id={`${idPrefix}-desc`} label="Descrição *" hint={I.descricao} className={DS_FILTER_BOX_WIDE_MOD} required value={form.descricao_item} onChange={(descricao_item) => set({ descricao_item })} />
      <TmNativeTextField label="Qtd" hint={I.quantidade} type="number" min={0} step="any" value={form.quantidade} onChange={(quantidade) => set({ quantidade: Number(quantidade) })} />
      <TmNativeTextField label="Valor unit. (R$)" hint={I.valorUnitario} type="number" min={0} step="any" value={form.valor_unitario} onChange={(valor_unitario) => set({ valor_unitario: Number(valor_unitario) })} />
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
      <TmNativeTextField label="Data" hint={I.data} type="date" value={form.data_investimento} onChange={(data_investimento) => set({ data_investimento })} />
      <TmNativeTextField label="Meses vigência" hint={I.mesesVigencia} type="number" min={1} step={1} placeholder="Opcional" value={form.meses_vigencia} onChange={(meses_vigencia) => set({ meses_vigencia })} />
    </div>
  );
}
