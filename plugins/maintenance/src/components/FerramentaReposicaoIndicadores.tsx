import { useMemo } from "react";
import { Activity, Calendar, Layers, Repeat, Tags } from "lucide-react";

import type { ReposicaoItem } from "../data/api/maintenanceApi";
import {
  computeReposicaoIndicadores,
  formatReposicaoIndicadorDate,
} from "../utils/reposicaoIndicadores";
import { formatCodigoDescricao } from "../utils/pecaOptions";
import { KpiCard } from "./data/KpiCard";

type FerramentaReposicaoIndicadoresProps = {
  reposicoes: ReposicaoItem[];
  pecaLabels?: Record<string, string>;
  loading?: boolean;
  filtrosAtivos?: boolean;
};

function formatNumber(value: number): string {
  return value.toLocaleString("pt-BR");
}

export function FerramentaReposicaoIndicadores({
  reposicoes,
  pecaLabels = {},
  loading = false,
  filtrosAtivos = false,
}: FerramentaReposicaoIndicadoresProps) {
  const indicadores = useMemo(() => computeReposicaoIndicadores(reposicoes), [reposicoes]);

  if (loading) {
    return (
      <section className="dm-card dm-indicadores-card" aria-busy="true">
        <div className="dm-section-header">
          <h3 className="dm-section-header__title">Indicadores</h3>
        </div>
        <p className="dm-indicadores-card__empty">Calculando indicadores…</p>
      </section>
    );
  }

  if (indicadores.total === 0) {
    if (filtrosAtivos) {
      return (
        <section className="dm-card dm-indicadores-card">
          <div className="dm-section-header">
            <h3 className="dm-section-header__title">Indicadores</h3>
          </div>
          <p className="dm-indicadores-card__empty">Nenhuma reposição com os filtros aplicados.</p>
        </section>
      );
    }
    return null;
  }

  const pecaMaisLabel = indicadores.pecaMaisTrocada
    ? formatCodigoDescricao(
        indicadores.pecaMaisTrocada.codigo,
        pecaLabels[indicadores.pecaMaisTrocada.codigo],
      )
    : "—";

  return (
    <section className="dm-card dm-indicadores-card">
      <div className="dm-section-header">
        <div className="dm-section-header__title-group">
          <h3 className="dm-section-header__title">Indicadores</h3>
          {filtrosAtivos ? (
            <p className="dm-section-header__hint">Com filtros do histórico aplicados.</p>
          ) : null}
        </div>
        <div className="dm-section-header__meta">
          <span className="dm-badge">{formatNumber(indicadores.total)} reposição(ões)</span>
        </div>
      </div>

      <div className="dm-indicadores-kpi-grid">
        <KpiCard
          title="Total de reposições"
          value={formatNumber(indicadores.total)}
          icon={<Repeat size={20} aria-hidden="true" />}
        />
        <KpiCard
          title="Peças distintas"
          value={formatNumber(indicadores.pecasDistintas)}
          icon={<Layers size={20} aria-hidden="true" />}
        />
        <KpiCard
          title="Média de golpes"
          value={formatNumber(indicadores.mediaGolpes)}
          icon={<Activity size={20} aria-hidden="true" />}
        />
        <KpiCard
          title="Última reposição"
          value={formatReposicaoIndicadorDate(indicadores.ultimaReposicao)}
          icon={<Calendar size={20} aria-hidden="true" />}
        />
      </div>

      {indicadores.pecaMaisTrocada ? (
        <p className="dm-indicadores-card__highlight">
          Peça mais trocada:{" "}
          <strong>
            {pecaMaisLabel} ({formatNumber(indicadores.pecaMaisTrocada.quantidade)}×)
          </strong>
        </p>
      ) : null}

      <div className="dm-indicadores-breakdown">
        <div className="dm-indicadores-breakdown__title">
          <Tags size={16} aria-hidden="true" />
          <h4>Quantidade por motivo</h4>
        </div>
        <ul className="dm-motivo-stats">
          {indicadores.porMotivo.map((item) => {
            const percentual = Math.round((item.quantidade / indicadores.total) * 100);
            return (
              <li key={item.motivo_id} className="dm-motivo-stats__item">
                <div className="dm-motivo-stats__label">
                  <span>{item.descricao}</span>
                  <strong>
                    {formatNumber(item.quantidade)} ({percentual}%)
                  </strong>
                </div>
                <div
                  className="dm-motivo-stats__bar"
                  role="presentation"
                  style={{ width: `${percentual}%` }}
                />
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}
