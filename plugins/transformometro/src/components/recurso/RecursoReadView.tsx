import { FieldLabel } from "@delpi/plugin-ui/index";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { RecursoCompartilhado } from "../../data/api/transformometroApi";
import { labelBaseCompetencia, labelCriterioRateio, labelEscopoRecurso } from "../../utils/catalogLabels";
import { toDateInputValue } from "../../utils/dateInputs";
import { formatCurrency } from "../../utils/format";

const C = TM_HELP_TOOLTIPS.columns;
const R = TM_HELP_TOOLTIPS.recursos;

type Props = {
  recurso: RecursoCompartilhado;
  vinculosAtivos?: number;
};

export function RecursoReadView({ recurso, vinculosAtivos }: Props) {
  const vigencia = `${toDateInputValue(recurso.data_inicio_vigencia) || "…"} → ${toDateInputValue(recurso.data_fim_vigencia) || "…"}`;

  return (
    <>
      <dl className="ds-dl-grid">
        <div>
          <dt><FieldLabel className="tm-field__label" label="Código" hint={C.codigo} /></dt>
          <dd>{recurso.codigo_recurso}</dd>
        </div>
        <div>
          <dt><FieldLabel className="tm-field__label" label="Nome" hint={R.nome} /></dt>
          <dd>{recurso.nome_recurso}</dd>
        </div>
        <div>
          <dt><FieldLabel className="tm-field__label" label="Status" hint={R.status} /></dt>
          <dd>{recurso.status_recurso}</dd>
        </div>
        <div>
          <dt><FieldLabel className="tm-field__label" label="Categoria" hint={R.categoria} /></dt>
          <dd>{recurso.categoria_recurso || "—"}</dd>
        </div>
        <div>
          <dt><FieldLabel className="tm-field__label" label="Fornecedor" hint={R.fornecedor} /></dt>
          <dd>{recurso.fornecedor || "—"}</dd>
        </div>
        <div>
          <dt><FieldLabel className="tm-field__label" label="Tipo / recorrência" hint={R.tipoCusto} /></dt>
          <dd>
            {recurso.tipo_custo} · {recurso.recorrencia}
          </dd>
        </div>
        <div>
          <dt><FieldLabel className="tm-field__label" label="Rateio" hint={R.criterioRateio} /></dt>
          <dd>{labelCriterioRateio(recurso.criterio_rateio)}</dd>
        </div>
        <div>
          <dt><FieldLabel className="tm-field__label" label="Escopo" hint={R.escopo} /></dt>
          <dd>{labelEscopoRecurso(recurso.escopo_recurso)}</dd>
        </div>
        <div>
          <dt><FieldLabel className="tm-field__label" label="Competência" hint={R.baseCompetencia} /></dt>
          <dd>{labelBaseCompetencia(recurso.base_competencia)}</dd>
        </div>
        <div>
          <dt><FieldLabel className="tm-field__label" label="Custo/mês vigente" hint={C.custoMesVigente} /></dt>
          <dd>{formatCurrency(recurso.valor_total_recorrente)}</dd>
        </div>
        {vinculosAtivos != null ? (
          <div>
            <dt><FieldLabel className="tm-field__label" label="Vínculos ativos" hint={C.ativoVinculo} /></dt>
            <dd>{vinculosAtivos}</dd>
          </div>
        ) : null}
        <div>
          <dt><FieldLabel className="tm-field__label" label="Vigência do recurso" hint={C.vigenciaRecurso} /></dt>
          <dd>{vigencia}</dd>
        </div>
      </dl>
      {recurso.observacoes ? (
        <p className="ds-hint">
          <FieldLabel className="tm-field__label" label="Observações" hint={C.observacoes} />: {recurso.observacoes}
        </p>
      ) : null}
    </>
  );
}
