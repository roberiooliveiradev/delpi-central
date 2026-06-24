import type { StockValueByLocation, StockValueEstimation } from "../types/supplies";
import { formatCurrency } from "../utils/format";

function formatProtheusDate(value?: string | null): string {
  const raw = (value ?? "").trim();
  if (raw.length !== 8) return raw || "—";
  return `${raw.slice(6, 8)}/${raw.slice(4, 6)}/${raw.slice(0, 4)}`;
}

type StockEstimationBreakdownProps = {
  estimation: StockValueEstimation;
  byBranch?: StockValueByLocation[];
};

export function StockEstimationBreakdown({
  estimation,
  byBranch = [],
}: StockEstimationBreakdownProps) {
  const branchRows = byBranch.filter(
    (row) =>
      row.closing_base_date != null ||
      row.closing_base_value != null ||
      row.bridge_value != null
  );

  const showConsolidated =
    branchRows.length === 0 &&
    (estimation.closing_base_value != null ||
      estimation.bridge_value != null ||
      estimation.period_net_value != null);

  return (
    <section className="ds-stock-estimation" aria-label="Composição da estimativa de estoque">
      {estimation.data_quality_warning ? (
        <div className="ds-stock-estimation__warning" role="alert">
          {estimation.data_quality_warning}
        </div>
      ) : null}

      {showConsolidated ? (
        <dl className="ds-stock-estimation__grid">
          <div>
            <dt>Base SB9</dt>
            <dd>
              {formatProtheusDate(estimation.closing_base_date)} ·{" "}
              {formatCurrency(estimation.closing_base_value)}
            </dd>
          </div>
          <div>
            <dt>Ponte SD3</dt>
            <dd>{formatCurrency(estimation.bridge_value)}</dd>
          </div>
          <div>
            <dt>Período SD3</dt>
            <dd>{formatCurrency(estimation.period_net_value)}</dd>
          </div>
          {estimation.official_closure_available ? (
            <div>
              <dt>Último fechamento SB9 ≤ fim do período</dt>
              <dd>
                {formatProtheusDate(estimation.official_closure_date)} ·{" "}
                {formatCurrency(estimation.official_closure_value)}
                {estimation.official_closure_on_period_end
                  ? " (na data do inventário)"
                  : null}
              </dd>
            </div>
          ) : (
            <div>
              <dt>Fechamento SB9 na data fim</dt>
              <dd>Indisponível em SB9010</dd>
            </div>
          )}
        </dl>
      ) : null}

      {branchRows.length > 0 ? (
        <div className="ds-stock-estimation__table-wrap">
          <table className="ds-stock-estimation__table">
            <thead>
              <tr>
                <th>Filial</th>
                <th>Base SB9</th>
                <th>Ponte SD3</th>
                <th>Período SD3</th>
                <th>SB9 ≤ fim</th>
              </tr>
            </thead>
            <tbody>
              {branchRows.map((row) => (
                <tr key={row.branch ?? "branch"}>
                  <td>{row.branch ?? "—"}</td>
                  <td>
                    {formatProtheusDate(row.closing_base_date)}
                    <br />
                    <span className="ds-stock-estimation__muted">
                      {formatCurrency(row.closing_base_value)}
                    </span>
                  </td>
                  <td>{formatCurrency(row.bridge_value)}</td>
                  <td>{formatCurrency(row.period_net_value)}</td>
                  <td>
                    {row.official_closure_available
                      ? `${formatProtheusDate(row.official_closure_date)} · ${formatCurrency(row.official_closure_value)}`
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}
