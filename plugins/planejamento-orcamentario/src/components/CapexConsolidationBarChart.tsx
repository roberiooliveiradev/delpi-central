import { formatMoneyBr } from "../utils/capexInvestments";
import type { CapexConsolidationGroupItem } from "../types/budgetPlanning";

type Props = {
  title: string;
  items: CapexConsolidationGroupItem[];
  orientation?: "horizontal" | "vertical";
  emptyLabel?: string;
  currency?: string;
};

function amountNumber(value: string | undefined): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

/** Gráfico de barras acessível (CSS) — sem dependência extra de chart lib. */
export function CapexConsolidationBarChart({
  title,
  items,
  orientation = "horizontal",
  emptyLabel = "Sem dados para este agrupamento.",
  currency = "BRL",
}: Props) {
  const max = Math.max(...items.map((i) => amountNumber(i.total_amount)), 0);

  if (!items.length) {
    return <p className="po-muted">{emptyLabel}</p>;
  }

  return (
    <div
      className={
        orientation === "vertical"
          ? "po-bar-chart po-bar-chart--vertical"
          : "po-bar-chart po-bar-chart--horizontal"
      }
      role="img"
      aria-label={title}
    >
      <ul className="po-bar-chart__list">
        {items.map((item) => {
          const amount = amountNumber(item.total_amount);
          const pct = max > 0 ? Math.round((amount / max) * 100) : 0;
          const label = item.description || item.code || "—";
          const tip = `${label}: ${formatMoneyBr(item.total_amount, currency)} · ${item.investment_count} investimento(s)${
            item.percent_of_total != null ? ` · ${item.percent_of_total}% do total` : ""
          }`;
          const rowKey = [item.unit_id, item.cost_center_id || item.code]
            .filter(Boolean)
            .join(":") || item.code || label;
          return (
            <li key={rowKey} className="po-bar-chart__item" title={tip}>
              <div className="po-bar-chart__label">
                <span>{label}</span>
                <span className="po-bar-chart__meta">
                  {formatMoneyBr(item.total_amount, currency)} · {item.investment_count}
                </span>
              </div>
              <div className="po-bar-chart__track" aria-hidden="true">
                <div
                  className="po-bar-chart__fill"
                  style={
                    orientation === "vertical"
                      ? { height: `${pct}%` }
                      : { width: `${pct}%` }
                  }
                />
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
