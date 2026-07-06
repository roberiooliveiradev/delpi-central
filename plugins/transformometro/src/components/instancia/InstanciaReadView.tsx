import type { OptionsData, ProcessoInstancia } from "../../data/api/transformometroApi";

type Props = {
  instancia: ProcessoInstancia;
  options: OptionsData;
};

function formatSetores(instancia: ProcessoInstancia): string {
  if (instancia.setores?.length) {
    return instancia.setores
      .map((setor) => `${setor.codigo_setor ?? setor.setor_id} — ${setor.nome_setor ?? ""}`.trim())
      .join("; ");
  }
  return `${instancia.codigo_setor ?? instancia.setor_id ?? ""} — ${instancia.nome_setor ?? ""}`.trim();
}

export function InstanciaReadView({ instancia, options }: Props) {
  const unidade = instancia.todas_filiais_ativas
    ? `Todas as unidades ativas (${options.filiais.length})`
    : `${instancia.codigo_filial ?? instancia.filial_id} — ${instancia.nome_filial ?? ""}`.trim();

  return (
    <dl className="ds-dl-grid">
      <div>
        <dt>Unidade</dt>
        <dd>{unidade}</dd>
      </div>
      <div>
        <dt>Status</dt>
        <dd>{instancia.status_instancia ?? "ativo"}</dd>
      </div>
      <div>
        <dt>Setores</dt>
        <dd>{formatSetores(instancia) || "—"}</dd>
      </div>
      <div>
        <dt>Rótulo</dt>
        <dd>{instancia.rotulo_instancia ?? "—"}</dd>
      </div>
      {instancia.todas_filiais_ativas && options.filiais.length > 1 ? (
        <div>
          <dt>Consolidado</dt>
          <dd>Economia e horas × {options.filiais.length} unidades</dd>
        </div>
      ) : null}
    </dl>
  );
}
