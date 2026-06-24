import type { StockValueByLocation, StockValueEstimation } from "../types/supplies";
import { formatCurrency } from "../utils/format";
import { InfoCard } from "./InfoCard";
import { MetricCard } from "./MetricCard";

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

  const register = estimation.inventory_register;
  const showRegister =
    estimation.method === "sb2_register_snapshot" && register != null;

  const hasMetrics = showRegister || (showConsolidated && !showRegister);
  const hasBranchTable = branchRows.length > 0;

  if (!estimation.data_quality_warning && !hasMetrics && !hasBranchTable) {
    return null;
  }

  return (
    <section
      className="ds-stock-estimation-section"
      aria-label="Composição da estimativa de estoque"
    >
      {estimation.data_quality_warning ? (
        <InfoCard variant="warning">{estimation.data_quality_warning}</InfoCard>
      ) : null}

      {showRegister ? (
        <div className="ds-stock-estimation-section__block">
          <h2 className="ds-section-title">
            Composição do inventário (proxy MATR460)
          </h2>
          <div className="ds-metric-grid">
            <MetricCard
              label="EM ESTOQUE (SB2)"
              value={formatCurrency(register.em_estoque_value)}
            />
            <MetricCard
              label="EM PROCESSO (proxy)"
              value={formatCurrency(register.em_processo_proxy_value)}
            />
            <MetricCard
              label="TOTAL GERAL (proxy)"
              value={formatCurrency(register.total_geral_proxy_value)}
            />
            <MetricCard
              label="Armazéns de processo"
              value={(register.process_locations ?? []).join(", ") || "—"}
            />
          </div>
        </div>
      ) : null}

      {showConsolidated && !showRegister ? (
        <div className="ds-stock-estimation-section__block">
          <h2 className="ds-section-title">Composição Kardex (SB9 + SD3)</h2>
          <div className="ds-metric-grid">
            <MetricCard
              label="Base SB9"
              value={formatCurrency(estimation.closing_base_value)}
              hint={formatProtheusDate(estimation.closing_base_date)}
            />
            <MetricCard
              label="Ponte SD3"
              value={formatCurrency(estimation.bridge_value)}
            />
            <MetricCard
              label="Período SD3"
              value={formatCurrency(estimation.period_net_value)}
            />
            {estimation.official_closure_available ? (
              <MetricCard
                label="Último fechamento SB9 ≤ fim do período"
                value={formatCurrency(estimation.official_closure_value)}
                hint={`${formatProtheusDate(estimation.official_closure_date)}${
                  estimation.official_closure_on_period_end
                    ? " · na data do inventário"
                    : ""
                }`}
              />
            ) : (
              <MetricCard
                label="Fechamento SB9 na data fim"
                value="Indisponível em SB9010"
              />
            )}
          </div>
        </div>
      ) : null}

      {hasBranchTable ? (
        <article className="ds-card ds-table-section">
          <header className="ds-table-section__header">
            <h2 className="ds-section-title">Breakdown por filial</h2>
          </header>
          <div className="ds-table-wrap">
            <table className="ds-table ds-stock-estimation__table">
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
        </article>
      ) : null}
    </section>
  );
}
