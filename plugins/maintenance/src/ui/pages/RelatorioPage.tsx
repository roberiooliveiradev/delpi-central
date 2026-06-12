import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { LineChart, RefreshCw } from "lucide-react";

import { MaintenanceShell } from "../../components/MaintenanceShell";
import { MiniAplicadoresPageHeader } from "../../components/MiniAplicadoresPageHeader";
import { MAINTENANCE_ROUTES } from "../../constants/routes";
import { useMaintenanceActiveFilial, useMaintenanceModuleHomePath, useOperationalFilial } from "../../hooks/useMaintenanceScope";
import {
  fetchPreventivaAlertas,
  fetchPreventivaHistorico,
  type PreventivaAlerta,
} from "../../data/api/maintenanceApi";

type RelatorioPageProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  filialScope?: string;
  onNavigate: (path: string) => void;
};

function statusClass(status: string): string {
  if (status === "CRÍTICO") return "dm-badge dm-badge--danger";
  if (status === "ATENÇÃO") return "dm-badge dm-badge--warning";
  if (status === "OK") return "dm-badge dm-badge--success";
  return "dm-badge";
}

export function RelatorioPage({
  getAccessToken,
  pathname,
  filialScope,
  onNavigate,
}: RelatorioPageProps) {
  const filial = useOperationalFilial(getAccessToken, filialScope) ?? "01";
  const moduleHomePath = useMaintenanceModuleHomePath(getAccessToken, filialScope ?? filial);
  const { canManageMiniApplicators } = useMaintenanceActiveFilial(getAccessToken, filialScope);
  const [alertas, setAlertas] = useState<PreventivaAlerta[]>([]);
  const [selected, setSelected] = useState<PreventivaAlerta | null>(null);
  const [historico, setHistorico] = useState<Array<{ label: string; golpes: number }>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAlertas = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchPreventivaAlertas(filial, getAccessToken);
      setAlertas(data.items ?? []);
      setSelected(null);
      setHistorico([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar alertas.");
      setAlertas([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadAlertas();
  }, [filial, getAccessToken]);

  const loadHistorico = async (item: PreventivaAlerta) => {
    setSelected(item);
    try {
      const data = await fetchPreventivaHistorico(
        {
          filial: item.filial,
          codigo_ferramenta: item.codigo_ferramenta,
          codigo_peca: item.codigo_peca,
        },
        getAccessToken,
      );
      setHistorico(
        (data.items ?? []).map((row, index) => ({
          label: `#${index + 1}`,
          golpes: row.golpes,
        })),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar histórico.");
      setHistorico([]);
    }
  };

  const resumo = useMemo(
    () => ({
      critico: alertas.filter((item) => item.status === "CRÍTICO").length,
      atencao: alertas.filter((item) => item.status === "ATENÇÃO").length,
      ok: alertas.filter((item) => item.status === "OK").length,
    }),
    [alertas],
  );

  return (
    <MaintenanceShell>
      <MiniAplicadoresPageHeader
        title="Relatório preventivo"
        subtitle="Alertas por percentual de uso vs. média histórica de golpes."
        icon={LineChart}
        moduleHomePath={moduleHomePath}
        showConfiguration={canManageMiniApplicators}
        currentPath={pathname}
        onNavigate={onNavigate}
        actions={
          <button type="button" className="dm-primary-btn" onClick={() => void loadAlertas()} disabled={loading}>
            <RefreshCw size={16} />
            {loading ? "Carregando…" : "Atualizar"}
          </button>
        }
      />

      <section className="dm-card dm-filter-bar">
        <p className="dm-filial-badge">Filial operacional: {filial}</p>
        <div className="dm-kpi-inline">
          <span className="dm-badge dm-badge--danger">CRÍTICO: {resumo.critico}</span>
          <span className="dm-badge dm-badge--warning">ATENÇÃO: {resumo.atencao}</span>
          <span className="dm-badge dm-badge--success">OK: {resumo.ok}</span>
        </div>
      </section>

      {error ? <p className="dm-state-box dm-state-box--error">{error}</p> : null}

      <section className="dm-card">
        <h3 className="dm-card__title">Ranking preventivo</h3>
        <div className="dm-table-wrap">
          <table className="dm-table">
            <thead>
              <tr>
                <th>Status</th>
                <th>Ferramenta</th>
                <th>Peça</th>
                <th>Golpes atuais</th>
                <th>Média</th>
                <th>% uso</th>
              </tr>
            </thead>
            <tbody>
              {alertas.length === 0 && !loading ? (
                <tr>
                  <td colSpan={6} className="dm-table__empty">
                    Nenhum alerta — registre reposições para gerar preventiva.
                  </td>
                </tr>
              ) : null}
              {alertas.map((item) => (
                <tr
                  key={`${item.codigo_ferramenta}-${item.codigo_peca}`}
                  className={selected?.codigo_peca === item.codigo_peca ? "is-selected" : ""}
                >
                  <td data-label="Status">
                    <button type="button" className={statusClass(item.status)} onClick={() => void loadHistorico(item)}>
                      {item.status}
                    </button>
                  </td>
                  <td data-label="Ferramenta">{item.codigo_ferramenta}</td>
                  <td data-label="Peça">{item.codigo_peca}</td>
                  <td data-label="Golpes atuais">{item.golpes_atuais}</td>
                  <td data-label="Média">{item.media_golpes}</td>
                  <td data-label="% uso">{item.percentual_uso}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {selected ? (
        <section className="dm-card">
          <h3 className="dm-card__title">
            Histórico — {selected.codigo_ferramenta} / {selected.codigo_peca}
          </h3>
          <div className="dm-chart-wrap">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={historico}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="label" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="golpes" fill="var(--dm-accent, #089bdb)" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <button
            type="button"
            className="dm-ghost-btn"
            onClick={() =>
              onNavigate(MAINTENANCE_ROUTES.miniAplicadorDetail(selected.codigo_ferramenta))
            }
          >
            Abrir ferramenta
          </button>
        </section>
      ) : null}
    </MaintenanceShell>
  );
}
