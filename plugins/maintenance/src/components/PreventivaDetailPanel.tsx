import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ExternalLink, Hammer, Package, PlusCircle } from "lucide-react";

import { ChartSection, StateBox, StatusBadge } from "./data";
import { MAINTENANCE_ROUTES } from "../constants/routes";
import type { FerramentaItem, PreventivaAlerta, PreventivaHistoricoItem } from "../data/api/maintenanceApi";

export type PreventivaDetailData = {
  alerta: PreventivaAlerta | null;
  ferramenta: FerramentaItem | null;
  pecaDescricao: string | null;
  estoqueLocal01: number | null;
  historico: PreventivaHistoricoItem[];
};

type PreventivaDetailPanelProps = {
  codigoFerramenta: string;
  codigoPeca: string;
  data: PreventivaDetailData | null;
  loading: boolean;
  layout?: "sidebar" | "page";
  onNavigate: (path: string) => void;
  onClose: () => void;
};

function formatDate(value: string | undefined): string {
  if (!value) return "—";
  return new Date(value).toLocaleString("pt-BR");
}

function formatNumber(value: number | undefined | null): string {
  if (value === undefined || value === null || Number.isNaN(value)) return "—";
  return value.toLocaleString("pt-BR");
}

function statusAccent(status: string | undefined): string {
  if (status === "CRÍTICO") return "#ef4444";
  if (status === "ATENÇÃO") return "#f59e0b";
  if (status === "OK") return "#22c55e";
  return "var(--dm-accent, #089bdb)";
}

