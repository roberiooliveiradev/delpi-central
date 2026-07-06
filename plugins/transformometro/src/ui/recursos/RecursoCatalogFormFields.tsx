import { FieldLabel } from "../../components/HelpTooltip";
import { SelectField } from "../../components/ui/SelectField";
import { mapSelectOptionsFromItems } from "../../components/ui/selectTypes";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { OptionsData } from "../../data/api/transformometroApi";
import {
  labelBaseCompetencia,
  labelCriterioRateio,
  labelEscopoRecurso,
} from "../../utils/catalogLabels";
import type { RecursoCatalogFormState } from "./recursoCatalogForm";

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
      <div className="ds-filters-row">
        <label className="ds-filter-box ds-filter-box--wide">
          <FieldLabel label="Nome *" hint={R.nome} />
          <input
            required
            value={form.nome_recurso}
            onChange={(e) => onChange({ ...form, nome_recurso: e.target.value })}
          />
        </label>
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
        <label className="ds-filter-box">
          <FieldLabel label="Fornecedor" hint={R.fornecedor} />
          <input
            value={form.fornecedor}
            onChange={(e) => onChange({ ...form, fornecedor: e.target.value })}
          />
        </label>
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
        <label className="ds-filter-box">
          <FieldLabel label="Centro de custo" hint={R.centroCusto} />
          <input
            value={form.centro_custo}
            onChange={(e) => onChange({ ...form, centro_custo: e.target.value })}
          />
        </label>
        <label className="ds-filter-box">
          <FieldLabel label="Início vigência do recurso" hint={R.inicioVigencia} />
          <input
            type="date"
            value={form.data_inicio_vigencia}
            onChange={(e) => onChange({ ...form, data_inicio_vigencia: e.target.value })}
          />
        </label>
        <label className="ds-filter-box">
          <FieldLabel label="Fim vigência do recurso" hint={R.fimVigencia} />
          <input
            type="date"
            value={form.data_fim_vigencia}
            onChange={(e) => onChange({ ...form, data_fim_vigencia: e.target.value })}
          />
        </label>
      </div>
      <label className="ds-filter-box ds-filter-box--wide">
        <FieldLabel label="Observações" hint={TM_HELP_TOOLTIPS.columns.observacoes} />
        <input
          value={form.observacoes}
          onChange={(e) => onChange({ ...form, observacoes: e.target.value })}
        />
      </label>
      {hideSubmit ? null : (
        <button type="submit" className="ds-primary-btn">
          {submitLabel}
        </button>
      )}
    </>
  );
}
