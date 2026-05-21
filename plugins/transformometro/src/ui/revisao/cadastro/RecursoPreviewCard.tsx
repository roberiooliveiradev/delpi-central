import type { RecursoCompartilhado } from "../../../data/api/transformometroApi";
import { toDateInputValue } from "../../../utils/dateInputs";
import { labelCriterioRateio } from "../../../utils/catalogLabels";
import { formatCurrency } from "../../../utils/format";

type Props = {
  recurso: RecursoCompartilhado;
};

export function RecursoPreviewCard({ recurso }: Props) {
  return (
    <div className="ds-resource-preview" role="region" aria-label="Dados do recurso selecionado">
      <p className="ds-resource-preview__title">
        {recurso.codigo_recurso} — {recurso.nome_recurso}
      </p>
      <dl className="ds-resource-preview__grid">
        <div>
          <dt>Categoria</dt>
          <dd>{recurso.categoria_recurso || "—"}</dd>
        </div>
        <div>
          <dt>Fornecedor</dt>
          <dd>{recurso.fornecedor || "—"}</dd>
        </div>
        <div>
          <dt>Tipo de custo</dt>
          <dd>{recurso.tipo_custo}</dd>
        </div>
        <div>
          <dt>Recorrência</dt>
          <dd>{recurso.recorrencia}</dd>
        </div>
        <div>
          <dt>Valor recorrente</dt>
          <dd>{formatCurrency(recurso.valor_total_recorrente)}/mês</dd>
        </div>
        <div>
          <dt>Rateio</dt>
          <dd>{labelCriterioRateio(recurso.criterio_rateio)}</dd>
        </div>
        <div>
          <dt>Status</dt>
          <dd>{recurso.status_recurso}</dd>
        </div>
        <div>
          <dt>Centro de custo</dt>
          <dd>{recurso.centro_custo || "—"}</dd>
        </div>
        <div>
          <dt>Vigência catálogo</dt>
          <dd>
            {toDateInputValue(recurso.data_inicio_vigencia) || "…"} →{" "}
            {toDateInputValue(recurso.data_fim_vigencia) || "aberta"}
          </dd>
        </div>
        {recurso.observacoes ? (
          <div className="ds-resource-preview__full">
            <dt>Observações</dt>
            <dd>{recurso.observacoes}</dd>
          </div>
        ) : null}
      </dl>
    </div>
  );
}
