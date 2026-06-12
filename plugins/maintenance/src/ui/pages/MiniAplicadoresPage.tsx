import { useCallback, useEffect, useMemo, useState } from "react";
import { Hammer, RefreshCw } from "lucide-react";

import {
  type DataTableColumn,
  DataTableSection,
  FilialBadge,
  FilterBar,
  StateBox,
} from "../../components/data";
import { MAINTENANCE_ROUTES } from "../../constants/routes";
import {
  useMaintenanceActiveFilial,
  useMaintenanceModuleHomePath,
  useOperationalFilial,
} from "../../hooks/useMaintenanceScope";
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

type MiniAplicadoresPageProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  filialScope?: string;
  onNavigate: (path: string) => void;
  codigoFerramenta?: string;
};

export function MiniAplicadoresPage({
  getAccessToken,
  pathname,
  filialScope,
  onNavigate,
  codigoFerramenta,
}: MiniAplicadoresPageProps) {
  const filial = useOperationalFilial(getAccessToken, filialScope) ?? "01";
  const moduleHomePath = useMaintenanceModuleHomePath(getAccessToken, filialScope ?? filial);
  const { canManageMiniApplicators } = useMaintenanceActiveFilial(getAccessToken, filialScope);
  const [descricao, setDescricao] = useState("");
  const [codigo, setCodigo] = useState("");
  const [items, setItems] = useState<FerramentaItem[]>([]);
  const [total, setTotal] = useState(0);
  const [pecas, setPecas] = useState<FerramentaItem[]>([]);
  const [componentes, setComponentes] = useState<ComponenteItem[]>([]);
  const [motivos, setMotivos] = useState<MotivoItem[]>([]);
  const [reposicoes, setReposicoes] = useState<ReposicaoItem[]>([]);
  const [codigoPeca, setCodigoPeca] = useState("");
  const [golpes, setGolpes] = useState(0);
  const [motivoId, setMotivoId] = useState<number | "">("");
  const [observacao, setObservacao] = useState("");
  const [dataReposicao, setDataReposicao] = useState(() => new Date().toISOString());
  const [editingReposicaoId, setEditingReposicaoId] = useState<string | null>(null);
  const [filtroHistoricoPeca, setFiltroHistoricoPeca] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const resetReposicaoForm = useCallback(() => {
    setEditingReposicaoId(null);
    setCodigoPeca(pecas[0]?.codigo ?? "");
    setGolpes(0);
    setMotivoId("");
    setObservacao("");
    setDataReposicao(new Date().toISOString());
  }, [pecas]);

  const loadFerramentas = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchFerramentas(
        {
          codigo: codigo.trim() || undefined,
          descricao: descricao.trim() || undefined,
          filial,
          page: 1,
          page_size: 50,
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
      setLoading(false);
    }
  }, [codigo, descricao, filial, getAccessToken]);

  const loadDetalhe = useCallback(
    async (options?: { pecaFilter?: string }) => {
    if (!codigoFerramenta) return;
    const pecaFilter = options?.pecaFilter ?? filtroHistoricoPeca;
    setLoading(true);
    setError(null);
    try {
      const [pecasData, motivosData, reposicoesData, componentesData] = await Promise.all([
        fetchPecas(codigoFerramenta, filial, getAccessToken),
        fetchMotivos(filial, getAccessToken),
        fetchReposicoes(
          {
            filial,
            codigo_ferramenta: codigoFerramenta,
            codigo_peca: pecaFilter || undefined,
          },
          getAccessToken,
        ),
        fetchComponentes(codigoFerramenta, filial, getAccessToken),
      ]);
      const pecaItems = pecasData.items ?? [];
      setPecas(pecaItems);
      setMotivos(motivosData.items ?? []);
      setReposicoes(reposicoesData.items ?? []);
      setComponentes(componentesData.items ?? []);
      setCodigoPeca((current) => current || pecaItems[0]?.codigo || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar detalhe.");
    } finally {
      setLoading(false);
    }
  },
    [codigoFerramenta, filial, filtroHistoricoPeca, getAccessToken],
  );

  useEffect(() => {
    if (codigoFerramenta) {
      setFiltroHistoricoPeca("");
      setEditingReposicaoId(null);
      void loadDetalhe({ pecaFilter: "" });
      return;
    }
    void loadFerramentas();
  }, [codigoFerramenta, filial, loadFerramentas]);

  useEffect(() => {
    if (!codigoFerramenta || !codigoPeca || editingReposicaoId) return;
    let active = true;
    suggestGolpes({ filial, codigo_ferramenta: codigoFerramenta, codigo_peca: codigoPeca }, getAccessToken)
      .then((data) => {
        if (active) setGolpes(data.total_golpes ?? 0);
      })
      .catch(() => {
        if (active) setGolpes(0);
      });
    return () => {
      active = false;
    };
  }, [codigoFerramenta, codigoPeca, editingReposicaoId, filial, getAccessToken]);

  async function handleSuggestGolpes() {
    if (!codigoFerramenta || !codigoPeca) return;
    try {
      const data = await suggestGolpes(
        { filial, codigo_ferramenta: codigoFerramenta, codigo_peca: codigoPeca },
        getAccessToken,
      );
      setGolpes(data.total_golpes ?? 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao sugerir golpes.");
    }
  }

  function handleEditReposicao(item: ReposicaoItem) {
    setEditingReposicaoId(item.reposicao_id);
    setCodigoPeca(item.codigo_peca);
    setGolpes(item.golpes);
    setMotivoId(item.motivo_id);
    setObservacao(item.observacao ?? "");
    setDataReposicao(item.data_reposicao);
    setSuccess(null);
    setError(null);
  }

  async function handleDeleteReposicao(item: ReposicaoItem) {
    if (!window.confirm(`Excluir reposição de ${item.codigo_peca} em ${new Date(item.data_reposicao).toLocaleString("pt-BR")}?`)) {
      return;
    }
    setError(null);
    setSuccess(null);
    try {
      await deleteReposicao(item.reposicao_id, getAccessToken);
      setSuccess("Reposição excluída.");
      resetReposicaoForm();
      await loadDetalhe();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao excluir reposição.");
    }
  }

  async function handleSubmitReposicao(event: React.FormEvent) {
    event.preventDefault();
    if (!codigoFerramenta || !codigoPeca || motivoId === "") return;
    setError(null);
    setSuccess(null);
    const payload = {
      filial,
      codigo_ferramenta: codigoFerramenta,
      codigo_peca: codigoPeca,
      data_reposicao: dataReposicao,
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
        render: (item) => (
          <button
            type="button"
            className="dm-link-btn"
            onClick={() => onNavigate(MAINTENANCE_ROUTES.miniAplicadorDetail(item.codigo))}
          >
            {item.codigo}
          </button>
        ),
      },
      {
        key: "descricao",
        header: "Descrição",
        render: (item) => item.descricao,
      },
    ],
    [onNavigate],
  );

  const reposicoesColumns = useMemo<DataTableColumn<ReposicaoItem>[]>(() => {
    const columns: DataTableColumn<ReposicaoItem>[] = [
      {
        key: "data",
        header: "Data",
        render: (item) => new Date(item.data_reposicao).toLocaleString("pt-BR"),
      },
      { key: "peca", header: "Peça", render: (item) => item.codigo_peca },
      { key: "golpes", header: "Golpes", render: (item) => item.golpes, align: "right" },
      {
        key: "motivo",
        header: "Motivo",
        render: (item) => item.motivo_descricao ?? item.motivo_id,
      },
    ];

    if (canManageMiniApplicators) {
      columns.push({
        key: "acoes",
        header: "Ações",
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
      { key: "nivel", header: "Nível", render: (item) => item.nivel, align: "center" },
      {
        key: "codigo",
        header: "Código",
        render: (item) => (
          <span className="dm-datatable__cell-indent" style={{ paddingLeft: `${item.nivel * 12}px` }}>
            {item.codigo}
          </span>
        ),
      },
      { key: "descricao", header: "Descrição", render: (item) => item.descricao },
      { key: "unidade", header: "Un.", render: (item) => item.unidade, align: "center" },
      {
        key: "estoque01",
        header: "Estoque 01",
        render: (item) => item.estoque_local_01.toLocaleString("pt-BR"),
        align: "right",
      },
      {
        key: "estoque99",
        header: "Estoque 99",
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
        moduleHomePath={moduleHomePath}
        showConfiguration={canManageMiniApplicators}
        currentPath={pathname}
        onNavigate={onNavigate}
        actions={
          <button
            type="button"
            className="dm-primary-btn"
            onClick={() => (codigoFerramenta ? void loadDetalhe() : void loadFerramentas())}
            disabled={loading}
          >
            <RefreshCw size={16} />
            {loading ? "Carregando…" : "Atualizar"}
          </button>
        }
      />

      {!codigoFerramenta ? (
        <>
          <FilterBar leading={<FilialBadge filial={filial} />}>
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
            <button type="button" className="dm-primary-btn" onClick={() => void loadFerramentas()}>
              Buscar
            </button>
          </FilterBar>

          {error ? <StateBox variant="error">{error}</StateBox> : null}

          <DataTableSection
            title="Ferramentas"
            badge={`${total} registro(s)`}
            columns={ferramentasColumns}
            rows={items}
            loading={loading}
            emptyMessage="Nenhuma ferramenta encontrada."
            getRowKey={(item) => item.codigo}
          />
        </>
      ) : (
        <>
          {error ? <StateBox variant="error">{error}</StateBox> : null}
          {success ? <StateBox variant="success">{success}</StateBox> : null}

          {canManageMiniApplicators ? (
            <section className="dm-card">
              <h3 className="dm-section-header__title">
                {editingReposicaoId ? "Editar reposição" : "Nova reposição"}
              </h3>
              <FilterBar embedded leading={<FilialBadge filial={filial} />} onSubmit={handleSubmitReposicao}>
                <label className="dm-field">
                  <span>Peça</span>
                  <select value={codigoPeca} onChange={(event) => setCodigoPeca(event.target.value)}>
                    {pecas.map((peca) => (
                      <option key={peca.codigo} value={peca.codigo}>
                        {peca.codigo} — {peca.descricao}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="dm-field">
                  <span>Golpes</span>
                  <input
                    type="number"
                    min={1}
                    value={golpes}
                    onChange={(event) => setGolpes(Number(event.target.value))}
                  />
                </label>
                <button type="button" className="dm-ghost-btn" onClick={() => void handleSuggestGolpes()}>
                  Sugerir golpes
                </button>
                <label className="dm-field">
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
                <label className="dm-field">
                  <span>Observação</span>
                  <input value={observacao} onChange={(event) => setObservacao(event.target.value)} />
                </label>
                <button type="submit" className="dm-primary-btn">
                  {editingReposicaoId ? "Salvar alterações" : "Registrar reposição"}
                </button>
                {editingReposicaoId ? (
                  <button type="button" className="dm-ghost-btn" onClick={resetReposicaoForm}>
                    Cancelar edição
                  </button>
                ) : null}
              </FilterBar>
            </section>
          ) : null}

          <DataTableSection
            title="Histórico de reposições"
            actions={
              <button
                type="button"
                className="dm-ghost-btn"
                onClick={() => onNavigate(MAINTENANCE_ROUTES.miniAplicadores)}
              >
                Voltar para lista
              </button>
            }
            toolbar={
              <FilterBar embedded>
                <label className="dm-field">
                  <span>Filtrar por peça</span>
                  <select
                    value={filtroHistoricoPeca}
                    onChange={(event) => setFiltroHistoricoPeca(event.target.value)}
                  >
                    <option value="">Todas</option>
                    {pecas.map((peca) => (
                      <option key={peca.codigo} value={peca.codigo}>
                        {peca.codigo}
                      </option>
                    ))}
                  </select>
                </label>
                <button type="button" className="dm-ghost-btn" onClick={() => void loadDetalhe()}>
                  Aplicar filtro
                </button>
              </FilterBar>
            }
            columns={reposicoesColumns}
            rows={reposicoes}
            loading={loading}
            emptyMessage="Nenhuma reposição registrada."
            getRowKey={(item) => item.reposicao_id}
            getRowClassName={(item) => (editingReposicaoId === item.reposicao_id ? "is-selected" : undefined)}
          />

          <DataTableSection
            title="Componentes e estoque"
            badge={`${componentes.length} item(ns)`}
            columns={componentesColumns}
            rows={componentes}
            loading={loading}
            emptyMessage="Nenhum componente na estrutura desta ferramenta."
            getRowKey={(item, index) => `${item.codigo}-${item.nivel}-${index}`}
          />
        </>
      )}
    </MaintenanceShell>
  );
}