export function PreventivaDetailPanel({
  codigoFerramenta,
  codigoPeca,
  data,
  loading,
  layout = "sidebar",
  onNavigate,
  onClose,
}: PreventivaDetailPanelProps) {
  const isPage = layout === "page";
  const hasSelection = Boolean(codigoFerramenta && codigoPeca);
  const alerta = data?.alerta;
  const ferramenta = data?.ferramenta;
  const historicoChart = (data?.historico ?? []).map((row) => ({
    label: new Date(row.data_reposicao).toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "short",
      year: "2-digit",
    }),
    golpes: row.golpes,
  }));

  const usageChart =
    alerta && alerta.media_golpes > 0
      ? [
          { name: "Golpes atuais", value: alerta.golpes_atuais, fill: statusAccent(alerta.status) },
          {
            name: "Média histórica",
            value: Math.round(alerta.media_golpes),
            fill: "color-mix(in srgb, var(--dm-accent) 55%, #94a3b8)",
          },
        ]
      : [];

  const RootTag = isPage ? "section" : "aside";

  return (
    <RootTag
      className={`dm-detail-panel${hasSelection ? " is-active" : ""}${isPage ? " dm-detail-panel--page" : ""}`}
      aria-live="polite"
    >
      {hasSelection ? (
        <div className="dm-detail-panel__header">
          <div>
            {!isPage ? <p className="dm-eyebrow">Detalhe preventivo</p> : null}
            <h3 className="dm-detail-panel__title">
              {codigoFerramenta} / {codigoPeca}
            </h3>
          </div>
          <button type="button" className="dm-ghost-btn dm-detail-panel__close" onClick={onClose}>
            {isPage ? "Voltar à lista" : "Fechar"}
          </button>
        </div>
      ) : (
        <div className="dm-detail-panel__header">
          <div>
            {!isPage ? <p className="dm-eyebrow">Painel de detalhes</p> : null}
            <h3 className="dm-detail-panel__title">Selecione um item</h3>
          </div>
        </div>
      )}

      {!hasSelection ? (
        <StateBox>
          Selecione um alerta ou reposição nas abas anteriores para ver detalhes, gráficos e
          estoque.
        </StateBox>
      ) : null}

      {hasSelection && loading ? (
        <div className="dm-detail-panel__loading">
          <StateBox>Carregando detalhes…</StateBox>
        </div>
      ) : null}

      {hasSelection && !loading && data ? (
        <div className="dm-detail-panel__body dm-content-transition">
          <div className="dm-detail-panel__identity">
            <button
              type="button"
              className="dm-detail-panel__link"
              onClick={() => onNavigate(MAINTENANCE_ROUTES.miniAplicadorDetail(codigoFerramenta))}
            >
              <Hammer size={16} aria-hidden="true" />
              <span>
                {ferramenta
                  ? `${ferramenta.codigo} — ${ferramenta.descricao}`
                  : codigoFerramenta}
              </span>
              <ExternalLink size={14} aria-hidden="true" />
            </button>
            <p className="dm-detail-panel__meta">
              <Package size={14} aria-hidden="true" />
              Peça: {codigoPeca}
              {data.pecaDescricao ? ` — ${data.pecaDescricao}` : ""}
            </p>
          </div>

          {alerta ? (
            <div className="dm-detail-metrics">
              <div className="dm-detail-metric">
                <span>Status</span>
                <StatusBadge status={alerta.status} />
              </div>
              <div className="dm-detail-metric">
                <span>% de uso</span>
                <strong>{alerta.percentual_uso.toLocaleString("pt-BR")}%</strong>
              </div>
              <div className="dm-detail-metric">
                <span>Golpes atuais</span>
                <strong>{formatNumber(alerta.golpes_atuais)}</strong>
              </div>
              <div className="dm-detail-metric">
                <span>Média histórica</span>
                <strong>{formatNumber(alerta.media_golpes)}</strong>
              </div>
              <div className="dm-detail-metric">
                <span>Última reposição</span>
                <strong>{formatDate(alerta.data_ultima_reposicao)}</strong>
              </div>
              <div className="dm-detail-metric">
                <span>Estoque peça (01)</span>
                <strong>{formatNumber(data.estoqueLocal01)}</strong>
              </div>
            </div>
          ) : (
            <StateBox>Sem dados preventivos para este par — registre reposições para calcular alertas.</StateBox>
          )}

          {usageChart.length > 0 ? (
            <ChartSection title="Uso vs. média">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={usageChart} layout="vertical" margin={{ left: 8, right: 16 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" />
                  <YAxis type="category" dataKey="name" width={120} />
                  <Tooltip formatter={(value) => formatNumber(Number(value))} />
                  <Bar dataKey="value" radius={[0, 8, 8, 0]}>
                    {usageChart.map((entry) => (
                      <Cell key={entry.name} fill={entry.fill} />
                    ))}
                  </Bar>
                  {alerta ? (
                    <ReferenceLine
                      x={alerta.media_golpes}
                      stroke="#64748b"
                      strokeDasharray="4 4"
                      label={{ value: "Média", position: "insideTopRight", fill: "#64748b" }}
                    />
                  ) : null}
                </BarChart>
              </ResponsiveContainer>
            </ChartSection>
          ) : null}

          <ChartSection
            title="Histórico de golpes entre reposições"
            actions={
              historicoChart.length > 0 ? (
                <span className="dm-badge">{historicoChart.length} trocas</span>
              ) : undefined
            }
          >
            {historicoChart.length === 0 ? (
              <StateBox>Nenhuma reposição registrada para este par.</StateBox>
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={historicoChart}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                  <YAxis />
                  <Tooltip formatter={(value) => [formatNumber(Number(value)), "Golpes"]} />
                  <Legend />
                  <Bar
                    dataKey="golpes"
                    name="Golpes por ciclo"
                    fill="var(--dm-accent, #089bdb)"
                    radius={[8, 8, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            )}
          </ChartSection>

          <div className="dm-detail-panel__actions">
            <button
              type="button"
              className="dm-primary-btn"
              onClick={() => onNavigate(MAINTENANCE_ROUTES.miniAplicadorDetail(codigoFerramenta))}
            >
              <ExternalLink size={16} />
              Abrir ferramenta
            </button>
            <button
              type="button"
              className="dm-ghost-btn"
              onClick={() => onNavigate(MAINTENANCE_ROUTES.miniAplicadorDetail(codigoFerramenta))}
            >
              <PlusCircle size={16} />
              Nova reposição
            </button>
          </div>
        </div>
      ) : null}
    </RootTag>
  );
}
