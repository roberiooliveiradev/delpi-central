import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { AlertTriangle, CheckCircle2, CircleAlert, LineChart, RefreshCw, Search, X } from "lucide-react";
import {
  NativeTextControl,
  simpleKpiCardBemClasses,
  simpleKpiCardIconToneClass,
} from "@delpi/plugin-ui/index";

import {
  PreventivaDetailPanel,
  type PreventivaDetailData,
} from "../../components/PreventivaDetailPanel";
import { SectionTabs } from "../../components/SectionTabs";
import {
  type DataTableColumn,
  DataTableSection,
  FilterBar,
  KpiCard,
  MultiSelectField,
  StateBox,
  StatusBadge,
} from "../../components/data";
import { CONFIG_TOOLTIPS } from "../../content/configTooltips";
import { MAINTENANCE_ROUTES } from "../../constants/routes";
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
  fetchRevisaoProgramadaAlertas,
  fetchRevisaoProgramadaResumo,
  fetchUltimasReposicoes,
  registrarRevisaoProgramada,
  type PreventivaAlerta,
  type PreventivaResumo,
  type RevisaoProgramadaAlerta,
  type RevisaoProgramadaResumo,
  type UltimaReposicaoItem,
} from "../../data/api/maintenanceApi";
import { fromDateInputValue, toDateInputValue } from "../../utils/datetimeLocal";

type RelatorioPageProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  filialScope?: string;
  onNavigate: (path: string) => void;
};

type ListReportTab = "alertas" | "ultimas" | "revisoes";
type ReportTab = ListReportTab | "detalhe";
type StatusFilterValue = "CRÍTICO" | "ATENÇÃO" | "OK" | "SEM STATUS";
type RevisaoStatusFilterValue = "CRÍTICO" | "ATENÇÃO" | "OK" | "SEM STATUS";

type Selection = {
  codigo_ferramenta: string;
  codigo_peca: string;
};

const STATUS_OPTIONS: StatusFilterValue[] = ["CRÍTICO", "ATENÇÃO", "OK", "SEM STATUS"];
const REVISAO_STATUS_OPTIONS: RevisaoStatusFilterValue[] = ["CRÍTICO", "ATENÇÃO", "OK", "SEM STATUS"];

const EMPTY_REVISAO_RESUMO: RevisaoProgramadaResumo = {
  critico: 0,
  atencao: 0,
  ok: 0,
  sem_status: 0,
  total: 0,
};

function formatDateTime(value?: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleString("pt-BR");
}

function formatDate(value?: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleDateString("pt-BR");
}

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

const KPI_CN = simpleKpiCardBemClasses("dm", "kpi-card", { withBody: true, withSubtitle: true });

type FilterKpiTone = "danger" | "warning" | "success";

