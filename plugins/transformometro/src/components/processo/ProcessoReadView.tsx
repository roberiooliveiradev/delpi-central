import type { Processo } from "../../data/api/transformometroApi";

type Props = {
  processo: Processo;
};

export function ProcessoReadView({ processo }: Props) {
  return (
    <>
      <dl className="ds-dl-grid">
        <div>
          <dt>Código</dt>
          <dd>{processo.codigo_processo}</dd>
        </div>
        <div>
          <dt>Nome</dt>
          <dd>{processo.nome_processo}</dd>
        </div>
        <div>
          <dt>Status</dt>
          <dd>{processo.status_processo}</dd>
        </div>
        {processo.familia_processo ? (
          <div>
            <dt>Família</dt>
            <dd>{processo.familia_processo}</dd>
          </div>
        ) : null}
        {processo.agrupador_ferramenta ? (
          <div>
            <dt>Agrupador</dt>
            <dd>{processo.agrupador_ferramenta}</dd>
          </div>
        ) : null}
        {processo.gestor_responsavel ? (
          <div>
            <dt>Gestor</dt>
            <dd>{processo.gestor_responsavel}</dd>
          </div>
        ) : null}
      </dl>
      {processo.objetivo_processo ? (
        <p className="ds-hint">
          <strong>Objetivo:</strong> {processo.objetivo_processo}
        </p>
      ) : null}
      {processo.descricao_processo ? (
        <p className="ds-hint">
          <strong>Descrição:</strong> {processo.descricao_processo}
        </p>
      ) : null}
    </>
  );
}
