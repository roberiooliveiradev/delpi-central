import { Database } from "lucide-react";

import type { StockValueByLocation, StockValueEstimation } from "../types/supplies";
import {
  formatPeriodLabelLong,
  formatProtheusDateHuman,
  humanizeProtheusDatesInText,
} from "../utils/dates";
import { formatCurrency } from "../utils/format";

type StockContextCardProps = {
  dateStart?: string;
  dateEnd?: string;
  branchLabel: string;
  locationLabel: string;
  hasHistoricalPeriod: boolean;
  estimation?: StockValueEstimation;
  isOfficialClosure: boolean;
  isRegisterSnapshot: boolean;
  byBranch?: StockValueByLocation[];
};

type ContextStat = {
  label: string;
  value: string;
  hint?: string;
};

function methodBadge(
  isOfficialClosure: boolean,
  isRegisterSnapshot: boolean,
  estimation?: StockValueEstimation
): { label: string; tone: "success" | "info" | "neutral" } {
  if (isOfficialClosure) {
    return { label: "Fechamento oficial SB9", tone: "success" };
  }
  if (isRegisterSnapshot) {
    return { label: "Snapshot SB2 · MATR460", tone: "info" };
  }
  if (estimation?.enabled) {
    return { label: "Kardex SB9 + SD3", tone: "neutral" };
  }
  return { label: "Posição atual SB2", tone: "info" };
}

function buildStats(
  estimation: StockValueEstimation | undefined,
  isRegisterSnapshot: boolean
): ContextStat[] {
  const register = estimation?.inventory_register;
  if (isRegisterSnapshot && register) {
    const stats: ContextStat[] = [
      {
        label: "EM processo (proxy)",
        value: formatCurrency(register.em_processo_proxy_value),
      },
      {
        label: "Total geral (proxy)",
        value: formatCurrency(register.total_geral_proxy_value),
        hint: "EM estoque + EM processo",
      },
      {
        label: "Armazéns de processo",
        value: (register.process_locations ?? []).join(", ") || "—",
      },
    ];
    if (estimation?.closing_base_date) {
      stats.push({
        label: "Último fechamento SB9",
        value: formatProtheusDateHuman(estimation.closing_base_date),
        hint: estimation.closing_base_value
          ? formatCurrency(estimation.closing_base_value)
          : undefined,
      });
    }
    return stats;
  }

  if (!estimation?.enabled) return [];

  const stats: ContextStat[] = [
    {
      label: "Base SB9",
      value: formatCurrency(estimation.closing_base_value),
      hint: estimation.closing_base_date
        ? formatProtheusDateHuman(estimation.closing_base_date)
        : undefined,
    },
    {
      label: "Ponte SD3",
      value: formatCurrency(estimation.bridge_value),
    },
    {
      label: "Movimento no período",
      value: formatCurrency(estimation.period_net_value),
    },
  ];

  if (estimation.official_closure_available) {
    stats.push({
      label: "SB9 até fim do período",
      value: formatCurrency(estimation.official_closure_value),
      hint: `${formatProtheusDateHuman(estimation.official_closure_date)}${
        estimation.official_closure_on_period_end ? " · na data do inventário" : ""
      }`,
    });
  }

  return stats;
}

export function StockContextCard({
  dateStart,
  dateEnd,
  branchLabel,
  locationLabel,
  hasHistoricalPeriod,
  estimation,
  isOfficialClosure,
  isRegisterSnapshot,
  byBranch = [],
}: StockContextCardProps) {
  const badge = methodBadge(isOfficialClosure, isRegisterSnapshot, estimation);
  const periodLabel = hasHistoricalPeriod
    ? formatPeriodLabelLong(dateStart, dateEnd)
    : "Posição corrente (sem filtro de período)";
  const stats = buildStats(estimation, isRegisterSnapshot);

  const branchRows = byBranch.filter(
    (row) =>
      row.closing_base_date != null ||
      row.closing_base_value != null ||
      row.bridge_value != null
  );

  const note = estimation?.note
    ? humanizeProtheusDatesInText(estimation.note)
    : null;
  const warning = estimation?.data_quality_warning
    ? humanizeProtheusDatesInText(estimation.data_quality_warning)
    : null;

  const showComposition =
    stats.length > 0 || Boolean(warning) || Boolean(note) || isOfficialClosure;

  return (
    <article className="ds-card ds-stock-context-card" aria-label="Contexto TOTVS Protheus">
      <header className="ds-stock-context-card__header">
        <div className="ds-stock-context-card__brand" aria-hidden="true">
          <Database size={22} />
        </div>
        <div className="ds-stock-context-card__intro">
          <h2 className="ds-stock-context-card__title">TOTVS Protheus</h2>
          <p className="ds-stock-context-card__sources">
            CPV (movimentos SD3), OTD de compras, saldo de estoque e base do giro IDD.
          </p>
        </div>
        <span className={`ds-stock-context-card__badge ds-stock-context-card__badge--${badge.tone}`}>
          {badge.label}
        </span>
      </header>

      <dl className="ds-stock-context-card__meta">
        <div>
          <dt>Período</dt>
          <dd>{periodLabel}</dd>
        </div>
        <div>
          <dt>Escopo</dt>
          <dd>
            {branchLabel} · {locationLabel}
          </dd>
        </div>
        {isOfficialClosure && estimation?.end_date ? (
          <div>
            <dt>Inventário fechado em</dt>
            <dd>{formatProtheusDateHuman(estimation.end_date)}</dd>
          </div>
        ) : null}
      </dl>

      {showComposition ? (
        <div className="ds-stock-context-card__body">
          {note ? <p className="ds-stock-context-card__note">{note}</p> : null}
          {warning ? (
            <p className="ds-stock-context-card__warning" role="alert">
              {warning}
            </p>
          ) : null}

          {stats.length > 0 ? (
            <div className="ds-stock-context-card__composition">
              <h3 className="ds-stock-context-card__composition-title">
                {isRegisterSnapshot
                  ? "Composição do inventário (proxy MATR460)"
                  : "Composição da estimativa"}
              </h3>
              <div className="ds-stock-context-card__stats">
                {stats.map((stat) => (
                  <div key={stat.label} className="ds-stock-context-card__stat">
                    <span className="ds-stock-context-card__stat-label">{stat.label}</span>
                    <strong className="ds-stock-context-card__stat-value">{stat.value}</strong>
                    {stat.hint ? (
                      <span className="ds-stock-context-card__stat-hint">{stat.hint}</span>
                    ) : null}
                  </div>
                ))}
              </div>
              {isRegisterSnapshot ? (
                <p className="ds-stock-context-card__footnote">
                  O card <strong>Valor total</strong> abaixo corresponde ao{" "}
                  <strong>EM estoque (SB2)</strong> — referência principal para metas.
                </p>
              ) : null}
            </div>
          ) : null}

          {branchRows.length > 0 && !isRegisterSnapshot ? (
            <div className="ds-stock-context-card__table-wrap">
              <h3 className="ds-stock-context-card__composition-title">Por filial</h3>
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
                        {formatProtheusDateHuman(row.closing_base_date)}
                        <br />
                        <span className="ds-stock-estimation__muted">
                          {formatCurrency(row.closing_base_value)}
                        </span>
                      </td>
                      <td>{formatCurrency(row.bridge_value)}</td>
                      <td>{formatCurrency(row.period_net_value)}</td>
                      <td>
                        {row.official_closure_available
                          ? `${formatProtheusDateHuman(row.official_closure_date)} · ${formatCurrency(row.official_closure_value)}`
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </div>
      ) : null}
    </article>
  );
}
