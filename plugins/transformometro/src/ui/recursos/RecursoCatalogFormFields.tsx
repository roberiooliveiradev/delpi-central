import { SelectField } from "../../components/ui/SelectField";
import { mapSelectOptionsFromItems } from "../../components/ui/selectTypes";
import { TmNativeTextField } from "../../components/ui/tmNativeFormFields";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { OptionsData } from "../../data/api/transformometroApi";
import {
  labelBaseCompetencia,
  labelCriterioRateio,
  labelEscopoRecurso,
} from "../../utils/catalogLabels";
import type { RecursoCatalogFormState } from "./recursoCatalogForm";
import { DS_FILTERS_ROW, DS_FILTER_BOX_WIDE_MOD } from "../../components/filterChrome";

const R = TM_HELP_TOOLTIPS.recursos;

const DEFAULT_BASE_COMPETENCIA_OPTIONS = ["mensal_cheio", "proporcional_dias"];

type Props = {
  form: RecursoCatalogFormState;
  options: OptionsData;
  onChange: (value: RecursoCatalogFormState) => void;
  submitLabel: string;
  hideSubmit?: boolean;
};

const DEFAULT_ESCOPO_RECURSO_OPTIONS = ["empresa", "filial", "setor"];

export function RecursoCatalogFormFields({
  form,
  options,
  onChange,
  submitLabel,
  hideSubmit = false,
}: Props) {
  const baseCompetenciaOptions = options.base_competencia_recurso?.length
    ? options.base_competencia_recurso
    : DEFAULT_BASE_COMPETENCIA_OPTIONS;
  const escopoOptions = options.escopo_recurso?.length
    ? options.escopo_recurso
    : DEFAULT_ESCOPO_RECURSO_OPTIONS;

  return (
    <>
      <div className={DS_FILTERS_ROW}>
        <TmNativeTextField label="Nome *" hint={R.nome} className={DS_FILTER_BOX_WIDE_MOD} required value={form.nome_recurso} onChange={(nome_recurso) => onChange({ ...form, nome_recurso })} />
        <SelectField
          label="Categoria"
          hint={R.categoria}
          value={form.categoria_recurso}
          onChange={(categoria) => onChange({ ...form, categoria_recurso: categoria })}
          allowEmpty
          options={mapSelectOptionsFromItems(
            options.categorias,
            (c) => c,
            (c) => c
          )}
        />
        <TmNativeTextField label="Fornecedor" hint={R.fornecedor} value={form.fornecedor} onChange={(fornecedor) => onChange({ ...form, fornecedor })} />
        <SelectField
          label="Tipo de custo *"
          hint={R.tipoCusto}
          value={form.tipo_custo}
          onChange={(tipo) => onChange({ ...form, tipo_custo: tipo })}
          options={mapSelectOptionsFromItems(
            options.tipo_custo ?? ["fixo", "variavel", "assinatura", "licenca"],
            (t) => t,
            (t) => t
          )}
        />
        <SelectField
          label="Recorrência *"
          hint={R.recorrencia}
          value={form.recorrencia}
          onChange={(recorrencia) => onChange({ ...form, recorrencia })}
          options={mapSelectOptionsFromItems(
            options.recorrencias,
            (r) => r,
            (r) => r
          )}
        />
        <SelectField
          label="Critério de rateio *"
          hint={R.criterioRateio}
          value={form.criterio_rateio}
          onChange={(criterio) => onChange({ ...form, criterio_rateio: criterio })}
          options={mapSelectOptionsFromItems(
            options.criterio_rateio,
            (c) => c,
            (c) => labelCriterioRateio(c)
          )}
        />
        <SelectField
          label="Escopo de rateio *"
          hint={R.escopo}
          value={form.escopo_recurso}
          onChange={(escopo) => onChange({ ...form, escopo_recurso: escopo })}
          options={mapSelectOptionsFromItems(
            escopoOptions,
            (escopo) => escopo,
            (escopo) => labelEscopoRecurso(escopo)
          )}
        />
        <SelectField
          label="Base de competência *"
          hint={R.baseCompetencia}
          value={form.base_competencia}
          onChange={(base) => onChange({ ...form, base_competencia: base })}
          options={mapSelectOptionsFromItems(
            baseCompetenciaOptions,
            (base) => base,
            (base) => labelBaseCompetencia(base)
          )}
        />
        <SelectField
          label="Status *"
          hint={R.status}
          value={form.status_recurso}
          onChange={(status) => onChange({ ...form, status_recurso: status })}
          options={mapSelectOptionsFromItems(
            options.status_recurso,
            (s) => s,
            (s) => s
          )}
        />
        <TmNativeTextField label="Centro de custo" hint={R.centroCusto} value={form.centro_custo} onChange={(centro_custo) => onChange({ ...form, centro_custo })} />
        <TmNativeTextField label="Início vigência do recurso" hint={R.inicioVigencia} type="date" value={form.data_inicio_vigencia} onChange={(data_inicio_vigencia) => onChange({ ...form, data_inicio_vigencia })} />
        <TmNativeTextField label="Fim vigência do recurso" hint={R.fimVigencia} type="date" value={form.data_fim_vigencia} onChange={(data_fim_vigencia) => onChange({ ...form, data_fim_vigencia })} />
      </div>
      <TmNativeTextField label="Observações" hint={TM_HELP_TOOLTIPS.columns.observacoes} className={DS_FILTER_BOX_WIDE_MOD} value={form.observacoes} onChange={(observacoes) => onChange({ ...form, observacoes })} />
      {hideSubmit ? null : (
        <button type="submit" className="ds-primary-btn">
          {submitLabel}
        </button>
      )}
    </>
  );
}
