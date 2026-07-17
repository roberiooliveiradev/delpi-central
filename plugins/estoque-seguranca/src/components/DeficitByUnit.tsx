import type { DeficitByUnitRow } from "../types/safetyStock";
import { formatIntegerPtBr, formatNumberPtBr } from "../utils/formatters";
import { unitSuffix } from "../utils/safetyStockStatus";

type DeficitByUnitProps = {
  rows: DeficitByUnitRow[];
};

export function DeficitByUnit({ rows }: DeficitByUnitProps) {
  const hasDeficit = rows.some((row) => row.deficit_quantity > 0);

  return (
    <section className="ess-deficit" aria-label="Déficit por unidade de medida">
      <div className="ess-deficit__header">
        <h2 className="ess-deficit__title">Déficit por unidade</h2>
        <p className="ess-deficit__subtitle">
          Totais agrupados por unidade de medida — unidades diferentes não são somadas.
        </p>
      </div>

      {!hasDeficit ? (
        <p className="ess-deficit__empty" role="status">
          Nenhum déficit registrado para os filtros selecionados.
        </p>
      ) : (
        <ul className="ess-deficit__list">
          {rows.map((row) => (
            <li key={row.unit} className="ess-deficit__item">
              <span className="ess-deficit__unit">{row.unit}</span>
              <span className="ess-deficit__count">
                {formatIntegerPtBr(row.material_count)} materiais
              </span>
              <span className="ess-deficit__quantity">
                {formatNumberPtBr(row.deficit_quantity)} {unitSuffix(row.unit)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