function FilterKpiButton({
  active,
  onClick,
  icon,
  title,
  value,
  tone,
}: {
  active: boolean;
  onClick: () => void;
  icon: ReactNode;
  title: string;
  value: string | number;
  tone: FilterKpiTone;
}) {
  return (
    <button
      type="button"
      className={`${KPI_CN.article} dm-filter-kpi${active ? " is-active" : ""}`}
      onClick={onClick}
    >
      <div className={`${KPI_CN.icon} ${simpleKpiCardIconToneClass("dm", tone)}`} aria-hidden="true">
        {icon}
      </div>
      {KPI_CN.body ? (
        <div className={KPI_CN.body}>
          <p className={KPI_CN.title}>{title}</p>
          <p className={KPI_CN.value}>{value}</p>
        </div>
      ) : null}
    </button>
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
  const revisoesTable = useServerTable({ defaultSortKey: "dias_restantes", defaultSortDirection: "asc" });
  const [alertas, setAlertas] = useState<PreventivaAlerta[]>([]);
  const [alertasTotal, setAlertasTotal] = useState(0);
  const [ultimas, setUltimas] = useState<UltimaReposicaoItem[]>([]);
  const [ultimasTotal, setUltimasTotal] = useState(0);
  const [revisoes, setRevisoes] = useState<RevisaoProgramadaAlerta[]>([]);
  const [revisoesTotal, setRevisoesTotal] = useState(0);
  const [resumo, setResumo] = useState<PreventivaResumo>(EMPTY_RESUMO);
  const [revisaoResumo, setRevisaoResumo] = useState<RevisaoProgramadaResumo>(EMPTY_REVISAO_RESUMO);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [detailData, setDetailData] = useState<PreventivaDetailData | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [alertasLoading, setAlertasLoading] = useState(false);
  const [ultimasLoading, setUltimasLoading] = useState(false);
  const [revisoesLoading, setRevisoesLoading] = useState(false);
  const [resumoLoading, setResumoLoading] = useState(false);
  const [revisaoResumoLoading, setRevisaoResumoLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [alertasError, setAlertasError] = useState<string | null>(null);
  const [ultimasError, setUltimasError] = useState<string | null>(null);
  const [revisoesError, setRevisoesError] = useState<string | null>(null);
  const [ferramentaFiltro, setFerramentaFiltro] = useState("");
  const [pecaFiltro, setPecaFiltro] = useState("");
  const [statusFiltro, setStatusFiltro] = useState<StatusFilterValue[]>([]);
  const [revisaoStatusFiltro, setRevisaoStatusFiltro] = useState<RevisaoStatusFilterValue[]>([]);
  const [feitoDrafts, setFeitoDrafts] = useState<Record<string, string>>({});
  const [feitoSavingId, setFeitoSavingId] = useState<string | null>(null);
  const [appliedFerramentaFiltro, setAppliedFerramentaFiltro] = useState("");
  const [appliedPecaFiltro, setAppliedPecaFiltro] = useState("");

  const statusOptions = useMemo(
    () => STATUS_OPTIONS.map((status) => ({ value: status, label: status })),
    [],
  );

  const revisaoStatusOptions = useMemo(
    () => REVISAO_STATUS_OPTIONS.map((status) => ({ value: status, label: status })),
    [],
  );

  const toggleStatusFiltro = useCallback((status: StatusFilterValue) => {
    setStatusFiltro((current) =>
      current.includes(status) ? current.filter((item) => item !== status) : [...current, status],
    );
  }, []);

  const toggleRevisaoStatusFiltro = useCallback((status: RevisaoStatusFilterValue) => {
    setRevisaoStatusFiltro((current) =>
      current.includes(status) ? current.filter((item) => item !== status) : [...current, status],
    );
  }, []);

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
          status: statusFiltro.length > 0 ? statusFiltro : undefined,
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

  const loadRevisaoResumo = useCallback(async () => {
    setRevisaoResumoLoading(true);
    try {
      const data = await fetchRevisaoProgramadaResumo(filial, getAccessToken);
      setRevisaoResumo(data);
    } catch {
      setRevisaoResumo(EMPTY_REVISAO_RESUMO);
    } finally {
      setRevisaoResumoLoading(false);
    }
  }, [filial, getAccessToken]);

  const loadRevisoes = useCallback(async () => {
    setRevisoesLoading(true);
    setRevisoesError(null);
    try {
      const data = await fetchRevisaoProgramadaAlertas(
        filial,
        {
          page: revisoesTable.query.page,
          pageSize: revisoesTable.query.pageSize,
          sortKey: revisoesTable.query.sortKey,
          sortDirection: revisoesTable.query.sortDirection,
        },
        {
          ferramenta: appliedFerramentaFiltro.trim() || undefined,
          status: revisaoStatusFiltro.length > 0 ? revisaoStatusFiltro : undefined,
        },
        getAccessToken,
      );
      setRevisoes(data.items ?? []);
      setRevisoesTotal(data.total ?? 0);
    } catch (err) {
      setRevisoesError(err instanceof Error ? err.message : "Falha ao carregar revisões programadas.");
      setRevisoes([]);
      setRevisoesTotal(0);
    } finally {
      setRevisoesLoading(false);
    }
  }, [
    appliedFerramentaFiltro,
    filial,
    getAccessToken,
    revisaoStatusFiltro,
    revisoesTable.query,
  ]);

  const loadReport = useCallback(async () => {
    await Promise.all([loadResumo(), loadAlertas(), loadUltimas(), loadRevisaoResumo(), loadRevisoes()]);
  }, [loadAlertas, loadResumo, loadRevisaoResumo, loadRevisoes, loadUltimas]);

  const resolveFeitoDate = useCallback(
    (item: RevisaoProgramadaAlerta) =>
      feitoDrafts[item.revisao_id] ?? toDateInputValue(new Date()),
    [feitoDrafts],
  );

  const handleMarcarRevisaoFeita = useCallback(
    async (item: RevisaoProgramadaAlerta) => {
      if (!canManageMiniApplicators) return;
      const feitoDate = resolveFeitoDate(item);
      const label = formatDate(fromDateInputValue(feitoDate));
      if (
        !window.confirm(
          `Registrar revisão feita em ${label} para ${item.codigo_ferramenta} e reprogramar a próxima?`,
        )
      ) {
        return;
      }
      setFeitoSavingId(item.revisao_id);
      setRevisoesError(null);
      try {
        await registrarRevisaoProgramada(
          item.revisao_id,
          filial,
          fromDateInputValue(feitoDate),
          getAccessToken,
        );
        setFeitoDrafts((prev) => {
          const next = { ...prev };
          delete next[item.revisao_id];
          return next;
        });
        await Promise.all([loadRevisaoResumo(), loadRevisoes()]);
      } catch (err) {
        setRevisoesError(err instanceof Error ? err.message : "Falha ao registrar revisão feita.");
      } finally {
        setFeitoSavingId(null);
      }
    },
    [
      canManageMiniApplicators,
      filial,
      getAccessToken,
      loadRevisaoResumo,
      loadRevisoes,
      resolveFeitoDate,
    ],
  );

  useEffect(() => {
    setError(alertasError ?? ultimasError ?? revisoesError);
  }, [alertasError, revisoesError, ultimasError]);

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
    void loadRevisaoResumo();
  }, [loadRevisaoResumo]);

  useEffect(() => {
    void loadRevisoes();
  }, [loadRevisoes]);

  useEffect(() => {
    alertasTable.resetPage();
    ultimasTable.resetPage();
    revisoesTable.resetPage();
    setAppliedFerramentaFiltro("");
    setAppliedPecaFiltro("");
    setFerramentaFiltro("");
    setPecaFiltro("");
    setStatusFiltro([]);
    setRevisaoStatusFiltro([]);
  }, [filial, alertasTable.resetPage, revisoesTable.resetPage, ultimasTable.resetPage]);

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
    revisoesTable.resetPage();
  };

  const clearFilters = () => {
    setFerramentaFiltro("");
    setPecaFiltro("");
    setStatusFiltro([]);
    setRevisaoStatusFiltro([]);
    setAppliedFerramentaFiltro("");
    setAppliedPecaFiltro("");
    alertasTable.resetPage();
    ultimasTable.resetPage();
    revisoesTable.resetPage();
  };

  useEffect(() => {
    alertasTable.resetPage();
  }, [statusFiltro, alertasTable.resetPage]);

  useEffect(() => {
    revisoesTable.resetPage();
  }, [revisaoStatusFiltro, revisoesTable.resetPage]);

  const handleTabChange = (id: string) => {
    const tab = id as ReportTab;
    setActiveTab(tab);
    if (tab === "alertas" || tab === "ultimas" || tab === "revisoes") {
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

  const revisoesColumns = useMemo<DataTableColumn<RevisaoProgramadaAlerta>[]>(() => {
    const columns: DataTableColumn<RevisaoProgramadaAlerta>[] = [
      {
        key: "status",
        header: "Status",
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
        key: "intervalo",
        header: "Intervalo",
        sortable: true,
        sortValue: (item) => item.intervalo_meses,
        render: (item) => `${item.intervalo_meses} mes(es)`,
        align: "right",
      },
      {
        key: "ultima",
        header: "Referência",
        sortable: true,
        sortValue: (item) => new Date(item.data_referencia ?? 0).getTime(),
        render: (item) => formatDateTime(item.data_referencia),
      },
      {
        key: "proxima",
        header: "Próxima revisão",
        sortable: true,
        sortValue: (item) => new Date(item.data_proxima_revisao ?? 0).getTime(),
        render: (item) => formatDate(item.data_proxima_revisao),
      },
      {
        key: "dias_restantes",
        header: "Dias restantes",
        sortable: true,
        sortValue: (item) => item.dias_restantes ?? 999999,
        render: (item) =>
          item.dias_restantes === null || item.dias_restantes === undefined
            ? "—"
            : item.dias_restantes.toLocaleString("pt-BR"),
        align: "right",
      },
    ];

    if (canManageMiniApplicators) {
      columns.push({
        key: "acoes",
        header: "Feito",
        headerHint: CONFIG_TOOLTIPS.revisaoRegistrar,
        className: "dm-datatable__col--revisao-feito",
        interactive: true,
        render: (item) => (
          <div className="dm-revisao-feito-actions">
            <NativeTextControl
              type="date"
              aria-label={`Data da revisão feita para ${item.codigo_ferramenta}`}
              value={resolveFeitoDate(item)}
              onChange={(value) =>
                setFeitoDrafts((prev) => ({
                  ...prev,
                  [item.revisao_id]: value,
                }))
              }
            />
            <button
              type="button"
              className="dm-ghost-btn dm-ghost-btn--sm"
              disabled={feitoSavingId === item.revisao_id}
              onClick={() => void handleMarcarRevisaoFeita(item)}
            >
              {feitoSavingId === item.revisao_id ? "Salvando…" : "Marcar feito"}
            </button>
          </div>
        ),
      });
    }

    return columns;
  }, [
    canManageMiniApplicators,
    feitoSavingId,
    handleMarcarRevisaoFeita,
    resolveFeitoDate,
  ]);

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

  const handleSelectRevisao = (item: RevisaoProgramadaAlerta) => {
    onNavigate(MAINTENANCE_ROUTES.miniAplicadorDetail(item.codigo_ferramenta));
  };

  const isRowSelected = (codigoFerramenta: string, codigoPeca: string) =>
    selection?.codigo_ferramenta === codigoFerramenta && selection?.codigo_peca === codigoPeca;

  return (
    <MaintenanceShell>
      <MiniAplicadoresPageHeader
        title="Relatório preventivo"
        subtitle="Preventiva por golpes, revisões programadas por tempo e detalhe por ferramenta/peça."
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
            disabled={alertasLoading || ultimasLoading || resumoLoading || revisoesLoading || revisaoResumoLoading}
          >
            <RefreshCw
              size={16}
              className={
                alertasLoading || ultimasLoading || resumoLoading || revisoesLoading || revisaoResumoLoading
                  ? "dm-spin"
                  : undefined
              }
            />
            {alertasLoading || ultimasLoading || resumoLoading || revisoesLoading || revisaoResumoLoading
              ? "Carregando…"
              : "Atualizar"}
          </button>
        }
      />

      <section className="dm-kpi-grid dm-kpi-grid--report">
        {listTab === "revisoes" ? (
          <>
            <FilterKpiButton
              active={revisaoStatusFiltro.includes("CRÍTICO")}
              onClick={() => toggleRevisaoStatusFiltro("CRÍTICO")}
              icon={<CircleAlert size={20} />}
              tone="danger"
              title="Revisão vencida"
              value={revisaoResumo.critico}
            />
            <FilterKpiButton
              active={revisaoStatusFiltro.includes("ATENÇÃO")}
              onClick={() => toggleRevisaoStatusFiltro("ATENÇÃO")}
              icon={<AlertTriangle size={20} />}
              tone="warning"
              title="Próxima do prazo"
              value={revisaoResumo.atencao}
            />
            <FilterKpiButton
              active={revisaoStatusFiltro.includes("OK")}
              onClick={() => toggleRevisaoStatusFiltro("OK")}
              icon={<CheckCircle2 size={20} />}
              tone="success"
              title="No prazo"
              value={revisaoResumo.ok}
            />
            <KpiCard
              title="Ferramentas programadas"
              value={String(revisaoResumo.total)}
              icon={<LineChart size={20} aria-hidden="true" />}
            />
          </>
        ) : (
          <>
            <FilterKpiButton
              active={statusFiltro.includes("CRÍTICO")}
              onClick={() => toggleStatusFiltro("CRÍTICO")}
              icon={<CircleAlert size={20} />}
              tone="danger"
              title="Crítico"
              value={resumo.critico}
            />
            <FilterKpiButton
              active={statusFiltro.includes("ATENÇÃO")}
              onClick={() => toggleStatusFiltro("ATENÇÃO")}
              icon={<AlertTriangle size={20} />}
              tone="warning"
              title="Atenção"
              value={resumo.atencao}
            />
            <FilterKpiButton
              active={statusFiltro.includes("OK")}
              onClick={() => toggleStatusFiltro("OK")}
              icon={<CheckCircle2 size={20} />}
              tone="success"
              title="OK"
              value={resumo.ok}
            />
            <KpiCard
              title="Pares monitorados"
              value={String(resumo.total)}
              subtitle={`${ultimasTotal} últimas reposições na filial`}
              icon={<LineChart size={20} aria-hidden="true" />}
            />
          </>
        )}
      </section>

      <FilterBar className="dm-filter-bar--relatorio">
        <label className="dm-field">
          <span>Ferramenta</span>
          <NativeTextControl
            value={ferramentaFiltro}
            onChange={setFerramentaFiltro}
            placeholder="Código ou descrição…"
          />
        </label>
        <label className="dm-field">
          <span>Peça</span>
          <NativeTextControl
            value={pecaFiltro}
            onChange={setPecaFiltro}
            placeholder="Código ou descrição…"
            disabled={listTab === "revisoes"}
          />
        </label>
        <MultiSelectField
          className="dm-field--multi-select"
          label="Status"
          emptyLabel="Todos"
          options={listTab === "revisoes" ? revisaoStatusOptions : statusOptions}
          selectedValues={listTab === "revisoes" ? revisaoStatusFiltro : statusFiltro}
          onChange={(values) =>
            listTab === "revisoes"
              ? setRevisaoStatusFiltro(values as RevisaoStatusFilterValue[])
              : setStatusFiltro(values as StatusFilterValue[])
          }
        />
        <div className="dm-filter-bar__actions">
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
            disabled={alertasLoading || ultimasLoading || resumoLoading || revisoesLoading || revisaoResumoLoading}
          >
            <RefreshCw size={16} />
            Recarregar
          </button>
        </div>
      </FilterBar>

      {error ? (
        <StateBox variant="error" onDismiss={() => setError(null)}>
          {error}
        </StateBox>
      ) : null}

      <section className="dm-card dm-report-table-card">
        <SectionTabs
          ariaLabel="Relatório preventivo"
          activeId={activeTab}
          onChange={handleTabChange}
          tabs={[
            { id: "alertas", label: "Alertas por golpes", count: alertasTotal },
            { id: "revisoes", label: "Revisões programadas", count: revisoesTotal },
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
              columnPreferencesKey="maintenance:RelatorioPage:ranking-preventivo:v1"
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

          {activeTab === "revisoes" ? (
            <DataTableSection
              columnPreferencesKey="maintenance:RelatorioPage:revis-es-programadas-1:v1"
              embedded
              title="Revisões programadas"
              hint="Clique em uma linha para abrir a ferramenta. Marque a revisão como feita para reprogramar a próxima."
              columns={revisoesColumns}
              rows={revisoes}
              loading={revisoesLoading}
              emptyMessage="Nenhuma revisão programada — configure na ferramenta desejada."
              getRowKey={(item) => item.revisao_id}
              onRowClick={handleSelectRevisao}
              serverTable={{
                page: revisoesTable.query.page,
                pageSize: revisoesTable.query.pageSize,
                total: revisoesTotal,
                onPageChange: revisoesTable.setPage,
                sortKey: revisoesTable.query.sortKey,
                sortDirection: revisoesTable.query.sortDirection,
                onSortChange: revisoesTable.handleSortChange,
              }}
            />
          ) : null}

          {activeTab === "ultimas" ? (
            <DataTableSection
              columnPreferencesKey="maintenance:RelatorioPage:ltimas-reposi-es-por-pe-a-2:v1"
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
