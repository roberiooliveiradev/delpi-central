import { useCallback, useEffect, useMemo, useState } from "react";
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

import {
  ChartSection,
  type DataTableColumn,
  DataTableSection,
  FilialBadge,
  FilterBar,
  StateBox,
  StatusBadge,
} from "../../components/data";
import { MaintenanceShell } from "../../components/MaintenanceShell";
import { MiniAplicadoresPageHeader } from "../../components/MiniAplicadoresPageHeader";
import { MAINTENANCE_ROUTES } from "../../constants/routes";
import {
  useMaintenanceActiveFilial,
  useMaintenanceModuleHomePath,
  useOperationalFilial,
} from "../../hooks/useMaintenanceScope";
import {
  fetchPreventivaAlertas,
  fetchPreventivaHistorico,
  fetchUltimasReposicoes,
  type PreventivaAlerta,
  type UltimaReposicaoItem,
} from "../../data/api/maintenanceApi";

type RelatorioPageProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  filialScope?: string;
  onNavigate: (path: string) => void;
};

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
  const [ultimas, setUltimas] = useState<UltimaReposicaoItem[]>([]);
  const [selected, setSelected] = useState<PreventivaAlerta | null>(null);
  const [historico, setHistorico] = useState<Array<{ label: string; golpes: number }>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAlertas = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [alertasData, ultimasData] = await Promise.all([
        fetchPreventivaAlertas(filial, getAccessToken),
        fetchUltimasReposicoes(filial, getAccessToken),
      ]);
      setAlertas(alertasData.items ?? []);
      setUltimas(ultimasData.items ?? []);
      setSelected(null);
      setHistorico([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar alertas.");
      setAlertas([]);
      setUltimas([]);
    } finally {
      setLoading(false);
    }
  }, [filial, getAccessToken]);

  useEffect(() => {
    void loadAlertas();
  }, [loadAlertas]);

  const loadHistorico = useCallback(
    async (item: PreventivaAlerta) => {
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
    },
    [getAccessToken],
  );

  const resumo = useMemo(
    () => ({
      critico: alertas.filter((item) => item.status === "CRÍTICO").length,
      atencao: alertas.filter((item) => item.status === "ATENÇÃO").length,
      ok: alertas.filter((item) => item.status === "OK").length,
    }),
    [alertas],
  );

  const ultimasColumns = useMemo<DataTableColumn<UltimaReposicaoItem>[]>(
    () => [
      {
        key: "data",
        header: "Data",
        render: (item) => new Date(item.data_reposicao).toLocaleString("pt-BR"),
      },
      {
        key: "ferramenta",
        header: "Ferramenta",
        render: (item) => (
          <button
            type="button"
            className="dm-link-btn"
            onClick={() => onNavigate(MAINTENANCE_ROUTES.miniAplicadorDetail(item.codigo_ferramenta))}
          >
            {item.codigo_ferramenta}
          </button>
        ),
      },
      { key: "peca", header: "Peça", render: (item) => item.codigo_peca },
      { key: "golpes", header: "Golpes", render: (item) => item.golpes, align: "right" },
    ],
    [onNavigate],
  );

  const alertasColumns = useMemo<DataTableColumn<PreventivaAlerta>[]>(
    () => [
      {
        key: "status",
        header: "Status",
        render: (item) => (
          <StatusBadge status={item.status} onClick={() => void loadHistorico(item)} />
        ),
      },
      { key: "ferramenta", header: "Ferramenta", render: (item) => item.codigo_ferramenta },
      { key: "peca", header: "Peça", render: (item) => item.codigo_peca },
      {
        key: "golpes_atuais",
        header: "Golpes atuais",
        render: (item) => item.golpes_atuais,
        align: "right",
      },
      { key: "media", header: "Média", render: (item) => item.media_golpes, align: "right" },
      {
        key: "percentual",
        header: "% uso",
        render: (item) => `${item.percentual_uso}%`,
        align: "right",
      },
    ],
    [loadHistorico],
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

      <FilterBar leading={<FilialBadge filial={filial} />}>
        <div className="dm-kpi-inline">
          <span className="dm-badge dm-badge--danger">CRÍTICO: {resumo.critico}</span>
          <span className="dm-badge dm-badge--warning">ATENÇÃO: {resumo.atencao}</span>
          <span className="dm-badge dm-badge--success">OK: {resumo.ok}</span>
        </div>
      </FilterBar>

      {error ? <StateBox variant="error">{error}</StateBox> : null}

      <DataTableSection
        title="Últimas reposições por peça"
        columns={ultimasColumns}
        rows={ultimas}
        loading={loading}
        emptyMessage="Nenhuma reposição registrada nesta filial."
        getRowKey={(item) => item.reposicao_id}
      />

      <DataTableSection
        title="Ranking preventivo"
        columns={alertasColumns}
        rows={alertas}
        loading={loading}
        emptyMessage="Nenhum alerta — registre reposições para gerar preventiva."
        getRowKey={(item) => `${item.codigo_ferramenta}-${item.codigo_peca}`}
        getRowClassName={(item) =>
          selected?.codigo_peca === item.codigo_peca && selected?.codigo_ferramenta === item.codigo_ferramenta
            ? "is-selected"
            : undefined
        }
      />

      {selected ? (
        <ChartSection
          title={`Histórico — ${selected.codigo_ferramenta} / ${selected.codigo_peca}`}
          actions={
            <button
              type="button"
              className="dm-ghost-btn"
              onClick={() => onNavigate(MAINTENANCE_ROUTES.miniAplicadorDetail(selected.codigo_ferramenta))}
            >
              Abrir ferramenta
            </button>
          }
        >
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={historico}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="golpes" fill="var(--dm-accent, #089bdb)" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartSection>
      ) : null}
    </MaintenanceShell>
  );
}
