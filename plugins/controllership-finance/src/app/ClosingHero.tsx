/**
 * Composição de hero das páginas da Central de Fechamento (doc 50).
 * Layout-only: recebe dados e handlers já resolvidos pela página — não
 * conhece HTTP, regras de negócio, autenticação ou cálculos.
 */
import type { ReactNode } from "react";

import {
  CfActionButton,
  CfMetricKpiCard,
  CfPageHero,
} from "./controllershipFinanceUi";

const updatedFormatter = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

export type ClosingHeroMetric = {
  id: string;
  label: string;
  value: string;
  /** Linha secundária sob o valor (ex.: "2 moedas" ou "de 4 filiais"). */
  hint?: ReactNode;
  /** Ícone discreto do tile (componente oficial aceita ReactNode). */
  icon?: ReactNode;
  tone?: "default" | "positive" | "negative" | "warning";
};

export type ClosingHeroProps = {
  title: ReactNode;
  subtitle: string;
  "aria-label"?: string;
  /** Timestamp real da última consulta concluída; omitido quando nulo. */
  updatedAt: Date | null;
  /** Repete a consulta vigente (mesmos filtros) — nunca valida/submete. */
  onRefresh: () => void;
  refreshing?: boolean;
  /** KPIs reais do payload — tiles `CfMetricKpiCard` com ícone e hint. */
  metrics?: ClosingHeroMetric[];
  /** Mensagem contextual persistente do hero (CfFeedbackMessage). */
  notice?: ReactNode;
  /** Área de filtros (form completo, já montado pela página). */
  filters: ReactNode;
  /** Restaura os defaults e dispara a consulta automática. */
  onClearFilters: () => void;
};

/**
 * "Atualizar" vive uma única vez por página, na linha de ações do painel
 * de filtros — o canto superior direito exibe apenas o timestamp real.
 */
export function ClosingHero({
  title,
  subtitle,
  "aria-label": ariaLabel,
  updatedAt,
  onRefresh,
  refreshing = false,
  metrics,
  notice,
  filters,
  onClearFilters,
}: ClosingHeroProps) {
  return (
    <CfPageHero
      eyebrow="Central de Fechamento"
      title={title}
      description={subtitle}
      aria-label={ariaLabel}
      actions={
        updatedAt ? (
          <span className="cf-hero-updated">
            Atualizado em {updatedFormatter.format(updatedAt)}
          </span>
        ) : null
      }
    >
      {metrics?.length ? (
        <div className="cf-hero-kpis" role="group" aria-label="Indicadores">
          {metrics.map((metric) => (
            <CfMetricKpiCard
              key={metric.id}
              label={metric.label}
              value={refreshing ? "…" : metric.value}
              hint={metric.hint}
              icon={metric.icon}
              tone={metric.tone}
            />
          ))}
        </div>
      ) : null}
      {notice}
      <div className="cf-hero-filters">{filters}</div>
      <div className="cf-settlements-actions">
        <CfActionButton
          variant="ghost"
          type="button"
          onClick={onClearFilters}
        >
          Limpar filtros
        </CfActionButton>
        <CfActionButton
          variant="primary"
          type="button"
          onClick={onRefresh}
          disabled={refreshing}
        >
          Atualizar consulta
        </CfActionButton>
      </div>
    </CfPageHero>
  );
}
