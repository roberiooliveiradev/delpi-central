import { FieldLabel } from "@delpi/plugin-ui";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { Processo } from "../../data/api/transformometroApi";

const P = TM_HELP_TOOLTIPS.processos;

type Props = {
  processo: Processo;
};

export function ProcessoReadView({ processo }: Props) {
  return (
    <>
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
      </dl>
      {processo.objetivo_processo ? (
        <p className="ds-hint">
          <FieldLabel className="tm-field__label" label="Objetivo" hint={P.objetivo} />: {processo.objetivo_processo}
        </p>
      ) : null}
      {processo.descricao_processo ? (
        <p className="ds-hint">
          <FieldLabel className="tm-field__label" label="Descrição" hint={P.descricao} />: {processo.descricao_processo}
        </p>
      ) : null}
    </>
  );
}
