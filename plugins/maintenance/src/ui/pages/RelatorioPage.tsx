import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertTriangle, LineChart, RefreshCw, Search, X } from "lucide-react";

import {
  PreventivaDetailPanel,
  type PreventivaDetailData,
} from "../../components/PreventivaDetailPanel";
import { SectionTabs } from "../../components/SectionTabs";
import {
  type DataTableColumn,
  DataTableSection,
  FilterBar,
  StateBox,
  StatusBadge,
} from "../../components/data";
import { MaintenanceShell } from "../../components/MaintenanceShell";
import { MiniAplicadoresPageHeader } from "../../components/MiniAplicadoresPageHeader";
import {
  useMaintenanceActiveFilial,
  useMaintenanceModuleHomePath,
  useOperationalFilial,
} from "../../hooks/useMaintenanceScope";
import { resolveFilialDisplayName } from "../../utils/maintenanceFilialSelection";
import {
  fetchComponentes,
  fetchFerramenta,
  fetchPecas,
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

type ListReportTab = "alertas" | "ultimas";
type ReportTab = ListReportTab | "detalhe";
type StatusFilter = "TODOS" | "CRÍTICO" | "ATENÇÃO" | "OK" | "SEM STATUS";

type Selection = {
  codigo_ferramenta: string;
  codigo_peca: string;
};

const STATUS_FILTERS: StatusFilter[] = ["TODOS", "CRÍTICO", "ATENÇÃO", "OK", "SEM STATUS"];

function matchesFilters(
  item: { codigo_ferramenta: string; codigo_peca: string; status?: string },
  filters: { ferramenta: string; peca: string; status: StatusFilter },
): boolean {
  if (filters.ferramenta.trim()) {
    const term = filters.ferramenta.trim().toLowerCase();
    if (!item.codigo_ferramenta.toLowerCase().includes(term)) return false;
  }
  if (filters.peca.trim()) {
    const term = filters.peca.trim().toLowerCase();
    if (!item.codigo_peca.toLowerCase().includes(term)) return false;
  }
  if (filters.status !== "TODOS" && item.status !== filters.status) return false;
  return true;
}

export function RelatorioPage({
  getAccessToken,
  pathname,
  filialScope,
  onNavigate,
}: RelatorioPageProps) {
  const filial = useOperationalFilial(getAccessToken, filialScope) ?? "01";
  const moduleHomePath = useMaintenanceModuleHomePath(getAccessToken, filialScope ?? filial);
  const { canManageMiniApplicators, filiais } = useMaintenanceActiveFilial(getAccessToken, filialScope);
  const filialDisplayName = resolveFilialDisplayName(filiais, filial);

  const [listTab, setListTab] = useState<ListReportTab>("alertas");
  const [activeTab, setActiveTab] = useState<ReportTab>("alertas");
  const [alertas, setAlertas] = useState<PreventivaAlerta[]>([]);
  const [ultimas, setUltimas] = useState<UltimaReposicaoItem[]>([]);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [detailData, setDetailData] = useState<PreventivaDetailData | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ferramentaFiltro, setFerramentaFiltro] = useState("");
  const [pecaFiltro, setPecaFiltro] = useState("");
  const [statusFiltro, setStatusFiltro] = useState<StatusFilter>("TODOS");

  const loadReport = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [alertasData, ultimasData] = await Promise.all([
        fetchPreventivaAlertas(filial, getAccessToken),
        fetchUltimasReposicoes(filial, getAccessToken),
      ]);
      setAlertas(alertasData.items ?? []);
      setUltimas(ultimasData.items ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar relatório.");
      setAlertas([]);
      setUltimas([]);
    } finally {
      setLoading(false);
    }
  }, [filial, getAccessToken]);

  useEffect(() => {
    void loadReport();
  }, [loadReport]);

  const loadDetail = useCallback(
    async (next: Selection) => {
      setSelection(next);
      setDetailLoading(true);
      setDetailData(null);
      setActiveTab("detalhe");
      try {
        const alertaMatch =
          alertas.find(
            (item) =>
              item.codigo_ferramenta === next.codigo_ferramenta &&
              item.codigo_peca === next.codigo_peca,
          ) ?? null;

        const [historicoData, ferramentaData, pecasData, componentesData] = await Promise.all([
          fetchPreventivaHistorico(
            {
              filial,
              codigo_ferramenta: next.codigo_ferramenta,
              codigo_peca: next.codigo_peca,
            },
            getAccessToken,
          ),
          fetchFerramenta(next.codigo_ferramenta, filial, getAccessToken).catch(() => null),
          fetchPecas(next.codigo_ferramenta, filial, getAccessToken).catch(() => ({ items: [] })),
          fetchComponentes(next.codigo_ferramenta, filial, getAccessToken).catch(() => ({
            items: [],
          })),
        ]);

        const peca = (pecasData.items ?? []).find((item) => item.codigo === next.codigo_peca);
        const componente = (componentesData.items ?? []).find(
          (item) => item.codigo === next.codigo_peca,
        );

        setDetailData({
          alerta: alertaMatch,
          ferramenta: ferramentaData,
          pecaDescricao: peca?.descricao ?? null,
          estoqueLocal01: componente?.estoque_local_01 ?? null,
          historico: historicoData.items ?? [],
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Falha ao carregar detalhes.");
        setDetailData(null);
      } finally {
        setDetailLoading(false);
      }
    },
    [alertas, filial, getAccessToken],
  );

  const resumo = useMemo(
    () => ({
      critico: alertas.filter((item) => item.status === "CRÍTICO").length,
      atencao: alertas.filter((item) => item.status === "ATENÇÃO").length,
      ok: alertas.filter((item) => item.status === "OK").length,
      semStatus: alertas.filter((item) => item.status === "SEM STATUS").length,
      total: alertas.length,
    }),
    [alertas],
  );

  const filterState = useMemo(
    () => ({
      ferramenta: ferramentaFiltro,
      peca: pecaFiltro,
      status: statusFiltro,
    }),
    [ferramentaFiltro, pecaFiltro, statusFiltro],
  );

  const alertasFiltrados = useMemo(
    () => alertas.filter((item) => matchesFilters(item, filterState)),
    [alertas, filterState],
  );

  const ultimasFiltradas = useMemo(
    () =>
      ultimas.filter((item) =>
        matchesFilters(
          { ...item, status: undefined },
          { ...filterState, status: "TODOS" },
        ),
      ),
    [ultimas, filterState],
  );

  const clearFilters = () => {
    setFerramentaFiltro("");
    setPecaFiltro("");
    setStatusFiltro("TODOS");
  };

  const handleTabChange = (id: string) => {
    const tab = id as ReportTab;
    setActiveTab(tab);
    if (tab === "alertas" || tab === "ultimas") {
      setListTab(tab);
    }
  };

  const handleCloseDetail = () => {
    setActiveTab(listTab);
  };

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
        render: (item) => item.codigo_ferramenta,
      },
      { key: "peca", header: "Peça", render: (item) => item.codigo_peca },
      {
        key: "golpes",
        header: "Golpes",
        render: (item) => item.golpes.toLocaleString("pt-BR"),
        align: "right",
      },
    ],
    [],
  );

  const alertasColumns = useMemo<DataTableColumn<PreventivaAlerta>[]>(
    () => [
      {
        key: "status",
        header: "Status",
        interactive: true,
        render: (item) => <StatusBadge status={item.status} />,
      },
      {
        key: "ferramenta",
        header: "Ferramenta",
        render: (item) => item.codigo_ferramenta,
      },
      { key: "peca", header: "Peça", render: (item) => item.codigo_peca },
      {
        key: "ultima",
        header: "Última reposição",
        render: (item) => new Date(item.data_ultima_reposicao).toLocaleString("pt-BR"),
      },
      {
        key: "golpes_atuais",
        header: "Golpes atuais",
        render: (item) => item.golpes_atuais.toLocaleString("pt-BR"),
        align: "right",
      },
      {
        key: "media",
        header: "Média",
        render: (item) => item.media_golpes.toLocaleString("pt-BR"),
        align: "right",
      },
      {
        key: "percentual",
        header: "% uso",
        render: (item) => `${item.percentual_uso.toLocaleString("pt-BR")}%`,
        align: "right",
      },
    ],
    [],
  );

  const handleSelectAlerta = (item: PreventivaAlerta) => {
    setListTab("alertas");
    void loadDetail({
      codigo_ferramenta: item.codigo_ferramenta,
      codigo_peca: item.codigo_peca,
    });
  };

  const handleSelectUltima = (item: UltimaReposicaoItem) => {
    setListTab("ultimas");
    void loadDetail({
      codigo_ferramenta: item.codigo_ferramenta,
      codigo_peca: item.codigo_peca,
    });
  };

  const isRowSelected = (codigoFerramenta: string, codigoPeca: string) =>
    selection?.codigo_ferramenta === codigoFerramenta && selection?.codigo_peca === codigoPeca;

  return (
    <MaintenanceShell>
      <MiniAplicadoresPageHeader
        title="Relatório preventivo"
        subtitle="Alertas, últimas reposições e detalhe por ferramenta — use as abas para navegar."
        icon={LineChart}
        filial={filial}
        filialDisplayName={filialDisplayName}
        moduleHomePath={moduleHomePath}
        showConfiguration={canManageMiniApplicators}
        currentPath={pathname}
        onNavigate={onNavigate}
        actions={
          <button
            type="button"
            className="dm-primary-btn"
            onClick={() => void loadReport()}
            disabled={loading}
          >
            <RefreshCw size={16} className={loading ? "dm-spin" : undefined} />
            {loading ? "Carregando…" : "Atualizar"}
          </button>
        }
      />

      <section className="dm-kpi-grid dm-kpi-grid--report">
        <button
          type="button"
          className={`dm-card dm-kpi-card dm-kpi-card--action${statusFiltro === "CRÍTICO" ? " is-active" : ""}`}
          onClick={() => setStatusFiltro((current) => (current === "CRÍTICO" ? "TODOS" : "CRÍTICO"))}
        >
          <div className="dm-kpi-card__icon dm-kpi-card__icon--danger" aria-hidden="true">
            <AlertTriangle size={20} />
          </div>
          <div>
            <p className="dm-kpi-card__label">Crítico</p>
            <p className="dm-kpi-card__value">{resumo.critico}</p>
          </div>
        </button>
        <button
          type="button"
          className={`dm-card dm-kpi-card dm-kpi-card--action${statusFiltro === "ATENÇÃO" ? " is-active" : ""}`}
          onClick={() => setStatusFiltro((current) => (current === "ATENÇÃO" ? "TODOS" : "ATENÇÃO"))}
        >
          <div className="dm-kpi-card__icon dm-kpi-card__icon--warning" aria-hidden="true">
            <AlertTriangle size={20} />
          </div>
          <div>
            <p className="dm-kpi-card__label">Atenção</p>
            <p className="dm-kpi-card__value">{resumo.atencao}</p>
          </div>
        </button>
        <button
          type="button"
          className={`dm-card dm-kpi-card dm-kpi-card--action${statusFiltro === "OK" ? " is-active" : ""}`}
          onClick={() => setStatusFiltro((current) => (current === "OK" ? "TODOS" : "OK"))}
        >
          <div className="dm-kpi-card__icon dm-kpi-card__icon--success" aria-hidden="true">
            <AlertTriangle size={20} />
          </div>
          <div>
            <p className="dm-kpi-card__label">OK</p>
            <p className="dm-kpi-card__value">{resumo.ok}</p>
          </div>
        </button>
        <article className="dm-card dm-kpi-card">
          <div className="dm-kpi-card__icon" aria-hidden="true">
            <LineChart size={20} />
          </div>
          <div>
            <p className="dm-kpi-card__label">Pares monitorados</p>
            <p className="dm-kpi-card__value">{resumo.total}</p>
            <p className="dm-kpi-card__hint">{ultimas.length} últimas reposições na filial</p>
          </div>
        </article>
      </section>

      <FilterBar>
        <label className="dm-field">
          <span>Ferramenta</span>
          <input
            value={ferramentaFiltro}
            onChange={(event) => setFerramentaFiltro(event.target.value)}
            placeholder="Código…"
          />
        </label>
        <label className="dm-field">
          <span>Peça</span>
          <input
            value={pecaFiltro}
            onChange={(event) => setPecaFiltro(event.target.value)}
            placeholder="Código…"
          />
        </label>
        <label className="dm-field">
          <span>Status</span>
          <select
            value={statusFiltro}
            onChange={(event) => setStatusFiltro(event.target.value as StatusFilter)}
          >
            {STATUS_FILTERS.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </label>
        <button type="button" className="dm-ghost-btn" onClick={clearFilters}>
          <X size={16} />
          Limpar
        </button>
        <button type="button" className="dm-ghost-btn" onClick={() => void loadReport()} disabled={loading}>
          <Search size={16} />
          Recarregar
        </button>
      </FilterBar>

      {error ? <StateBox variant="error">{error}</StateBox> : null}

      <section className="dm-card dm-report-table-card">
        <SectionTabs
          ariaLabel="Relatório preventivo"
          activeId={activeTab}
          onChange={handleTabChange}
          tabs={[
            { id: "alertas", label: "Alertas preventivos", count: alertasFiltrados.length },
            { id: "ultimas", label: "Últimas reposições", count: ultimasFiltradas.length },
            {
              id: "detalhe",
              label: "Detalhe preventivo",
              count: selection ? 1 : undefined,
            },
          ]}
        />

        <div key={activeTab} className="dm-content-transition">
          {activeTab === "alertas" ? (
            <DataTableSection
              embedded
              title="Ranking preventivo"
              hint="Clique em uma linha para abrir a aba Detalhe preventivo."
              columns={alertasColumns}
              rows={alertasFiltrados}
              loading={loading}
              emptyMessage="Nenhum alerta — registre reposições para gerar preventiva."
              getRowKey={(item) => `${item.codigo_ferramenta}-${item.codigo_peca}`}
              getRowClassName={(item) =>
                isRowSelected(item.codigo_ferramenta, item.codigo_peca) ? "is-selected" : undefined
              }
              onRowClick={handleSelectAlerta}
            />
          ) : null}

          {activeTab === "ultimas" ? (
            <DataTableSection
              embedded
              title="Últimas reposições por peça"
              hint="Clique em uma linha para abrir o detalhe preventivo."
              columns={ultimasColumns}
              rows={ultimasFiltradas}
              loading={loading}
              emptyMessage="Nenhuma reposição registrada nesta filial."
              getRowKey={(item) => item.reposicao_id}
              getRowClassName={(item) =>
                isRowSelected(item.codigo_ferramenta, item.codigo_peca) ? "is-selected" : undefined
              }
              onRowClick={handleSelectUltima}
            />
          ) : null}

          {activeTab === "detalhe" ? (
            <PreventivaDetailPanel
              layout="page"
              codigoFerramenta={selection?.codigo_ferramenta ?? ""}
              codigoPeca={selection?.codigo_peca ?? ""}
              data={selection ? detailData : null}
              loading={detailLoading}
              onNavigate={onNavigate}
              onClose={handleCloseDetail}
            />
          ) : null}
        </div>
      </section>
    </MaintenanceShell>
  );
}
