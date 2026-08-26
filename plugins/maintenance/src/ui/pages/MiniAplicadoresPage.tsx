import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Hammer, Loader2, Lock, PlusCircle, RefreshCw } from "lucide-react";
import { NativeCheckboxControl, NativeTextControl } from "@delpi/plugin-ui/index";

import { type DataTableColumn, BrDateInput, BrDatetimeInput, CodigoDescricaoCell, DataTableSection, FilterBar, MultiSelectField, StateBox } from "../../components/data";
import { MAINTENANCE_ROUTES } from "../../constants/routes";
import {
  useMaintenanceActiveFilial,
  useOperationalFilial,
} from "../../hooks/useMaintenanceScope";
import { useServerTable } from "../../hooks/useServerTable";
import { FerramentaAuditoriaSection } from "../../components/FerramentaAuditoriaSection";
import { FerramentasPorPecaSearchCard } from "../../components/FerramentasPorPecaSearchCard";
import { FerramentaOndeUsadoSection } from "../../components/FerramentaOndeUsadoSection";
import { FerramentaRevisaoProgramadaSection } from "../../components/FerramentaRevisaoProgramadaSection";
import { ComponentesEstoqueSection } from "../../components/ComponentesEstoqueSection";
import { ReposicoesGolpesChart } from "../../components/ReposicoesGolpesChart";
import { FerramentaReposicaoIndicadores } from "../../components/FerramentaReposicaoIndicadores";
import {
  DmNativeSelectField,
  DmNativeTextAreaField,
  DmNativeTextField,
} from "../../components/dmFormFields";
import {
  createReposicao,
  deleteReposicao,
  fetchAllReposicoes,
  fetchComponentes,
  fetchFerramentas,
  fetchMotivos,
  fetchReposicoes,
  suggestGolpes,
  updateReposicao,
  type ComponenteItem,
  type FerramentaItem,
  type MotivoItem,
  type ReposicaoItem,
} from "../../data/api/maintenanceApi";
import { MaintenanceActionButton, MaintenanceFieldLabel } from "../../app/maintenanceUi";
import { MaintenanceHeroFreshness } from "../../components/MaintenanceHeroFreshness";
import { useMaintenanceFreshness } from "../../hooks/useMaintenanceFreshness";
import { DM_HELP } from "../../content/helpTooltips";
import { MAINTENANCE_LIST_LAYOUT_KEYS } from "../../content/listLayoutKeys";
import { FerramentaListCard, ReposicaoListCard } from "../../components/listCards/MaintenanceListCards";
import { MaintenanceMiniAplicadoresHero } from "../../components/MaintenanceMiniAplicadoresHero";
import {
  fromDatetimeLocalValue,
  isValidDateRange,
  matchesReposicaoDateRange,
  toDatetimeLocalValue,
} from "../../utils/datetimeLocal";
import { resolveFilialDisplayName } from "../../utils/maintenanceFilialSelection";
import { MAX_LIST_PAGE_SIZE } from "../../utils/listQuery";
import {
  buildPecaDescricaoMap,
  componentesToPecaOptions,
  formatPecaLabel,
  reposicoesToPecaOptions,
} from "../../utils/pecaOptions";
import {
  hasReposicaoFormErrors,
  mapReposicaoApiError,
  validateReposicaoForm,
  type ReposicaoFormErrors,
} from "../../utils/reposicaoFormValidation";

type MiniAplicadoresPageProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  filialScope?: string;
  onNavigate: (path: string) => void;
  codigoFerramenta?: string;
};

function datetimeParamFromLocal(value: string): string | undefined {
  if (!value) return undefined;
  return value.length === 16 ? `${value}:00` : value;
}

