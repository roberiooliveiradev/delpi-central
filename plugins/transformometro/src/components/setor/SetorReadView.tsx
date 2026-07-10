import { FieldLabel } from "@delpi/plugin-ui/index";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { Setor } from "../../data/api/transformometroApi";

const S = TM_HELP_TOOLTIPS.setores;

type Props = {
  setor: Setor;
  filialLabels: Map<string, string>;
};

export function SetorReadView({ setor, filialLabels }: Props) {
  const unidades =
    (setor.filiais ?? [])
      .map((filialId) => filialLabels.get(filialId) ?? "—")
      .join(", ") || "—";

  return (
    <>
      <dl className="ds-dl-grid">
        <div>
          <dt><FieldLabel className="tm-field__label" label="Código" hint={S.codigo} /></dt>
          <dd>{setor.codigo_setor ?? setor.setor_id}</dd>
        </div>
        <div>
          <dt><FieldLabel className="tm-field__label" label="Nome" hint={S.nome} /></dt>
          <dd>{setor.nome_setor}</dd>
        </div>
        <div>
          <dt><FieldLabel className="tm-field__label" label="Status" hint={S.status} /></dt>
          <dd>{setor.status_setor ?? "ativo"}</dd>
        </div>
      </dl>
      <p className="ds-hint">
        <FieldLabel className="tm-field__label" label="Unidades vinculadas" hint={S.unidadesVinculadas} />: {unidades}
      </p>
    </>
  );
}
