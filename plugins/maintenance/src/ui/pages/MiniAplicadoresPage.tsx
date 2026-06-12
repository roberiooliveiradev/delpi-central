import { useCallback, useEffect, useState } from "react";
import { Hammer, RefreshCw } from "lucide-react";

import { MaintenanceShell } from "../../components/MaintenanceShell";
import { MiniAplicadoresPageHeader } from "../../components/MiniAplicadoresPageHeader";
import { MAINTENANCE_ROUTES } from "../../constants/routes";
import {
  useMaintenanceActiveFilial,
  useMaintenanceModuleHomePath,
  useOperationalFilial,
} from "../../hooks/useMaintenanceScope";
import {
  createReposicao,
  deleteReposicao,
  fetchFerramentas,
  fetchMotivos,
  fetchPecas,
  fetchReposicoes,
  suggestGolpes,
  updateReposicao,
  type FerramentaItem,
  type MotivoItem,
  type ReposicaoItem,
} from "../../data/api/maintenanceApi";

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
  const [items, setItems] = useState<FerramentaItem[]>([]);
  const [total, setTotal] = useState(0);
  const [pecas, setPecas] = useState<FerramentaItem[]>([]);
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
        { descricao: descricao.trim() || undefined, filial, page: 1, page_size: 50 },
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
  }, [descricao, filial, getAccessToken]);

  const loadDetalhe = useCallback(
    async (options?: { pecaFilter?: string }) => {
    if (!codigoFerramenta) return;
    const pecaFilter = options?.pecaFilter ?? filtroHistoricoPeca;
    setLoading(true);
    setError(null);
    try {
      const [pecasData, motivosData, reposicoesData] = await Promise.all([
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
      ]);
      const pecaItems = pecasData.items ?? [];
      setPecas(pecaItems);
      setMotivos(motivosData.items ?? []);
      setReposicoes(reposicoesData.items ?? []);
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
          <section className="dm-card dm-filter-bar">
            <p className="dm-filial-badge">Filial operacional: {filial}</p>
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
          </section>

          <section className="dm-card">
            <div className="dm-card__header">
              <h3 className="dm-card__title">Ferramentas</h3>
              <span className="dm-badge">{total} registro(s)</span>
            </div>
            {error ? <p className="dm-state-box dm-state-box--error">{error}</p> : null}
            <div className="dm-table-wrap">
              <table className="dm-table">
                <thead>
                  <tr>
                    <th>Código</th>
                    <th>Descrição</th>
                  </tr>
                </thead>
                <tbody>
                  {items.length === 0 && !loading ? (
                    <tr>
                      <td colSpan={2} className="dm-table__empty">
                        Nenhuma ferramenta encontrada.
                      </td>
                    </tr>
                  ) : null}
                  {items.map((item) => (
                    <tr key={item.codigo}>
                      <td data-label="Código">
                        <button
                          type="button"
                          className="dm-link-btn"
                          onClick={() =>
                            onNavigate(MAINTENANCE_ROUTES.miniAplicadorDetail(item.codigo))
                          }
                        >
                          {item.codigo}
                        </button>
                      </td>
                      <td data-label="Descrição">{item.descricao}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      ) : (
        <>
          {error ? <p className="dm-state-box dm-state-box--error">{error}</p> : null}
          {success ? <p className="dm-state-box">{success}</p> : null}

          {canManageMiniApplicators ? (
            <section className="dm-card">
              <h3 className="dm-card__title">
                {editingReposicaoId ? "Editar reposição" : "Nova reposição"}
              </h3>
              <form className="dm-filter-bar" onSubmit={handleSubmitReposicao}>
                <p className="dm-filial-badge">Filial operacional: {filial}</p>
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
              </form>
            </section>
          ) : null}

          <section className="dm-card">
            <div className="dm-card__header">
              <h3 className="dm-card__title">Histórico de reposições</h3>
              <button
                type="button"
                className="dm-ghost-btn"
                onClick={() => onNavigate(MAINTENANCE_ROUTES.miniAplicadores)}
              >
                Voltar para lista
              </button>
            </div>
            <div className="dm-filter-bar">
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
            </div>
            <div className="dm-table-wrap">
              <table className="dm-table">
                <thead>
                  <tr>
                    <th>Data</th>
                    <th>Peça</th>
                    <th>Golpes</th>
                    <th>Motivo</th>
                    {canManageMiniApplicators ? <th>Ações</th> : null}
                  </tr>
                </thead>
                <tbody>
                  {reposicoes.length === 0 ? (
                    <tr>
                      <td colSpan={canManageMiniApplicators ? 5 : 4} className="dm-table__empty">
                        Nenhuma reposição registrada.
                      </td>
                    </tr>
                  ) : null}
                  {reposicoes.map((item) => (
                    <tr key={item.reposicao_id} className={editingReposicaoId === item.reposicao_id ? "is-selected" : ""}>
                      <td data-label="Data">{new Date(item.data_reposicao).toLocaleString("pt-BR")}</td>
                      <td data-label="Peça">{item.codigo_peca}</td>
                      <td data-label="Golpes">{item.golpes}</td>
                      <td data-label="Motivo">{item.motivo_descricao ?? item.motivo_id}</td>
                      {canManageMiniApplicators ? (
                        <td data-label="Ações">
                          <div className="dm-row-actions">
                            <button
                              type="button"
                              className="dm-ghost-btn"
                              onClick={() => handleEditReposicao(item)}
                            >
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
                        </td>
                      ) : null}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </MaintenanceShell>
  );
}