export function MiniAplicadoresPage({
  getAccessToken,
  pathname,
  filialScope,
  onNavigate,
  codigoFerramenta,
}: MiniAplicadoresPageProps) {
  const filial = useOperationalFilial(getAccessToken, filialScope) ?? "01";
  const { canManageMiniApplicators, filiais } = useMaintenanceActiveFilial(getAccessToken, filialScope);
  const filialDisplayName = resolveFilialDisplayName(filiais, filial);
  const { lastUpdatedAt, touchFreshness } = useMaintenanceFreshness();
  const [descricao, setDescricao] = useState("");
  const [codigo, setCodigo] = useState("");
  const [incluirBloqueados, setIncluirBloqueados] = useState(false);
  const [selectedPecaCodigo, setSelectedPecaCodigo] = useState<string | null>(null);
  const [selectedPecaDescricao, setSelectedPecaDescricao] = useState("");
  const [items, setItems] = useState<FerramentaItem[]>([]);
  const [total, setTotal] = useState(0);
  const ferramentasTable = useServerTable({ defaultSortKey: "codigo" });
  const reposicoesTable = useServerTable({ defaultSortKey: "data", defaultSortDirection: "desc" });
  const [estruturaComponentes, setEstruturaComponentes] = useState<ComponenteItem[]>([]);
  const [allReposicoesChart, setAllReposicoesChart] = useState<ReposicaoItem[]>([]);
  const [chartLoading, setChartLoading] = useState(false);
  const [showReposicaoForm, setShowReposicaoForm] = useState(false);
  const reposicaoFormRef = useRef<HTMLElement>(null);
  const historicoSectionRef = useRef<HTMLDivElement>(null);
  const scrollHistoricoOnCloseRef = useRef(false);
  const [motivos, setMotivos] = useState<MotivoItem[]>([]);
  const [reposicoes, setReposicoes] = useState<ReposicaoItem[]>([]);
  const [reposicoesTotal, setReposicoesTotal] = useState(0);
  const [codigoPeca, setCodigoPeca] = useState("");
  const [golpes, setGolpes] = useState(0);
  const [motivoId, setMotivoId] = useState<string | "">("");
  const [observacao, setObservacao] = useState("");
  const [dataReposicao, setDataReposicao] = useState(() => toDatetimeLocalValue(new Date()));
  const [dataUltimaReposicao, setDataUltimaReposicao] = useState("");
  const [editingReposicaoId, setEditingReposicaoId] = useState<string | null>(null);
  const [filtroHistoricoPeca, setFiltroHistoricoPeca] = useState<string[]>([]);
  const [filtroHistoricoMotivo, setFiltroHistoricoMotivo] = useState<string[]>([]);
  const [filtroHistoricoDataInicial, setFiltroHistoricoDataInicial] = useState("");
  const [filtroHistoricoDataFinal, setFiltroHistoricoDataFinal] = useState("");
  const [filtroHistoricoPecaDraft, setFiltroHistoricoPecaDraft] = useState<string[]>([]);
  const [filtroHistoricoMotivoDraft, setFiltroHistoricoMotivoDraft] = useState<string[]>([]);
  const [filtroHistoricoDataInicialDraft, setFiltroHistoricoDataInicialDraft] = useState("");
  const [filtroHistoricoDataFinalDraft, setFiltroHistoricoDataFinalDraft] = useState("");
  const [ferramentasLoading, setFerramentasLoading] = useState(false);
  const [detalheLoading, setDetalheLoading] = useState(false);
  const [reposicoesLoading, setReposicoesLoading] = useState(false);
  const [golpesLoading, setGolpesLoading] = useState(false);
  const golpesRequestRef = useRef(0);
  const editingReposicaoRef = useRef<ReposicaoItem | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reposicaoFormErrors, setReposicaoFormErrors] = useState<ReposicaoFormErrors>({});
  const [success, setSuccess] = useState<string | null>(null);
  const [detalheVersion, setDetalheVersion] = useState(0);

  const pecaDescricaoMap = useMemo(
    () => buildPecaDescricaoMap([estruturaComponentes]),
    [estruturaComponentes],
  );

  const pecasReposicao = useMemo(() => {
    const options = componentesToPecaOptions(estruturaComponentes);
    if (codigoPeca && !options.some((item) => item.codigo === codigoPeca)) {
      options.push({ codigo: codigoPeca, descricao: pecaDescricaoMap[codigoPeca] ?? "" });
      options.sort((first, second) => first.codigo.localeCompare(second.codigo, "pt-BR"));
    }
    return options;
  }, [estruturaComponentes, codigoPeca, pecaDescricaoMap]);

  const pecasHistorico = useMemo(
    () => reposicoesToPecaOptions(allReposicoesChart, pecaDescricaoMap),
    [allReposicoesChart, pecaDescricaoMap],
  );

  const motivosHistorico = useMemo(() => {
    const byId = new Map(motivos.map((item) => [item.motivo_id, item]));
    const seen = new Set<string>();
    const options: MotivoItem[] = [];
    for (const item of allReposicoesChart) {
      if (seen.has(item.motivo_id)) continue;
      seen.add(item.motivo_id);
      const motivo = byId.get(item.motivo_id);
      options.push(
        motivo ?? {
          motivo_id: item.motivo_id,
          descricao: item.motivo_descricao ?? String(item.motivo_id),
        },
      );
    }
    return options.sort((first, second) =>
      first.descricao.localeCompare(second.descricao, "pt-BR"),
    );
  }, [allReposicoesChart, motivos]);

  const pecaHistoricoOptions = useMemo(
    () =>
      pecasHistorico.map((peca) => ({
        value: peca.codigo,
        label: formatPecaLabel(peca),
      })),
    [pecasHistorico],
  );

  const motivoHistoricoOptions = useMemo(
    () =>
      motivosHistorico.map((motivo) => ({
        value: String(motivo.motivo_id),
        label: motivo.descricao,
      })),
    [motivosHistorico],
  );

  const chartReposicoes = useMemo(() => {
    return allReposicoesChart.filter((item) => {
      if (filtroHistoricoPeca.length > 0 && !filtroHistoricoPeca.includes(item.codigo_peca)) {
        return false;
      }
      if (filtroHistoricoMotivo.length > 0 && !filtroHistoricoMotivo.includes(item.motivo_id)) {
        return false;
      }
      if (
        !matchesReposicaoDateRange(
          item.data_reposicao,
          filtroHistoricoDataInicial,
          filtroHistoricoDataFinal,
        )
      ) {
        return false;
      }
      return true;
    });
  }, [
    allReposicoesChart,
    filtroHistoricoDataFinal,
    filtroHistoricoDataInicial,
    filtroHistoricoMotivo,
    filtroHistoricoPeca,
  ]);

  const historicoFiltrosAtivos = Boolean(
    filtroHistoricoPeca.length > 0 ||
      filtroHistoricoMotivo.length > 0 ||
      filtroHistoricoDataInicial ||
      filtroHistoricoDataFinal,
  );

  const resetReposicaoForm = useCallback(() => {
    golpesRequestRef.current += 1;
    setGolpesLoading(false);
    editingReposicaoRef.current = null;
    setEditingReposicaoId(null);
    setCodigoPeca(pecasReposicao[0]?.codigo ?? "");
    setGolpes(0);
    setMotivoId("");
    setObservacao("");
    setDataReposicao(toDatetimeLocalValue(new Date()));
    setDataUltimaReposicao("");
    setReposicaoFormErrors({});
  }, [pecasReposicao]);

  const openNovaReposicao = useCallback(() => {
    golpesRequestRef.current += 1;
    setGolpesLoading(false);
    editingReposicaoRef.current = null;
    setEditingReposicaoId(null);
    setCodigoPeca(pecasReposicao[0]?.codigo ?? "");
    setGolpes(0);
    setMotivoId("");
    setObservacao("");
    setDataReposicao(toDatetimeLocalValue(new Date()));
    setDataUltimaReposicao("");
    setSuccess(null);
    setError(null);
    setReposicaoFormErrors({});
    setShowReposicaoForm(true);
  }, [pecasReposicao]);

  const closeReposicaoForm = useCallback((options?: { scrollToHistorico?: boolean }) => {
    resetReposicaoForm();
    scrollHistoricoOnCloseRef.current = options?.scrollToHistorico ?? true;
    setShowReposicaoForm(false);
  }, [resetReposicaoForm]);

  useEffect(() => {
    if (editingReposicaoId) {
      setShowReposicaoForm(true);
    }
  }, [editingReposicaoId]);

  useEffect(() => {
    if (showReposicaoForm) {
      window.requestAnimationFrame(() => {
        reposicaoFormRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
      return;
    }
    if (!scrollHistoricoOnCloseRef.current) return;
    scrollHistoricoOnCloseRef.current = false;
    window.requestAnimationFrame(() => {
      historicoSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }, [showReposicaoForm]);

  const refreshSuggestGolpes = useCallback(
    async (options: {
      codigoPecaValue: string;
      dataReposicaoValue: string;
      dataUltimaValue: string;
    }) => {
      if (!codigoFerramenta || !options.codigoPecaValue) return;
      const requestId = ++golpesRequestRef.current;
      setGolpesLoading(true);
      try {
        const data = await suggestGolpes(
          {
            filial,
            codigo_ferramenta: codigoFerramenta,
            codigo_peca: options.codigoPecaValue,
            data_inicial: datetimeParamFromLocal(options.dataUltimaValue),
            data_final: datetimeParamFromLocal(options.dataReposicaoValue),
          },
          getAccessToken,
        );
        if (requestId !== golpesRequestRef.current) return;
        if (!editingReposicaoRef.current && data.data_ultima_reposicao && !options.dataUltimaValue) {
          setDataUltimaReposicao(toDatetimeLocalValue(data.data_ultima_reposicao));
        }
        setGolpes(data.total_golpes ?? 0);
      } catch {
        if (requestId !== golpesRequestRef.current) return;
        if (!editingReposicaoRef.current) setGolpes(0);
      } finally {
        if (requestId === golpesRequestRef.current) {
          setGolpesLoading(false);
        }
      }
    },
    [codigoFerramenta, editingReposicaoId, filial, getAccessToken],
  );

  const loadFerramentas = useCallback(async () => {
    setFerramentasLoading(true);
    setError(null);
    try {
      const data = await fetchFerramentas(
        {
          codigo: selectedPecaCodigo ? undefined : codigo.trim() || undefined,
          descricao: selectedPecaCodigo ? undefined : descricao.trim() || undefined,
          codigoPeca: selectedPecaCodigo ?? undefined,
          incluirBloqueados,
          filial,
          page: ferramentasTable.query.page,
          pageSize: ferramentasTable.query.pageSize,
          sortKey: ferramentasTable.query.sortKey,
          sortDirection: ferramentasTable.query.sortDirection,
        },
        getAccessToken,
      );
      setItems(data.items ?? []);
      setTotal(data.total ?? 0);
      touchFreshness();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar ferramentas.");
      setItems([]);
      setTotal(0);
    } finally {
      setFerramentasLoading(false);
    }
  }, [
    codigo,
    descricao,
    filial,
    incluirBloqueados,
    selectedPecaCodigo,
    ferramentasTable.query,
    getAccessToken,
    touchFreshness,
  ]);

  const loadHistoricoChart = useCallback(
    async (total: number) => {
      if (!codigoFerramenta || total <= 0) {
        setAllReposicoesChart([]);
        return;
      }
      setChartLoading(true);
      try {
        const items = await fetchAllReposicoes(
          {
            filial,
            codigo_ferramenta: codigoFerramenta,
            sortKey: "data",
            sortDirection: "asc",
            maxItems: total,
          },
          getAccessToken,
        );
        setAllReposicoesChart(items);
      } catch {
        setAllReposicoesChart([]);
      } finally {
        setChartLoading(false);
      }
    },
    [codigoFerramenta, filial, getAccessToken],
  );

  const refreshHistoricoChart = useCallback(async () => {
    if (!codigoFerramenta) {
      setAllReposicoesChart([]);
      return;
    }
    try {
      const preview = await fetchReposicoes(
        {
          filial,
          codigo_ferramenta: codigoFerramenta,
          page: 1,
          pageSize: 1,
          sortKey: "data",
          sortDirection: "desc",
        },
        getAccessToken,
      );
      await loadHistoricoChart(preview.total ?? 0);
    } catch {
      setAllReposicoesChart([]);
    }
  }, [codigoFerramenta, filial, getAccessToken, loadHistoricoChart]);

  const loadReposicoesTable = useCallback(async (): Promise<number> => {
    if (!codigoFerramenta) return 0;
    setReposicoesLoading(true);
    try {
      const data = await fetchReposicoes(
        {
          filial,
          codigo_ferramenta: codigoFerramenta,
          codigo_peca: filtroHistoricoPeca.length > 0 ? filtroHistoricoPeca : undefined,
          motivo_id: filtroHistoricoMotivo.length > 0 ? filtroHistoricoMotivo : undefined,
          data_inicial: filtroHistoricoDataInicial || undefined,
          data_final: filtroHistoricoDataFinal || undefined,
          page: reposicoesTable.query.page,
          pageSize: reposicoesTable.query.pageSize,
          sortKey: reposicoesTable.query.sortKey,
          sortDirection: reposicoesTable.query.sortDirection,
        },
        getAccessToken,
      );
      const total = data.total ?? 0;
      setReposicoes(data.items ?? []);
      setReposicoesTotal(total);
      return total;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar reposições.");
      setReposicoes([]);
      setReposicoesTotal(0);
      return 0;
    } finally {
      setReposicoesLoading(false);
    }
  }, [
    codigoFerramenta,
    filial,
    filtroHistoricoPeca,
    filtroHistoricoMotivo,
    filtroHistoricoDataInicial,
    filtroHistoricoDataFinal,
    getAccessToken,
    reposicoesTable.query,
  ]);


  const loadDetalheBase = useCallback(async () => {
    if (!codigoFerramenta) return;
    setDetalheLoading(true);
    setError(null);
    try {
      const [motivosData, componentesData] = await Promise.all([
        fetchMotivos(filial, { page: 1, pageSize: 200 }, {}, getAccessToken),
        fetchComponentes(
          codigoFerramenta,
          filial,
          { page: 1, pageSize: MAX_LIST_PAGE_SIZE, sortKey: "nivel", sortDirection: "asc" },
          getAccessToken,
        ),
      ]);
      const estruturaItems = componentesData.items ?? [];
      const pecaItems = componentesToPecaOptions(estruturaItems);
      setMotivos(motivosData.items ?? []);
      setEstruturaComponentes(estruturaItems);
      setCodigoPeca((current) => {
        if (current && pecaItems.some((item) => item.codigo === current)) return current;
        return pecaItems[0]?.codigo ?? "";
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar detalhe.");
    } finally {
      setDetalheLoading(false);
    }
  }, [codigoFerramenta, filial, getAccessToken]);

  const loadDetalhe = useCallback(async () => {
    setError(null);
    await Promise.all([
      loadDetalheBase(),
      loadReposicoesTable(),
      refreshHistoricoChart(),
    ]);
    setDetalheVersion((current) => current + 1);
    touchFreshness();
  }, [loadDetalheBase, loadReposicoesTable, refreshHistoricoChart, touchFreshness]);

  const handleRevisaoFeedback = useCallback((message: { type: "success" | "error"; text: string }) => {
    if (message.type === "success") {
      setSuccess(message.text);
      setError(null);
      return;
    }
    setError(message.text);
    setSuccess(null);
  }, []);

  const applyHistoricoFilters = useCallback(() => {
    if (!isValidDateRange(filtroHistoricoDataInicialDraft, filtroHistoricoDataFinalDraft)) {
      setError("A data inicial não pode ser posterior à data final.");
      return;
    }
    setError(null);
    setFiltroHistoricoPeca(filtroHistoricoPecaDraft);
    setFiltroHistoricoMotivo(filtroHistoricoMotivoDraft);
    setFiltroHistoricoDataInicial(filtroHistoricoDataInicialDraft);
    setFiltroHistoricoDataFinal(filtroHistoricoDataFinalDraft);
    reposicoesTable.resetPage();
  }, [
    filtroHistoricoDataFinalDraft,
    filtroHistoricoDataInicialDraft,
    filtroHistoricoMotivoDraft,
    filtroHistoricoPecaDraft,
    reposicoesTable.resetPage,
  ]);

  useEffect(() => {
    if (!codigoFerramenta) return;
    setFiltroHistoricoPeca([]);
    setFiltroHistoricoMotivo([]);
    setFiltroHistoricoDataInicial("");
    setFiltroHistoricoDataFinal("");
    setFiltroHistoricoPecaDraft([]);
    setFiltroHistoricoMotivoDraft([]);
    setFiltroHistoricoDataInicialDraft("");
    setFiltroHistoricoDataFinalDraft("");
    setEditingReposicaoId(null);
    scrollHistoricoOnCloseRef.current = false;
    setShowReposicaoForm(false);
    reposicoesTable.resetPage();
    void loadDetalheBase();
  }, [
    codigoFerramenta,
    filial,
    loadDetalheBase,
    reposicoesTable.resetPage,
  ]);

  useEffect(() => {
    if (!codigoFerramenta) return;
    void loadReposicoesTable();
  }, [codigoFerramenta, loadReposicoesTable]);

  useEffect(() => {
    if (!codigoFerramenta) return;
    void refreshHistoricoChart();
  }, [codigoFerramenta, filial, refreshHistoricoChart]);


  useEffect(() => {
    if (codigoFerramenta) return;
    void loadFerramentas();
  }, [codigoFerramenta, loadFerramentas]);

  useEffect(() => {
    if (codigoFerramenta) return;
    ferramentasTable.resetPage();
  }, [filial, codigoFerramenta, ferramentasTable.resetPage]);

  useEffect(() => {
    if (!codigoFerramenta || !codigoPeca || !showReposicaoForm || editingReposicaoId) return;
    void refreshSuggestGolpes({
      codigoPecaValue: codigoPeca,
      dataReposicaoValue: dataReposicao,
      dataUltimaValue: dataUltimaReposicao,
    });
  }, [
    codigoFerramenta,
    codigoPeca,
    dataReposicao,
    dataUltimaReposicao,
    editingReposicaoId,
    refreshSuggestGolpes,
    showReposicaoForm,
  ]);

  useEffect(() => {
    setFiltroHistoricoMotivo((current) =>
      current.filter((motivoId) => motivosHistorico.some((item) => item.motivo_id === motivoId)),
    );
    setFiltroHistoricoMotivoDraft((current) =>
      current.filter((motivoId) => motivosHistorico.some((item) => item.motivo_id === motivoId)),
    );
  }, [motivosHistorico]);

  useEffect(() => {
    setFiltroHistoricoPeca((current) =>
      current.filter((codigo) => pecasHistorico.some((item) => item.codigo === codigo)),
    );
    setFiltroHistoricoPecaDraft((current) =>
      current.filter((codigo) => pecasHistorico.some((item) => item.codigo === codigo)),
    );
  }, [pecasHistorico]);

  async function handleSearch(event: React.FormEvent) {
    event.preventDefault();
    setSelectedPecaCodigo(null);
    setSelectedPecaDescricao("");
    ferramentasTable.resetPage();
    await loadFerramentas();
  }

  const handleSelectPeca = useCallback(
    (peca: { codigo: string; descricao: string } | null) => {
      setSelectedPecaCodigo(peca?.codigo ?? null);
      setSelectedPecaDescricao(peca?.descricao ?? "");
      ferramentasTable.resetPage();
    },
    [ferramentasTable.resetPage],
  );

  async function handleSuggestGolpes() {
    if (!codigoFerramenta || !codigoPeca) return;
    await refreshSuggestGolpes({
      codigoPecaValue: codigoPeca,
      dataReposicaoValue: dataReposicao,
      dataUltimaValue: dataUltimaReposicao,
    });
  }

  function handleEditReposicao(item: ReposicaoItem) {
    golpesRequestRef.current += 1;
    setGolpesLoading(false);
    editingReposicaoRef.current = item;
    setEditingReposicaoId(item.reposicao_id);
    setShowReposicaoForm(true);
    setCodigoPeca(item.codigo_peca);
    setGolpes(item.golpes);
    setMotivoId(item.motivo_id);
    setObservacao(item.observacao ?? "");
    setDataReposicao(toDatetimeLocalValue(item.data_reposicao));
    setDataUltimaReposicao(
      item.data_ultima_reposicao ? toDatetimeLocalValue(item.data_ultima_reposicao) : "",
    );
    setSuccess(null);
    setError(null);
    setReposicaoFormErrors({});
  }

  function clearReposicaoFieldError(field: keyof ReposicaoFormErrors) {
    setReposicaoFormErrors((current) => {
      if (!current[field]) return current;
      const next = { ...current };
      delete next[field];
      return next;
    });
  }

  async function handleDeleteReposicao(item: ReposicaoItem) {
    if (
      !window.confirm(
        `Excluir reposição de ${item.codigo_peca} em ${new Date(item.data_reposicao).toLocaleString("pt-BR")}?`,
      )
    ) {
      return;
    }
    setError(null);
    setSuccess(null);
    try {
      await deleteReposicao(item.reposicao_id, getAccessToken);
      setSuccess("Reposição excluída.");
      closeReposicaoForm();
      await loadDetalhe();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao excluir reposição.");
    }
  }

  async function handleSubmitReposicao(event: React.FormEvent) {
    event.preventDefault();
    const validationErrors = validateReposicaoForm({
      codigoPeca,
      dataReposicao,
      dataUltimaReposicao,
      golpes,
      motivoId,
    });
    if (hasReposicaoFormErrors(validationErrors)) {
      setReposicaoFormErrors(validationErrors);
      setError("Corrija os campos destacados antes de continuar.");
      setSuccess(null);
      return;
    }
    if (!codigoFerramenta) return;
    setReposicaoFormErrors({});
    setError(null);
    setSuccess(null);
    const payload = {
      filial,
      codigo_ferramenta: codigoFerramenta,
      codigo_peca: codigoPeca,
      data_reposicao: fromDatetimeLocalValue(dataReposicao),
      data_ultima_reposicao: editingReposicaoId
        ? editingReposicaoRef.current?.data_ultima_reposicao ?? undefined
        : dataUltimaReposicao
          ? fromDatetimeLocalValue(dataUltimaReposicao)
          : undefined,
      golpes,
      motivo_id: motivoId,
      observacao: observacao.trim() || undefined,
    };
    try {
      if (editingReposicaoId) {
        await updateReposicao(editingReposicaoId, payload, getAccessToken);
        setSuccess("Reposição atualizada.");
      } else {
        await createReposicao(payload, getAccessToken);
        setSuccess("Reposição registrada.");
      }
      closeReposicaoForm();
      await loadDetalhe();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Falha ao salvar reposição.";
      const apiErrors = mapReposicaoApiError(message);
      if (hasReposicaoFormErrors(apiErrors)) {
        setReposicaoFormErrors(apiErrors);
        setError("Corrija os campos destacados antes de continuar.");
      } else {
        setError(message);
      }
    }
  }

  const ferramentasColumns = useMemo<DataTableColumn<FerramentaItem>[]>(
    () => [
      {
        key: "codigo",
        header: "Código",
        sortable: true,
        sortValue: (item) => item.codigo,
        render: (item) => (
          <span className="dm-ferramenta-codigo">
            {item.bloqueado ? (
              <Lock size={14} className="dm-ferramenta-codigo__lock" aria-hidden="true" />
            ) : null}
            <span>{item.codigo}</span>
          </span>
        ),
      },
      {
        key: "descricao",
        header: "Descrição",
        sortable: true,
        sortValue: (item) => item.descricao,
        render: (item) => item.descricao,
      },
    ],
    [],
  );

  const reposicoesColumns = useMemo<DataTableColumn<ReposicaoItem>[]>(() => {
    const columns: DataTableColumn<ReposicaoItem>[] = [
      {
        key: "data",
        header: "Data",
        headerHint: DM_HELP.miniAplicadores.dataReposicao,
        sortable: true,
        sortValue: (item) => new Date(item.data_reposicao).getTime(),
        render: (item) => new Date(item.data_reposicao).toLocaleString("pt-BR"),
      },
      {
        key: "peca",
        header: "Peça",
        headerHint: DM_HELP.miniAplicadores.peca,
        sortable: true,
        sortValue: (item) => item.codigo_peca,
        render: (item) => (
          <CodigoDescricaoCell
            codigo={item.codigo_peca}
            descricao={pecaDescricaoMap[item.codigo_peca.trim()]}
          />
        ),
      },
      {
        key: "golpes",
        header: "Golpes",
        headerHint: DM_HELP.miniAplicadores.golpes,
        sortable: true,
        sortValue: (item) => item.golpes,
        render: (item) => item.golpes,
        align: "right",
      },
      {
        key: "motivo",
        header: "Motivo",
        headerHint: DM_HELP.miniAplicadores.motivo,
        sortable: true,
        sortValue: (item) => item.motivo_descricao ?? String(item.motivo_id),
        render: (item) => item.motivo_descricao ?? item.motivo_id,
      },
    ];

    if (canManageMiniApplicators) {
      columns.push({
        key: "acoes",
        header: "Ações",
        interactive: true,
        render: (item) => (
          <div className="dm-row-actions">
            <MaintenanceActionButton type="button" onClick={() => handleEditReposicao(item)} variant="ghost">
              Editar
            </MaintenanceActionButton>
            <MaintenanceActionButton
              type="button"
              onClick={() => void handleDeleteReposicao(item)}
             variant="ghost" className="dm-btn--danger">
              Excluir
            </MaintenanceActionButton>
          </div>
        ),
      });
    }

    return columns;
  }, [canManageMiniApplicators, pecaDescricaoMap]);


  return (
    <>
      <MaintenanceMiniAplicadoresHero
        title={
          <>
            <Hammer size={28} strokeWidth={1.75} aria-hidden />
            {codigoFerramenta ? `Ferramenta ${codigoFerramenta}` : "Ferramentas"}
          </>
        }
        description={
          codigoFerramenta
            ? "Histórico de reposições, revisão programada e cadastro de nova troca."
            : "Ferramentas dos grupos 23 e 24 via api-delpi."
        }
        filial={filial}
        filialDisplayName={filialDisplayName}
        actions={
          <div className="dm-hero-actions">
            <MaintenanceHeroFreshness updatedAt={lastUpdatedAt} />
            <MaintenanceActionButton
              variant="ghost"
              onClick={() => (codigoFerramenta ? void loadDetalhe() : void loadFerramentas())}
            disabled={codigoFerramenta ? detalheLoading : ferramentasLoading}
            aria-busy={codigoFerramenta ? detalheLoading : ferramentasLoading}
          >
            <RefreshCw
              size={16}
              className={
                codigoFerramenta
                  ? detalheLoading
                    ? "dm-spin"
                    : undefined
                  : ferramentasLoading
                    ? "dm-spin"
                    : undefined
              }
              aria-hidden
            />
            Atualizar
          </MaintenanceActionButton>
          </div>
        }
      />

      <section className="dm-page-stack">

      {!codigoFerramenta ? (
        <>
          <FerramentasPorPecaSearchCard
            filial={filial}
            selectedPecaCodigo={selectedPecaCodigo}
            onSelectPeca={handleSelectPeca}
            getAccessToken={getAccessToken}
          />

          <FilterBar onSubmit={handleSearch} className="dm-filter-bar--search">
            <DmNativeTextField
              id="dm-busca-ferramenta-codigo"
              label="Buscar por código"
              hint={DM_HELP.miniAplicadores.buscaFerramentaCodigo}
              value={codigo}
              onChange={setCodigo}
              placeholder="Ex.: 23 ou 23-026"
            />
            <DmNativeTextField
              id="dm-busca-ferramenta-descricao"
              label="Buscar por descrição"
              hint={DM_HELP.miniAplicadores.buscaFerramentaDescricao}
              value={descricao}
              onChange={setDescricao}
              placeholder="Ex.: 23-"
            />
            <div className="dm-filter-bar__actions">
              <NativeCheckboxControl
                className="dm-checkbox-field"
                checked={incluirBloqueados}
                onChange={(checked) => {
                  setIncluirBloqueados(checked);
                  ferramentasTable.resetPage();
                }}
                label="Mostrar bloqueadas"
              />
              <MaintenanceActionButton type="submit" variant="primary">
                Buscar
              </MaintenanceActionButton>
            </div>
          </FilterBar>

          {error ? (
            <StateBox variant="error" onDismiss={() => setError(null)}>
              {error}
            </StateBox>
          ) : null}

          <DataTableSection
            columnPreferencesKey="maintenance:MiniAplicadoresPage:miniaplicadorespage:v1"
            fontSizePreferencesKey="maintenance:mini-aplicadores:lista:table-font-size:v1"
            title={
              selectedPecaCodigo
                ? `Ferramentas com peça ${formatPecaLabel({
                    codigo: selectedPecaCodigo,
                    descricao: selectedPecaDescricao,
                  })}`
                : "Ferramentas"
            }
            titleHint={DM_HELP.miniAplicadores.listaTitle}
            columns={ferramentasColumns}
            rows={items}
            loading={ferramentasLoading}
            emptyMessage="Nenhuma ferramenta encontrada."
            getRowKey={(item) => item.codigo}
            getRowClassName={(item) => (item.bloqueado ? "is-blocked" : undefined)}
            onRowClick={(item) => onNavigate(MAINTENANCE_ROUTES.miniAplicadorDetail(item.codigo))}
            viewLayoutPreferencesKey={MAINTENANCE_LIST_LAYOUT_KEYS.ferramentas}
            renderCard={(item) => (
              <FerramentaListCard
                item={item}
                onActivate={() => onNavigate(MAINTENANCE_ROUTES.miniAplicadorDetail(item.codigo))}
              />
            )}
            serverTable={{
              page: ferramentasTable.query.page,
              pageSize: ferramentasTable.query.pageSize,
              total,
              onPageChange: ferramentasTable.setPage,
              sortKey: ferramentasTable.query.sortKey,
              sortDirection: ferramentasTable.query.sortDirection,
              onSortChange: ferramentasTable.handleSortChange,
            }}
          />
        </>
      ) : (
        <>
          {error ? (
            <StateBox variant="error" onDismiss={() => setError(null)}>
              {error}
            </StateBox>
          ) : null}
          {success ? (
            <StateBox variant="success" onDismiss={() => setSuccess(null)}>
              {success}
            </StateBox>
          ) : null}

          {canManageMiniApplicators && showReposicaoForm ? (
            <section ref={reposicaoFormRef} className="dm-card dm-reposicao-form-card">
              <div className="dm-section-header">
                <h3 className="dm-section-header__title">
                  {editingReposicaoId ? "Editar reposição" : "Nova reposição"}
                </h3>
                {!editingReposicaoId ? (
                  <MaintenanceActionButton type="button" onClick={() => closeReposicaoForm()} variant="ghost">
                    Fechar
                  </MaintenanceActionButton>
                ) : null}
              </div>
              <form
                className="dm-form-grid dm-form-grid--reposicao"
                lang="pt-BR"
                onSubmit={handleSubmitReposicao}
              >
                <DmNativeSelectField
                  id="dm-reposicao-peca"
                  label="Peça"
                  hint={DM_HELP.miniAplicadores.peca}
                  className={`dm-field--span-full${reposicaoFormErrors.codigoPeca ? " dm-field--invalid" : ""}`}
                  controlClassName="dm-select-peca"
                  value={codigoPeca}
                  onChange={(value) => {
                    clearReposicaoFieldError("codigoPeca");
                    setCodigoPeca(value);
                    if (!editingReposicaoId) {
                      setDataUltimaReposicao("");
                    }
                  }}
                  placeholderOption={
                    pecasReposicao.length === 0
                      ? "Nenhuma peça 3019 amarrada ao mini-aplicador"
                      : undefined
                  }
                  options={pecasReposicao.map((peca) => ({
                    value: peca.codigo,
                    label: formatPecaLabel(peca),
                  }))}
                  afterControl={
                    reposicaoFormErrors.codigoPeca ? (
                      <span className="dm-field__error">{reposicaoFormErrors.codigoPeca}</span>
                    ) : null
                  }
                />

                <label
                  className={`dm-field dm-field--span-4${reposicaoFormErrors.dataReposicao ? " dm-field--invalid" : ""}`}
                >
                  <MaintenanceFieldLabel
                    label="Data da reposição"
                    hint={DM_HELP.miniAplicadores.dataReposicao}
                    className="dm-field__label"
                  />
                  <BrDatetimeInput
                    value={dataReposicao}
                    error={reposicaoFormErrors.dataReposicao}
                    onChange={(value) => {
                      clearReposicaoFieldError("dataReposicao");
                      setDataReposicao(value);
                    }}
                  />
                </label>
                <label
                  className={`dm-field dm-field--span-4${reposicaoFormErrors.dataUltimaReposicao ? " dm-field--invalid" : ""}`}
                >
                  <MaintenanceFieldLabel
                    label="Data da última reposição"
                    hint={DM_HELP.miniAplicadores.dataUltima}
                    className="dm-field__label"
                  />
                  <BrDatetimeInput
                    value={dataUltimaReposicao}
                    error={reposicaoFormErrors.dataUltimaReposicao}
                    onChange={(value) => {
                      clearReposicaoFieldError("dataUltimaReposicao");
                      setDataUltimaReposicao(value);
                    }}
                    readOnly={Boolean(editingReposicaoId)}
                    disabled={Boolean(editingReposicaoId)}
                  />
                </label>
                <div
                  className={`dm-field dm-field--span-2 dm-golpes-field${golpesLoading ? " is-loading" : ""}${reposicaoFormErrors.golpes ? " dm-field--invalid" : ""}`}
                  aria-busy={golpesLoading}
                >
                  <MaintenanceFieldLabel
                    label={golpesLoading ? "Calculando golpes…" : "Golpes"}
                    hint={DM_HELP.miniAplicadores.golpes}
                    className="dm-field__label"
                  />
                  <div className="dm-golpes-field__control">
                    <NativeTextControl
                      type="number"
                      min={1}
                      value={golpes}
                      disabled={golpesLoading}
                      readOnly={golpesLoading}
                      aria-invalid={Boolean(reposicaoFormErrors.golpes)}
                      onChange={(value) => {
                        clearReposicaoFieldError("golpes");
                        setGolpes(Number(value));
                      }}
                      aria-live="polite"
                    />
                    {golpesLoading ? (
                      <Loader2
                        size={18}
                        className="dm-golpes-field__spinner dm-spin"
                        aria-hidden="true"
                      />
                    ) : null}
                  </div>
                  {reposicaoFormErrors.golpes ? (
                    <span className="dm-field__error">{reposicaoFormErrors.golpes}</span>
                  ) : null}
                </div>

                <MaintenanceActionButton
                  type="button"
                  disabled={golpesLoading || !codigoPeca}
                  title={DM_HELP.miniAplicadores.sugerirGolpes}
                  onClick={() => void handleSuggestGolpes()}
                  variant="ghost"
                  className="dm-form-grid__suggest dm-field--span-2"
                >
                  {golpesLoading ? (
                    <Loader2 size={16} className="dm-spin" aria-hidden="true" />
                  ) : null}
                  {golpesLoading ? "Calculando…" : "Sugerir golpes"}
                </MaintenanceActionButton>

                <DmNativeSelectField
                  id="dm-reposicao-motivo"
                  label="Motivo"
                  hint={DM_HELP.miniAplicadores.motivo}
                  className={`dm-field--span-full${reposicaoFormErrors.motivoId ? " dm-field--invalid" : ""}`}
                  value={motivoId}
                  onChange={(value) => {
                    clearReposicaoFieldError("motivoId");
                    setMotivoId(value);
                  }}
                  placeholderOption="Selecione…"
                  options={motivos.map((motivo) => ({
                    value: String(motivo.motivo_id),
                    label: motivo.descricao,
                  }))}
                  afterControl={
                    reposicaoFormErrors.motivoId ? (
                      <span className="dm-field__error">{reposicaoFormErrors.motivoId}</span>
                    ) : null
                  }
                />

                <DmNativeTextAreaField
                  id="dm-reposicao-observacao"
                  label="Observação"
                  hint={DM_HELP.miniAplicadores.observacao}
                  className="dm-field--span-full dm-field--textarea"
                  span={false}
                  rows={4}
                  value={observacao}
                  onChange={setObservacao}
                  placeholder="Detalhes da troca, condição da peça, etc."
                />

                <div className="dm-form-grid__buttons dm-field--span-full">
                  <MaintenanceActionButton type="submit" disabled={!codigoPeca} variant="primary">
                    {editingReposicaoId ? "Salvar alterações" : "Registrar reposição"}
                  </MaintenanceActionButton>
                  {editingReposicaoId ? (
                    <MaintenanceActionButton type="button" onClick={() => closeReposicaoForm()} variant="ghost">
                      Cancelar edição
                    </MaintenanceActionButton>
                  ) : null}
                </div>
              </form>
            </section>
          ) : null}

          {allReposicoesChart.length > 0 || chartLoading ? (
            <section className="dm-ferramenta-analytics">
              <ReposicoesGolpesChart
                reposicoes={chartReposicoes}
                pecaLabels={pecaDescricaoMap}
                loading={chartLoading}
              />
              <FerramentaReposicaoIndicadores
                reposicoes={chartReposicoes}
                pecaLabels={pecaDescricaoMap}
                loading={chartLoading}
                filtrosAtivos={historicoFiltrosAtivos}
              />
            </section>
          ) : null}

          <FerramentaRevisaoProgramadaSection
            filial={filial}
            codigoFerramenta={codigoFerramenta}
            canManage={canManageMiniApplicators}
            reloadKey={detalheVersion}
            getAccessToken={getAccessToken}
            onFeedback={handleRevisaoFeedback}
          />

          <div ref={historicoSectionRef} className="dm-historico-anchor">
            <DataTableSection
              columnPreferencesKey="maintenance:MiniAplicadoresPage:hist-rico-de-reposi-es-1:v1"
              title="Histórico de reposições"
              titleHint={DM_HELP.miniAplicadores.historico}
            actions={
              <div className="dm-row-actions">
                {canManageMiniApplicators && !showReposicaoForm && !editingReposicaoId ? (
                  <MaintenanceActionButton type="button" onClick={openNovaReposicao} variant="primary">
                    <PlusCircle size={16} />
                    Nova reposição
                  </MaintenanceActionButton>
                ) : null}
                <MaintenanceActionButton
                  type="button"
                  onClick={() => onNavigate(MAINTENANCE_ROUTES.miniAplicadores)}
                 variant="ghost">
                  Voltar para lista
                </MaintenanceActionButton>
              </div>
            }
            toolbar={
              <FilterBar embedded>
                <MultiSelectField
                  label="Filtrar por peça"
                  className="dm-field--filter-peca"
                  emptyLabel="Todas"
                  searchable
                  options={pecaHistoricoOptions}
                  selectedValues={filtroHistoricoPecaDraft}
                  onChange={setFiltroHistoricoPecaDraft}
                />
                <MultiSelectField
                  label="Filtrar por motivo"
                  className="dm-field--filter-motivo"
                  emptyLabel="Todos"
                  options={motivoHistoricoOptions}
                  selectedValues={filtroHistoricoMotivoDraft}
                  onChange={setFiltroHistoricoMotivoDraft}
                />
                <label className="dm-field dm-field--filter-date">
                  <MaintenanceFieldLabel label="De" hint={DM_HELP.miniAplicadores.dataReposicao} />
                  <BrDateInput
                    value={filtroHistoricoDataInicialDraft}
                    onChange={setFiltroHistoricoDataInicialDraft}
                  />
                </label>
                <label className="dm-field dm-field--filter-date">
                  <MaintenanceFieldLabel label="Até" hint={DM_HELP.miniAplicadores.dataReposicao} />
                  <BrDateInput
                    value={filtroHistoricoDataFinalDraft}
                    onChange={setFiltroHistoricoDataFinalDraft}
                  />
                </label>
                <div className="dm-filter-bar__actions">
                  <MaintenanceActionButton type="button" onClick={applyHistoricoFilters} variant="ghost">
                    Aplicar filtro
                  </MaintenanceActionButton>
                </div>
              </FilterBar>
            }
            columns={reposicoesColumns}
            rows={reposicoes}
            loading={reposicoesLoading}
            emptyMessage="Nenhuma reposição registrada."
            getRowKey={(item) => item.reposicao_id}
            getRowClassName={(item) => (editingReposicaoId === item.reposicao_id ? "is-selected" : undefined)}
            viewLayoutPreferencesKey={MAINTENANCE_LIST_LAYOUT_KEYS.reposicoes}
            renderCard={(item) => (
              <ReposicaoListCard
                item={item}
                pecaDescricao={pecaDescricaoMap[item.codigo_peca.trim()]}
                onActivate={
                  canManageMiniApplicators ? () => handleEditReposicao(item) : undefined
                }
              />
            )}
            serverTable={{
              page: reposicoesTable.query.page,
              pageSize: reposicoesTable.query.pageSize,
              total: reposicoesTotal,
              onPageChange: reposicoesTable.setPage,
              sortKey: reposicoesTable.query.sortKey,
              sortDirection: reposicoesTable.query.sortDirection,
              onSortChange: reposicoesTable.handleSortChange,
            }}
            onRowClick={
              canManageMiniApplicators ? (item) => handleEditReposicao(item) : undefined
            }
          />
          </div>

          <ComponentesEstoqueSection
            filial={filial}
            codigoFerramenta={codigoFerramenta}
            getAccessToken={getAccessToken}
            estruturaItems={estruturaComponentes}
          />

          <FerramentaOndeUsadoSection
            filial={filial}
            codigoFerramenta={codigoFerramenta}
            getAccessToken={getAccessToken}
          />

          <FerramentaAuditoriaSection
            filial={filial}
            codigoFerramenta={codigoFerramenta}
            reloadKey={detalheVersion}
            getAccessToken={getAccessToken}
          />
        </>
      )}
      </section>
    </>
  );
}
