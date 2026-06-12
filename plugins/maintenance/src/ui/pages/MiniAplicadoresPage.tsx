import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Hammer, Loader2, PlusCircle, RefreshCw } from "lucide-react";

import { type DataTableColumn, DataTableSection, FilterBar, StateBox } from "../../components/data";
import { MAINTENANCE_ROUTES } from "../../constants/routes";
import {
  useMaintenanceActiveFilial,
  useMaintenanceModuleHomePath,
  useOperationalFilial,
} from "../../hooks/useMaintenanceScope";
import { useServerTable } from "../../hooks/useServerTable";
import { ReposicoesGolpesChart } from "../../components/ReposicoesGolpesChart";
import {
  createReposicao,
  deleteReposicao,
  fetchComponentes,
  fetchFerramentas,
  fetchMotivos,
  fetchPecas,
  fetchReposicoes,
  suggestGolpes,
  updateReposicao,
  type ComponenteItem,
  type FerramentaItem,
  type MotivoItem,
  type ReposicaoItem,
} from "../../data/api/maintenanceApi";
import { MaintenanceShell } from "../../components/MaintenanceShell";
import { MiniAplicadoresPageHeader } from "../../components/MiniAplicadoresPageHeader";
import {
  fromDatetimeLocalValue,
  toDatetimeLocalValue,
} from "../../utils/datetimeLocal";
import { resolveFilialDisplayName } from "../../utils/maintenanceFilialSelection";
import { formatPecaLabel, type PecaOption } from "../../utils/pecaOptions";

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
  const moduleHomePath = useMaintenanceModuleHomePath(getAccessToken, filialScope ?? filial);
  const { canManageMiniApplicators, filiais } = useMaintenanceActiveFilial(getAccessToken, filialScope);
  const filialDisplayName = resolveFilialDisplayName(filiais, filial);
  const [descricao, setDescricao] = useState("");
  const [codigo, setCodigo] = useState("");
  const [items, setItems] = useState<FerramentaItem[]>([]);
  const [total, setTotal] = useState(0);
  const ferramentasTable = useServerTable({ defaultSortKey: "codigo" });
  const reposicoesTable = useServerTable({ defaultSortKey: "data", defaultSortDirection: "desc" });
  const componentesTable = useServerTable({ defaultSortKey: "nivel" });
  const [pecasOptions, setPecasOptions] = useState<PecaOption[]>([]);
  const [chartReposicoes, setChartReposicoes] = useState<ReposicaoItem[]>([]);
  const [chartLoading, setChartLoading] = useState(false);
  const [showReposicaoForm, setShowReposicaoForm] = useState(false);
  const [componentes, setComponentes] = useState<ComponenteItem[]>([]);
  const [componentesTotal, setComponentesTotal] = useState(0);
  const [motivos, setMotivos] = useState<MotivoItem[]>([]);
  const [reposicoes, setReposicoes] = useState<ReposicaoItem[]>([]);
  const [reposicoesTotal, setReposicoesTotal] = useState(0);
  const [codigoPeca, setCodigoPeca] = useState("");
  const [golpes, setGolpes] = useState(0);
  const [motivoId, setMotivoId] = useState<number | "">("");
  const [observacao, setObservacao] = useState("");
  const [dataReposicao, setDataReposicao] = useState(() => toDatetimeLocalValue(new Date()));
  const [dataUltimaReposicao, setDataUltimaReposicao] = useState("");
  const [editingReposicaoId, setEditingReposicaoId] = useState<string | null>(null);
  const [filtroHistoricoPeca, setFiltroHistoricoPeca] = useState("");
  const [ferramentasLoading, setFerramentasLoading] = useState(false);
  const [detalheLoading, setDetalheLoading] = useState(false);
  const [reposicoesLoading, setReposicoesLoading] = useState(false);
  const [componentesLoading, setComponentesLoading] = useState(false);
  const [golpesLoading, setGolpesLoading] = useState(false);
  const golpesRequestRef = useRef(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const pecasEstrutura = useMemo(() => {
    const options = [...pecasOptions];
    if (codigoPeca && !options.some((item) => item.codigo === codigoPeca)) {
      options.push({ codigo: codigoPeca, descricao: codigoPeca });
      options.sort((first, second) => first.codigo.localeCompare(second.codigo, "pt-BR"));
    }
    return options;
  }, [pecasOptions, codigoPeca]);

  const resetReposicaoForm = useCallback(() => {
    setEditingReposicaoId(null);
    setCodigoPeca(pecasEstrutura[0]?.codigo ?? "");
    setGolpes(0);
    setMotivoId("");
    setObservacao("");
    setDataReposicao(toDatetimeLocalValue(new Date()));
    setDataUltimaReposicao("");
  }, [pecasEstrutura]);

  const openNovaReposicao = useCallback(() => {
    setEditingReposicaoId(null);
    setCodigoPeca(pecasEstrutura[0]?.codigo ?? "");
    setGolpes(0);
    setMotivoId("");
    setObservacao("");
    setDataReposicao(toDatetimeLocalValue(new Date()));
    setDataUltimaReposicao("");
    setSuccess(null);
    setError(null);
    setShowReposicaoForm(true);
  }, [pecasEstrutura]);

  const closeReposicaoForm = useCallback(() => {
    resetReposicaoForm();
    setShowReposicaoForm(false);
  }, [resetReposicaoForm]);

  useEffect(() => {
    if (editingReposicaoId) {
      setShowReposicaoForm(true);
    }
  }, [editingReposicaoId]);

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
        if (data.data_ultima_reposicao && !options.dataUltimaValue) {
          setDataUltimaReposicao(toDatetimeLocalValue(data.data_ultima_reposicao));
        }
        if (!editingReposicaoId) {
          setGolpes(data.total_golpes ?? 0);
        }
      } catch {
        if (requestId !== golpesRequestRef.current) return;
        if (!editingReposicaoId) setGolpes(0);
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
          codigo: codigo.trim() || undefined,
          descricao: descricao.trim() || undefined,
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
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar ferramentas.");
      setItems([]);
      setTotal(0);
    } finally {
      setFerramentasLoading(false);
    }
  }, [codigo, descricao, filial, ferramentasTable.query, getAccessToken]);

  const loadChartReposicoes = useCallback(
    async (total: number) => {
      if (!codigoFerramenta || total <= 0) {
        setChartReposicoes([]);
        return;
      }
      setChartLoading(true);
      try {
        const data = await fetchReposicoes(
          {
            filial,
            codigo_ferramenta: codigoFerramenta,
            codigo_peca: filtroHistoricoPeca || undefined,
            page: 1,
            pageSize: Math.min(total, 100),
            sortKey: "data",
            sortDirection: "asc",
          },
          getAccessToken,
        );
        setChartReposicoes(data.items ?? []);
      } catch {
        setChartReposicoes([]);
      } finally {
        setChartLoading(false);
      }
    },
    [codigoFerramenta, filial, filtroHistoricoPeca, getAccessToken],
  );

  const loadReposicoes = useCallback(async () => {
    if (!codigoFerramenta) return;
    setReposicoesLoading(true);
    setError(null);
    try {
      const data = await fetchReposicoes(
        {
          filial,
          codigo_ferramenta: codigoFerramenta,
          codigo_peca: filtroHistoricoPeca || undefined,
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
      await loadChartReposicoes(total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar reposições.");
      setReposicoes([]);
      setReposicoesTotal(0);
      setChartReposicoes([]);
    } finally {
      setReposicoesLoading(false);
    }
  }, [
    codigoFerramenta,
    filial,
    filtroHistoricoPeca,
    getAccessToken,
    loadChartReposicoes,
    reposicoesTable.query,
  ]);

  const loadComponentesTable = useCallback(async () => {
    if (!codigoFerramenta) return;
    setComponentesLoading(true);
    try {
      const data = await fetchComponentes(
        codigoFerramenta,
        filial,
        {
          page: componentesTable.query.page,
          pageSize: componentesTable.query.pageSize,
          sortKey: componentesTable.query.sortKey,
          sortDirection: componentesTable.query.sortDirection,
        },
        getAccessToken,
      );
      setComponentes(data.items ?? []);
      setComponentesTotal(data.total ?? 0);
    } catch {
      setComponentes([]);
      setComponentesTotal(0);
    } finally {
      setComponentesLoading(false);
    }
  }, [codigoFerramenta, componentesTable.query, filial, getAccessToken]);

  const loadDetalheBase = useCallback(async () => {
    if (!codigoFerramenta) return;
    setDetalheLoading(true);
    setError(null);
    try {
      const [motivosData, pecasData] = await Promise.all([
        fetchMotivos(filial, { page: 1, pageSize: 200 }, {}, getAccessToken),
        fetchPecas(codigoFerramenta, filial, getAccessToken),
      ]);
      const pecaItems = (pecasData.items ?? []).map((item) => ({
        codigo: item.codigo,
        descricao: item.descricao,
      }));
      setMotivos(motivosData.items ?? []);
      setPecasOptions(pecaItems);
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
    await Promise.all([loadDetalheBase(), loadReposicoes(), loadComponentesTable()]);
  }, [loadComponentesTable, loadDetalheBase, loadReposicoes]);

  useEffect(() => {
    if (!codigoFerramenta) return;
    setFiltroHistoricoPeca("");
    setEditingReposicaoId(null);
    setShowReposicaoForm(false);
    reposicoesTable.resetPage();
    componentesTable.resetPage();
    void loadDetalheBase();
  }, [
    codigoFerramenta,
    filial,
    loadDetalheBase,
    reposicoesTable.resetPage,
    componentesTable.resetPage,
  ]);

  useEffect(() => {
    if (!codigoFerramenta) return;
    void loadReposicoes();
  }, [codigoFerramenta, loadReposicoes]);

  useEffect(() => {
    if (!codigoFerramenta) return;
    void loadComponentesTable();
  }, [codigoFerramenta, loadComponentesTable]);

  useEffect(() => {
    if (codigoFerramenta) return;
    void loadFerramentas();
  }, [codigoFerramenta, loadFerramentas]);

  useEffect(() => {
    if (codigoFerramenta) return;
    ferramentasTable.resetPage();
  }, [filial, codigoFerramenta, ferramentasTable.resetPage]);

  useEffect(() => {
    if (!codigoFerramenta || !codigoPeca || editingReposicaoId) return;
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
  ]);

  useEffect(() => {
    if (!filtroHistoricoPeca) return;
    if (!pecasEstrutura.some((item) => item.codigo === filtroHistoricoPeca)) {
      setFiltroHistoricoPeca("");
    }
  }, [filtroHistoricoPeca, pecasEstrutura]);

  async function handleSearch(event: React.FormEvent) {
    event.preventDefault();
    ferramentasTable.resetPage();
    await loadFerramentas();
  }

  async function handleSuggestGolpes() {
    if (!codigoFerramenta || !codigoPeca) return;
    await refreshSuggestGolpes({
      codigoPecaValue: codigoPeca,
      dataReposicaoValue: dataReposicao,
      dataUltimaValue: dataUltimaReposicao,
    });
  }

  function handleEditReposicao(item: ReposicaoItem) {
    setEditingReposicaoId(item.reposicao_id);
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
      resetReposicaoForm();
      setShowReposicaoForm(false);
      await loadDetalhe();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao excluir reposição.");
    }
  }

  async function handleSubmitReposicao(event: React.FormEvent) {
    event.preventDefault();
    if (!codigoFerramenta || !codigoPeca || motivoId === "") return;
    if (golpes <= 0) {
      setError("Informe golpes maior que zero ou use «Sugerir golpes».");
      return;
    }
    setError(null);
    setSuccess(null);
    const payload = {
      filial,
      codigo_ferramenta: codigoFerramenta,
      codigo_peca: codigoPeca,
      data_reposicao: fromDatetimeLocalValue(dataReposicao),
      data_ultima_reposicao: dataUltimaReposicao
        ? fromDatetimeLocalValue(dataUltimaReposicao)
        : undefined,
      golpes,
      motivo_id: Number(motivoId),
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
      resetReposicaoForm();
      setShowReposicaoForm(false);
      await loadDetalhe();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar reposição.");
    }
  }

  const ferramentasColumns = useMemo<DataTableColumn<FerramentaItem>[]>(
    () => [
      {
        key: "codigo",
        header: "Código",
        sortable: true,
        sortValue: (item) => item.codigo,
        render: (item) => item.codigo,
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
        sortable: true,
        sortValue: (item) => new Date(item.data_reposicao).getTime(),
        render: (item) => new Date(item.data_reposicao).toLocaleString("pt-BR"),
      },
      {
        key: "peca",
        header: "Peça",
        sortable: true,
        sortValue: (item) => item.codigo_peca,
        render: (item) => item.codigo_peca,
      },
      {
        key: "golpes",
        header: "Golpes",
        sortable: true,
        sortValue: (item) => item.golpes,
        render: (item) => item.golpes,
        align: "right",
      },
      {
        key: "motivo",
        header: "Motivo",
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
            <button type="button" className="dm-ghost-btn" onClick={() => handleEditReposicao(item)}>
              Editar
            </button>
            <button
              type="button"
              className="dm-ghost-btn dm-ghost-btn--danger"
              onClick={() => void handleDeleteReposicao(item)}
            >
              Excluir
            </button>
          </div>
        ),
      });
    }

    return columns;
  }, [canManageMiniApplicators]);

  const componentesColumns = useMemo<DataTableColumn<ComponenteItem>[]>(
    () => [
      {
        key: "nivel",
        header: "Nível",
        sortable: true,
        sortValue: (item) => item.nivel,
        render: (item) => item.nivel,
        align: "center",
      },
      {
        key: "codigo",
        header: "Código",
        sortable: true,
        sortValue: (item) => item.codigo,
        render: (item) => (
          <span className="dm-datatable__cell-indent" style={{ paddingLeft: `${item.nivel * 12}px` }}>
            {item.codigo}
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
      {
        key: "unidade",
        header: "Un.",
        sortable: true,
        sortValue: (item) => item.unidade,
        render: (item) => item.unidade,
        align: "center",
      },
      {
        key: "estoque01",
        header: "Estoque 01",
        sortable: true,
        sortValue: (item) => item.estoque_local_01,
        render: (item) => item.estoque_local_01.toLocaleString("pt-BR"),
        align: "right",
      },
      {
        key: "estoque99",
        header: "Estoque 99",
        sortable: true,
        sortValue: (item) => item.estoque_local_99,
        render: (item) => item.estoque_local_99.toLocaleString("pt-BR"),
        align: "right",
      },
    ],
    [],
  );

  return (
    <MaintenanceShell>
      <MiniAplicadoresPageHeader
        title={codigoFerramenta ? `Ferramenta ${codigoFerramenta}` : "Ferramentas"}
        subtitle={
          codigoFerramenta
            ? "Histórico de reposições e cadastro de nova troca."
            : "Ferramentas dos grupos 23 e 24 via api-delpi."
        }
        icon={Hammer}
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
            onClick={() => (codigoFerramenta ? void loadDetalhe() : void loadFerramentas())}
            disabled={codigoFerramenta ? detalheLoading : ferramentasLoading}
          >
            <RefreshCw
              size={16}
              className={codigoFerramenta ? (detalheLoading ? "dm-spin" : undefined) : ferramentasLoading ? "dm-spin" : undefined}
            />
            {codigoFerramenta
              ? detalheLoading
                ? "Carregando…"
                : "Atualizar"
              : ferramentasLoading
                ? "Carregando…"
                : "Atualizar"}
          </button>
        }
      />

      {!codigoFerramenta ? (
        <>
          <FilterBar onSubmit={handleSearch}>
            <label className="dm-field">
              <span>Buscar por código</span>
              <input
                value={codigo}
                onChange={(event) => setCodigo(event.target.value)}
                placeholder="Ex.: 23-026"
              />
            </label>
            <label className="dm-field">
              <span>Buscar por descrição</span>
              <input
                value={descricao}
                onChange={(event) => setDescricao(event.target.value)}
                placeholder="Ex.: 23-"
              />
            </label>
            <button type="submit" className="dm-primary-btn">
              Buscar
            </button>
          </FilterBar>

          {error ? <StateBox variant="error">{error}</StateBox> : null}

          <DataTableSection
            title="Ferramentas"
            badge={`${total} registro(s)`}
            columns={ferramentasColumns}
            rows={items}
            loading={ferramentasLoading}
            emptyMessage="Nenhuma ferramenta encontrada."
            getRowKey={(item) => item.codigo}
            onRowClick={(item) => onNavigate(MAINTENANCE_ROUTES.miniAplicadorDetail(item.codigo))}
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
          {error ? <StateBox variant="error">{error}</StateBox> : null}
          {success ? <StateBox variant="success">{success}</StateBox> : null}

          {canManageMiniApplicators && showReposicaoForm ? (
            <section className="dm-card dm-reposicao-form-card">
              <div className="dm-section-header">
                <h3 className="dm-section-header__title">
                  {editingReposicaoId ? "Editar reposição" : "Nova reposição"}
                </h3>
                {!editingReposicaoId ? (
                  <button type="button" className="dm-ghost-btn" onClick={closeReposicaoForm}>
                    Fechar
                  </button>
                ) : null}
              </div>
              <form className="dm-form-grid dm-form-grid--reposicao" onSubmit={handleSubmitReposicao}>
                <label className="dm-field dm-field--span-full">
                  <span>Peça</span>
                  <select
                    className="dm-select-peca"
                    value={codigoPeca}
                    onChange={(event) => {
                      setCodigoPeca(event.target.value);
                      setDataUltimaReposicao("");
                    }}
                  >
                    {pecasEstrutura.length === 0 ? (
                      <option value="">Nenhuma peça (3019) na estrutura</option>
                    ) : null}
                    {pecasEstrutura.map((peca) => (
                      <option key={peca.codigo} value={peca.codigo}>
                        {formatPecaLabel(peca)}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="dm-field dm-field--span-4">
                  <span>Data da reposição</span>
                  <input
                    type="datetime-local"
                    value={dataReposicao}
                    onChange={(event) => setDataReposicao(event.target.value)}
                  />
                </label>
                <label className="dm-field dm-field--span-4">
                  <span>Data da última reposição</span>
                  <input
                    type="datetime-local"
                    value={dataUltimaReposicao}
                    onChange={(event) => setDataUltimaReposicao(event.target.value)}
                  />
                </label>
                <div
                  className={`dm-field dm-field--span-2 dm-golpes-field${golpesLoading ? " is-loading" : ""}`}
                  aria-busy={golpesLoading}
                >
                  <span>{golpesLoading ? "Calculando golpes…" : "Golpes"}</span>
                  <div className="dm-golpes-field__control">
                    <input
                      type="number"
                      min={1}
                      value={golpes}
                      disabled={golpesLoading}
                      readOnly={golpesLoading}
                      onChange={(event) => setGolpes(Number(event.target.value))}
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
                </div>

                <button
                  type="button"
                  className="dm-ghost-btn dm-form-grid__suggest dm-field--span-2"
                  disabled={golpesLoading || !codigoPeca}
                  onClick={() => void handleSuggestGolpes()}
                >
                  {golpesLoading ? (
                    <Loader2 size={16} className="dm-spin" aria-hidden="true" />
                  ) : null}
                  {golpesLoading ? "Calculando…" : "Sugerir golpes"}
                </button>

                <label className="dm-field dm-field--span-full">
                  <span>Motivo</span>
                  <select
                    value={motivoId}
                    onChange={(event) =>
                      setMotivoId(event.target.value ? Number(event.target.value) : "")
                    }
                  >
                    <option value="">Selecione…</option>
                    {motivos.map((motivo) => (
                      <option key={motivo.motivo_id} value={motivo.motivo_id}>
                        {motivo.descricao}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="dm-field dm-field--span-full dm-field--textarea">
                  <span>Observação</span>
                  <textarea
                    rows={4}
                    value={observacao}
                    placeholder="Detalhes da troca, condição da peça, etc."
                    onChange={(event) => setObservacao(event.target.value)}
                  />
                </label>

                <div className="dm-form-grid__buttons dm-field--span-full">
                  <button type="submit" className="dm-primary-btn" disabled={!codigoPeca}>
                    {editingReposicaoId ? "Salvar alterações" : "Registrar reposição"}
                  </button>
                  {editingReposicaoId ? (
                    <button type="button" className="dm-ghost-btn" onClick={closeReposicaoForm}>
                      Cancelar edição
                    </button>
                  ) : null}
                </div>
              </form>
            </section>
          ) : null}

          {reposicoesTotal > 0 ? (
            <ReposicoesGolpesChart reposicoes={chartReposicoes} loading={chartLoading} />
          ) : null}

          <DataTableSection
            title="Histórico de reposições"
            actions={
              <div className="dm-row-actions">
                {canManageMiniApplicators && !showReposicaoForm && !editingReposicaoId ? (
                  <button type="button" className="dm-primary-btn" onClick={openNovaReposicao}>
                    <PlusCircle size={16} />
                    Nova reposição
                  </button>
                ) : null}
                <button
                  type="button"
                  className="dm-ghost-btn"
                  onClick={() => onNavigate(MAINTENANCE_ROUTES.miniAplicadores)}
                >
                  Voltar para lista
                </button>
              </div>
            }
            toolbar={
              <FilterBar embedded>
                <label className="dm-field dm-field--filter-peca">
                  <span>Filtrar por peça</span>
                  <select
                    className="dm-select-peca"
                    value={filtroHistoricoPeca}
                    onChange={(event) => setFiltroHistoricoPeca(event.target.value)}
                  >
                    <option value="">Todas</option>
                    {pecasEstrutura.map((peca) => (
                      <option key={peca.codigo} value={peca.codigo}>
                        {formatPecaLabel(peca)}
                      </option>
                    ))}
                  </select>
                </label>
                <button
                  type="button"
                  className="dm-ghost-btn"
                  onClick={() => {
                    reposicoesTable.resetPage();
                    void loadReposicoes();
                  }}
                >
                  Aplicar filtro
                </button>
              </FilterBar>
            }
            columns={reposicoesColumns}
            rows={reposicoes}
            loading={reposicoesLoading}
            emptyMessage="Nenhuma reposição registrada."
            getRowKey={(item) => item.reposicao_id}
            getRowClassName={(item) => (editingReposicaoId === item.reposicao_id ? "is-selected" : undefined)}
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

          <DataTableSection
            title="Componentes e estoque"
            badge={`${componentesTotal} item(ns)`}
            columns={componentesColumns}
            rows={componentes}
            loading={componentesLoading}
            emptyMessage="Nenhum componente na estrutura desta ferramenta."
            getRowKey={(item, index) => `${item.codigo}-${item.nivel}-${index}`}
            serverTable={{
              page: componentesTable.query.page,
              pageSize: componentesTable.query.pageSize,
              total: componentesTotal,
              onPageChange: componentesTable.setPage,
              sortKey: componentesTable.query.sortKey,
              sortDirection: componentesTable.query.sortDirection,
              onSortChange: componentesTable.handleSortChange,
            }}
          />
        </>
      )}
    </MaintenanceShell>
  );
}
