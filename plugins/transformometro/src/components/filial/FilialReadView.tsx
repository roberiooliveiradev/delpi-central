import { FieldLabel } from "@delpi/plugin-ui/index";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { Filial } from "../../data/api/transformometroApi";

const F = TM_HELP_TOOLTIPS.filiais;

type Props = {
  filial: Filial;
};

export function FilialReadView({ filial }: Props) {
  return (
    <dl className="ds-dl-grid">
      <div>
        <dt><FieldLabel className="tm-field__label" label="Código TOTVS" hint={F.codigo} /></dt>
        <dd>{filial.codigo_filial ?? filial.filial_id}</dd>
      </div>
      <div>
        <dt><FieldLabel className="tm-field__label" label="Nome" hint={F.nome} /></dt>
        <dd>{filial.nome_filial}</dd>
      </div>
      <div>
        <dt><FieldLabel className="tm-field__label" label="Status" hint={F.status} /></dt>
        <dd>{filial.status_filial ?? "ativo"}</dd>
      </div>
    </dl>
  );
}
