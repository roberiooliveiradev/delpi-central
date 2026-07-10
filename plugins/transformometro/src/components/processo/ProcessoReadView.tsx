import { FieldLabel } from "@delpi/plugin-ui/index";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { Processo } from "../../data/api/transformometroApi";
import { formatProcessoEscopoRead, hasProcessoEscopo } from "../../ui/processos/processoEscopo";

const P = TM_HELP_TOOLTIPS.processos;

type Props = {
  processo: Processo;
  activeFilialCount?: number;
};

export function ProcessoReadView({ processo, activeFilialCount = 1 }: Props) {
  const escopo = hasProcessoEscopo({
    todas_filiais_ativas: Boolean(processo.todas_filiais_ativas),
    filial_ids: processo.filial_ids ?? (processo.filial_id ? [processo.filial_id] : []),
    setor_ids: processo.setor_ids ?? (processo.setor_id ? [processo.setor_id] : []),
  })
    ? formatProcessoEscopoRead(processo, activeFilialCount)
    : null;

  return (
    <div className="tm-processo-read-view">
      <dl className="ds-dl-grid">
        <div>
          <dt><FieldLabel className="tm-field__label" label="Código" hint={P.codigo} /></dt>
          <dd>{processo.codigo_processo}</dd>
        </div>
        <div>
          <dt><FieldLabel className="tm-field__label" label="Nome" hint={P.nome} /></dt>
          <dd>{processo.nome_processo}</dd>
        </div>
        <div>
          <dt><FieldLabel className="tm-field__label" label="Status" hint={P.status} /></dt>
          <dd>{processo.status_processo}</dd>
        </div>
        {processo.familia_processo ? (
          <div>
            <dt><FieldLabel className="tm-field__label" label="Família" hint={P.familia} /></dt>
            <dd>{processo.familia_processo}</dd>
          </div>
        ) : null}
        {processo.agrupador_ferramenta ? (
          <div>
            <dt><FieldLabel className="tm-field__label" label="Agrupador" hint={P.agrupadorFerramenta} /></dt>
            <dd>{processo.agrupador_ferramenta}</dd>
          </div>
        ) : null}
        {processo.gestor_responsavel ? (
          <div>
            <dt><FieldLabel className="tm-field__label" label="Gestor" hint={P.gestor} /></dt>
            <dd>{processo.gestor_responsavel}</dd>
          </div>
        ) : null}
        {escopo ? (
          <>
            <div>
              <dt><FieldLabel className="tm-field__label" label="Unidades" hint={P.unidade} /></dt>
              <dd>{escopo.unidades}</dd>
            </div>
            <div>
              <dt><FieldLabel className="tm-field__label" label="Departamentos" hint={P.setor} /></dt>
              <dd>{escopo.departamentos}</dd>
            </div>
          </>
        ) : null}
      </dl>
      {processo.objetivo_processo ? (
        <div className="tm-processo-read-view__block">
          <FieldLabel className="tm-field__label" label="Objetivo" hint={P.objetivo} />
          <p className="tm-processo-read-view__text">{processo.objetivo_processo}</p>
        </div>
      ) : null}
      {processo.descricao_processo ? (
        <div className="tm-processo-read-view__block">
          <FieldLabel className="tm-field__label" label="Descrição" hint={P.descricao} />
          <p className="tm-processo-read-view__text">{processo.descricao_processo}</p>
        </div>
      ) : null}
    </div>
  );
}
