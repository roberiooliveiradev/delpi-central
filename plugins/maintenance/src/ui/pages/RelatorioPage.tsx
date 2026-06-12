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
import { useServerTable } from "../../hooks/useServerTable";
import { resolveFilialDisplayName } from "../../utils/maintenanceFilialSelection";
import { formatCodigoDescricao } from "../../utils/pecaOptions";
import {
  fetchComponentes,
  fetchFerramenta,
  fetchPecas,
  fetchPreventivaAlertas,
  fetchPreventivaHistorico,
  fetchPreventivaResumo,
  fetchUltimasReposicoes,
  type PreventivaAlerta,
  type PreventivaResumo,
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

const EMPTY_RESUMO: PreventivaResumo = {
  critico: 0,
  atencao: 0,
  ok: 0,
  sem_status: 0,
  total: 0,
};

function CodigoDescricaoCell({
  codigo,
  descricao,
}: {
  codigo: string;
  descricao?: string | null;
}) {
  const label = descricao?.trim();
  if (!label) {
    return <span>{codigo}</span>;
  }

  return (
    <span className="dm-datatable__codigo-descricao">
      <span className="dm-datatable__codigo-descricao__codigo">{codigo}</span>
      <span className="dm-datatable__codigo-descricao__descricao">{label}</span>
    </span>
  );
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
  const alertasTable = useServerTable({ defaultSortKey: "percentual", defaultSortDirection: "desc" });
  const ultimasTable = useServerTable({ defaultSortKey: "data", defaultSortDirection: "desc" });
  const [alertas, setAlertas] = useState<PreventivaAlerta[]>([]);
  const [alertasTotal, setAlertasTotal] = useState(0);
  const [ultimas, setUltimas] = useState<UltimaReposicaoItem[]>([]);
  const [ultimasTotal, setUltimasTotal] = useState(0);
  const [resumo, setResumo] = useState<PreventivaResumo>(EMPTY_RESUMO);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [detailData, setDetailData] = useState<PreventivaDetailData | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [alertasLoading, setAlertasLoading] = useState(false);
  const [ultimasLoading, setUltimasLoading] = useState(false);
  const [resumoLoading, setResumoLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [alertasError, setAlertasError] = useState<string | null>(null);
  const [ultimasError, setUltimasError] = useState<string | null>(null);
  const [ferramentaFiltro, setFerramentaFiltro] = useState("");
  const [pecaFiltro, setPecaFiltro] = useState("");
  const [statusFiltro, setStatusFiltro] = useState<StatusFilter>("TODOS");
  const [appliedFerramentaFiltro, setAppliedFerramentaFiltro] = useState("");
  const [appliedPecaFiltro, setAppliedPecaFiltro] = useState("");

  const loadResumo = useCallback(async () => {
    setResumoLoading(true);
    try {
      const data = await fetchPreventivaResumo(filial, getAccessToken);
      setResumo(data);
    } catch {
      setResumo(EMPTY_RESUMO);
    } finally {
      setResumoLoading(false);
    }
  }, [filial, getAccessToken]);

  const loadAlertas = useCallback(async () => {
    setAlertasLoading(true);
    setAlertasError(null);
    try {
      const data = await fetchPreventivaAlertas(
        filial,
        {
          page: alertasTable.query.page,
          pageSize: alertasTable.query.pageSize,
          sortKey: alertasTable.query.sortKey,
          sortDirection: alertasTable.query.sortDirection,
        },
        {
          ferramenta: appliedFerramentaFiltro.trim() || undefined,
          peca: appliedPecaFiltro.trim() || undefined,
          status: statusFiltro !== "TODOS" ? statusFiltro : undefined,
        },
        getAccessToken,
      );
      setAlertas(data.items ?? []);
      setAlertasTotal(data.total ?? 0);
    } catch (err) {
      setAlertasError(err instanceof Error ? err.message : "Falha ao carregar alertas.");
      setAlertas([]);
      setAlertasTotal(0);
    } finally {
      setAlertasLoading(false);
    }
  }, [
    alertasTable.query,
    appliedFerramentaFiltro,
    appliedPecaFiltro,
    filial,
    getAccessToken,
    statusFiltro,
  ]);

  const loadUltimas = useCallback(async () => {
    setUltimasLoading(true);
    setUltimasError(null);
    try {
      const data = await fetchUltimasReposicoes(
        filial,
        {
          page: ultimasTable.query.page,
          pageSize: ultimasTable.query.pageSize,
          sortKey: ultimasTable.query.sortKey,
          sortDirection: ultimasTable.query.sortDirection,
        },
        {
          ferramenta: appliedFerramentaFiltro.trim() || undefined,
          peca: appliedPecaFiltro.trim() || undefined,
        },
        getAccessToken,
      );
      setUltimas(data.items ?? []);
      setUltimasTotal(data.total ?? 0);
    } catch (err) {
      setUltimasError(err instanceof Error ? err.message : "Falha ao carregar últimas reposições.");
      setUltimas([]);
      setUltimasTotal(0);
    } finally {
      setUltimasLoading(false);
    }
  }, [appliedFerramentaFiltro, appliedPecaFiltro, filial, getAccessToken, ultimasTable.query]);

  const loadReport = useCallback(async () => {
    await Promise.all([loadResumo(), loadAlertas(), loadUltimas()]);
  }, [loadAlertas, loadResumo, loadUltimas]);

  useEffect(() => {
    setError(alertasError ?? ultimasError);
  }, [alertasError, ultimasError]);

  useEffect(() => {
    void loadResumo();
  }, [loadResumo]);

  useEffect(() => {
    void loadAlertas();
  }, [loadAlertas]);

  useEffect(() => {
    void loadUltimas();
  }, [loadUltimas]);

  useEffect(() => {
    alertasTable.resetPage();
    ultimasTable.resetPage();
    setAppliedFerramentaFiltro("");
    setAppliedPecaFiltro("");
    setFerramentaFiltro("");
    setPecaFiltro("");
    setStatusFiltro("TODOS");
  }, [filial, alertasTable.resetPage, ultimasTable.resetPage]);

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
          fetchComponentes(next.codigo_ferramenta, filial, {}, getAccessToken).catch(() => ({
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

  const applyFilters = () => {
    setAppliedFerramentaFiltro(ferramentaFiltro);
    setAppliedPecaFiltro(pecaFiltro);
    alertasTable.resetPage();
    ultimasTable.resetPage();
  };

  const clearFilters = () => {
    setFerramentaFiltro("");
    setPecaFiltro("");
    setStatusFiltro("TODOS");
    setAppliedFerramentaFiltro("");
    setAppliedPecaFiltro("");
    alertasTable.resetPage();
    ultimasTable.resetPage();
  };

  useEffect(() => {
    alertasTable.resetPage();
  }, [statusFiltro, alertasTable.resetPage]);

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
        sortable: true,
        sortValue: (item) => new Date(item.data_reposicao).getTime(),
        render: (item) => new Date(item.data_reposicao).toLocaleString("pt-BR"),
      },
      {
        key: "ferramenta",
        header: "Ferramenta",
        sortable: true,
        sortValue: (item) =>
          formatCodigoDescricao(item.codigo_ferramenta, item.descricao_ferramenta),
        render: (item) => (
          <CodigoDescricaoCell
            codigo={item.codigo_ferramenta}
            descricao={item.descricao_ferramenta}
          />
        ),
      },
      {
        key: "peca",
        header: "Peça",
        sortable: true,
        sortValue: (item) => formatCodigoDescricao(item.codigo_peca, item.descricao_peca),
        render: (item) => (
          <CodigoDescricaoCell codigo={item.codigo_peca} descricao={item.descricao_peca} />
        ),
      },
      {
        key: "golpes",
        header: "Golpes",
        sortable: true,
        sortValue: (item) => item.golpes,
        render: (item) => item.golpes.toLocaleString("pt-BR"),
        align: "right",
      },
    ],
    [],
  );

  const statusSortRank = (status: string) => {
    if (status === "CRÍTICO") return 0;
    if (status === "ATENÇÃO") return 1;
    if (status === "OK") return 2;
    return 3;
  };

  const alertasColumns = useMemo<DataTableColumn<PreventivaAlerta>[]>(
    () => [
      {
        key: "status",
        header: "Status",
        interactive: true,
        sortable: true,
        sortValue: (item) => statusSortRank(item.status),
        render: (item) => <StatusBadge status={item.status} />,
      },
      {
        key: "ferramenta",
        header: "Ferramenta",
        sortable: true,
        sortValue: (item) =>
          formatCodigoDescricao(item.codigo_ferramenta, item.descricao_ferramenta),
        render: (item) => (
          <CodigoDescricaoCell
            codigo={item.codigo_ferramenta}
            descricao={item.descricao_ferramenta}
          />
        ),
      },
      {
        key: "peca",
        header: "Peça",
        sortable: true,
        sortValue: (item) => formatCodigoDescricao(item.codigo_peca, item.descricao_peca),
        render: (item) => (
          <CodigoDescricaoCell codigo={item.codigo_peca} descricao={item.descricao_peca} />
        ),
      },
      {
        key: "ultima",
        header: "Última reposição",
        sortable: true,
        sortValue: (item) => new Date(item.data_ultima_reposicao).getTime(),
        render: (item) => new Date(item.data_ultima_reposicao).toLocaleString("pt-BR"),
      },
      {
        key: "golpes_atuais",
        header: "Golpes atuais",
        sortable: true,
        sortValue: (item) => item.golpes_atuais,
        render: (item) => item.golpes_atuais.toLocaleString("pt-BR"),
        align: "right",
      },
      {
        key: "media",
        header: "Média",
        sortable: true,
        sortValue: (item) => item.media_golpes,
        render: (item) => item.media_golpes.toLocaleString("pt-BR"),
        align: "right",
      },
      {
        key: "percentual",
        header: "% uso",
        sortable: true,
        sortValue: (item) => item.percentual_uso,
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
            disabled={alertasLoading || ultimasLoading || resumoLoading}
          >
            <RefreshCw
              size={16}
              className={alertasLoading || ultimasLoading || resumoLoading ? "dm-spin" : undefined}
            />
            {alertasLoading || ultimasLoading || resumoLoading ? "Carregando…" : "Atualizar"}
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
            <p className="dm-kpi-card__hint">{ultimasTotal} últimas reposições na filial</p>
          </div>
        </article>
      </section>

      <FilterBar>
        <label className="dm-field">
          <span>Ferramenta</span>
          <input
            value={ferramentaFiltro}
            onChange={(event) => setFerramentaFiltro(event.target.value)}
            placeholder="Código ou descrição…"
          />
        </label>
        <label className="dm-field">
          <span>Peça</span>
          <input
            value={pecaFiltro}
            onChange={(event) => setPecaFiltro(event.target.value)}
            placeholder="Código ou descrição…"
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
        <button type="button" className="dm-primary-btn" onClick={applyFilters}>
          <Search size={16} />
          Buscar
        </button>
        <button
          type="button"
          className="dm-ghost-btn"
          onClick={() => void loadReport()}
          disabled={alertasLoading || ultimasLoading || resumoLoading}
        >
          <RefreshCw size={16} />
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
            { id: "alertas", label: "Alertas preventivos", count: alertasTotal },
            { id: "ultimas", label: "Últimas reposições", count: ultimasTotal },
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
              rows={alertas}
              loading={alertasLoading}
              emptyMessage="Nenhum alerta — registre reposições para gerar preventiva."
              getRowKey={(item) => `${item.codigo_ferramenta}-${item.codigo_peca}`}
              getRowClassName={(item) =>
                isRowSelected(item.codigo_ferramenta, item.codigo_peca) ? "is-selected" : undefined
              }
              serverTable={{
                page: alertasTable.query.page,
                pageSize: alertasTable.query.pageSize,
                total: alertasTotal,
                onPageChange: alertasTable.setPage,
                sortKey: alertasTable.query.sortKey,
                sortDirection: alertasTable.query.sortDirection,
                onSortChange: alertasTable.handleSortChange,
              }}
              onRowClick={handleSelectAlerta}
            />
          ) : null}

          {activeTab === "ultimas" ? (
            <DataTableSection
              embedded
              title="Últimas reposições por peça"
              hint="Clique em uma linha para abrir o detalhe preventivo."
              columns={ultimasColumns}
              rows={ultimas}
              loading={ultimasLoading}
              emptyMessage="Nenhuma reposição registrada nesta filial."
              getRowKey={(item) => item.reposicao_id}
              getRowClassName={(item) =>
                isRowSelected(item.codigo_ferramenta, item.codigo_peca) ? "is-selected" : undefined
              }
              serverTable={{
                page: ultimasTable.query.page,
                pageSize: ultimasTable.query.pageSize,
                total: ultimasTotal,
                onPageChange: ultimasTable.setPage,
                sortKey: ultimasTable.query.sortKey,
                sortDirection: ultimasTable.query.sortDirection,
                onSortChange: ultimasTable.handleSortChange,
              }}
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
