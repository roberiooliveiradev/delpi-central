import type { OptionsData } from "../../data/api/transformometroApi";
import { labelBaseCompetencia, labelCriterioRateio } from "../../utils/catalogLabels";
import type { RecursoCatalogFormState } from "./recursoCatalogForm";

const DEFAULT_BASE_COMPETENCIA_OPTIONS = ["mensal_cheio", "proporcional_dias"];

type Props = {
  form: RecursoCatalogFormState;
  options: OptionsData;
  onChange: (value: RecursoCatalogFormState) => void;
  submitLabel: string;
};

export function RecursoCatalogFormFields({ form, options, onChange, submitLabel }: Props) {
  const baseCompetenciaOptions = options.base_competencia_recurso?.length
    ? options.base_competencia_recurso
    : DEFAULT_BASE_COMPETENCIA_OPTIONS;

  return (
    <>
      <div className="ds-filters-row">
        <label className="ds-filter-box ds-filter-box--wide">
          Nome *
          <input
            required
            value={form.nome_recurso}
            onChange={(e) => onChange({ ...form, nome_recurso: e.target.value })}
          />
        </label>
        <label className="ds-filter-box">
          Categoria
          <select
            value={form.categoria_recurso}
            onChange={(e) => onChange({ ...form, categoria_recurso: e.target.value })}
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
          Fornecedor
          <input
            value={form.fornecedor}
            onChange={(e) => onChange({ ...form, fornecedor: e.target.value })}
          />
        </label>
        <label className="ds-filter-box">
          Tipo de custo *
          <select
            value={form.tipo_custo}
            onChange={(e) => onChange({ ...form, tipo_custo: e.target.value })}
          >
            {(options.tipo_custo ?? ["fixo", "variavel", "assinatura", "licenca"]).map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
        <label className="ds-filter-box">
          Recorrência *
          <select
            value={form.recorrencia}
            onChange={(e) => onChange({ ...form, recorrencia: e.target.value })}
          >
            {options.recorrencias.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </label>
        <label className="ds-filter-box">
          Critério de rateio *
          <select
            value={form.criterio_rateio}
            onChange={(e) => onChange({ ...form, criterio_rateio: e.target.value })}
          >
            {options.criterio_rateio.map((c) => (
              <option key={c} value={c}>
                {labelCriterioRateio(c)}
              </option>
            ))}
          </select>
        </label>
        <label className="ds-filter-box">
          Base de competência *
          <select
            value={form.base_competencia}
            onChange={(e) => onChange({ ...form, base_competencia: e.target.value })}
          >
            {baseCompetenciaOptions.map((base) => (
              <option key={base} value={base}>
                {labelBaseCompetencia(base)}
              </option>
            ))}
          </select>
        </label>
        <label className="ds-filter-box">
          Status *
          <select
            value={form.status_recurso}
            onChange={(e) => onChange({ ...form, status_recurso: e.target.value })}
          >
            {options.status_recurso.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label className="ds-filter-box">
          Centro de custo
          <input
            value={form.centro_custo}
            onChange={(e) => onChange({ ...form, centro_custo: e.target.value })}
          />
        </label>
        <label className="ds-filter-box">
          Início vigência do recurso
          <input
            type="date"
            value={form.data_inicio_vigencia}
            onChange={(e) => onChange({ ...form, data_inicio_vigencia: e.target.value })}
          />
        </label>
        <label className="ds-filter-box">
          Fim vigência do recurso
          <input
            type="date"
            value={form.data_fim_vigencia}
            onChange={(e) => onChange({ ...form, data_fim_vigencia: e.target.value })}
          />
        </label>
      </div>
      <label className="ds-filter-box ds-filter-box--wide">
        Observações
        <input
          value={form.observacoes}
          onChange={(e) => onChange({ ...form, observacoes: e.target.value })}
        />
      </label>
      <button type="submit" className="ds-primary-btn">
        {submitLabel}
      </button>
    </>
  );
}
