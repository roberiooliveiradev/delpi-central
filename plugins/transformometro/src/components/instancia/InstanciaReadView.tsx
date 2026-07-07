import { FieldLabel } from "@delpi/plugin-ui";
import { MelhoriaFaseBadge } from "../../components/melhoria/MelhoriaFaseBadge";
import { MelhoriaFasePipeline } from "../../components/melhoria/MelhoriaFasePipeline";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { OptionsData, ProcessoInstancia } from "../../data/api/transformometroApi";
import { renderTableStatus } from "../../utils/tablePresentation";

const I = TM_HELP_TOOLTIPS.instancias;

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
    <div className="tm-instancia-read">
      <MelhoriaFasePipeline currentFase={instancia.fase_melhoria} hint={I.fase} />
      <dl className="ds-dl-grid">
        <div>
          <dt><FieldLabel className="tm-field__label" label="Unidade" hint={I.colunaUnidade} /></dt>
          <dd>{unidade}</dd>
        </div>
        <div>
          <dt><FieldLabel className="tm-field__label" label="Status" hint={I.status} /></dt>
          <dd>{renderTableStatus(instancia.status_instancia ?? "ativo")}</dd>
        </div>
        <div>
          <dt><FieldLabel className="tm-field__label" label="Fase" hint={I.fase} /></dt>
          <dd>
            <MelhoriaFaseBadge fase={instancia.fase_melhoria} />
          </dd>
        </div>
        <div>
          <dt><FieldLabel className="tm-field__label" label="Departamentos" hint={I.setores} /></dt>
          <dd>{formatSetores(instancia) || "—"}</dd>
        </div>
        <div>
          <dt><FieldLabel className="tm-field__label" label="Título" hint={I.rotulo} /></dt>
          <dd>{instancia.rotulo_instancia ?? "—"}</dd>
        </div>
        {instancia.resumo_melhoria?.trim() ? (
          <div className="ds-dl-grid__full">
            <dt><FieldLabel className="tm-field__label" label="Resumo" hint={I.resumo} /></dt>
            <dd>{instancia.resumo_melhoria.trim()}</dd>
          </div>
        ) : null}
        {instancia.todas_filiais_ativas && options.filiais.length > 1 ? (
          <div>
            <dt><FieldLabel className="tm-field__label" label="Consolidado" hint={I.multiplicadorConsolidado} /></dt>
            <dd>Economia e horas × {options.filiais.length} unidades</dd>
          </div>
        ) : null}
      </dl>
    </div>
  );
}
