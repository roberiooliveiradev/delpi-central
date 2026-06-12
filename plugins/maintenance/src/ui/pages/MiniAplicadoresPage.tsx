import { useCallback, useEffect, useState } from "react";
import { Hammer, RefreshCw } from "lucide-react";

import { MaintenanceShell } from "../../components/MaintenanceShell";
import { PageHeader } from "../../components/PageHeader";
import { MAINTENANCE_ROUTES } from "../../constants/routes";
import {
  createReposicao,
  fetchFerramentas,
  fetchMotivos,
  fetchPecas,
  fetchReposicoes,
  suggestGolpes,
  type FerramentaItem,
  type MotivoItem,
  type ReposicaoItem,
} from "../../data/api/maintenanceApi";

type MiniAplicadoresPageProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  onNavigate: (path: string) => void;
  codigoFerramenta?: string;
};

export function MiniAplicadoresPage({
  getAccessToken,
  pathname,
  onNavigate,
  codigoFerramenta,
}: MiniAplicadoresPageProps) {
  const [descricao, setDescricao] = useState("");
  const [filial, setFilial] = useState("01");
  const [items, setItems] = useState<FerramentaItem[]>([]);
  const [total, setTotal] = useState(0);
  const [pecas, setPecas] = useState<FerramentaItem[]>([]);
  const [motivos, setMotivos] = useState<MotivoItem[]>([]);
  const [reposicoes, setReposicoes] = useState<ReposicaoItem[]>([]);
  const [codigoPeca, setCodigoPeca] = useState("");
  const [golpes, setGolpes] = useState(0);
  const [motivoId, setMotivoId] = useState<number | "">("");
  const [observacao, setObservacao] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

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

  const loadDetalhe = useCallback(async () => {
    if (!codigoFerramenta) return;
    setLoading(true);
    setError(null);
    try {
      const [pecasData, motivosData, reposicoesData] = await Promise.all([
        fetchPecas(codigoFerramenta, getAccessToken),
        fetchMotivos(getAccessToken),
        fetchReposicoes({ filial, codigo_ferramenta: codigoFerramenta }, getAccessToken),
      ]);
      setPecas(pecasData.items ?? []);
      setMotivos(motivosData.items ?? []);
      setReposicoes(reposicoesData.items ?? []);
      if ((pecasData.items ?? []).length > 0 && !codigoPeca) {
        setCodigoPeca(pecasData.items[0].codigo);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar detalhe.");
    } finally {
      setLoading(false);
    }
  }, [codigoFerramenta, codigoPeca, filial, getAccessToken]);

  useEffect(() => {
    if (codigoFerramenta) {
      void loadDetalhe();
      return;
    }
    void loadFerramentas();
  }, [codigoFerramenta, loadDetalhe, loadFerramentas]);

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

  async function handleCreateReposicao(event: React.FormEvent) {
    event.preventDefault();
    if (!codigoFerramenta || !codigoPeca || motivoId === "") return;
    setError(null);
    setSuccess(null);
    try {
      await createReposicao(
        {
          filial,
          codigo_ferramenta: codigoFerramenta,
          codigo_peca: codigoPeca,
          data_reposicao: new Date().toISOString(),
          golpes,
          motivo_id: Number(motivoId),
          observacao: observacao.trim() || undefined,
        },
        getAccessToken,
      );
      setSuccess("Reposição registrada.");
      setObservacao("");
      await loadDetalhe();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao registrar reposição.");
    }
  }

  return (
    <MaintenanceShell>
      <PageHeader
        title={codigoFerramenta ? `Ferramenta ${codigoFerramenta}` : "Mini-aplicadores"}
        subtitle={
          codigoFerramenta
            ? "Histórico de reposições e cadastro de nova troca."
            : "Ferramentas dos grupos 23 e 24 via api-delpi."
        }
        icon={Hammer}
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
            <label className="dm-field">
              <span>Filial</span>
              <select value={filial} onChange={(event) => setFilial(event.target.value)}>
                <option value="01">01 — Matriz</option>
                <option value="02">02 — ES</option>
              </select>
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
                            onNavigate(`${MAINTENANCE_ROUTES.miniAplicadores}/${item.codigo}`)
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

          <section className="dm-card">
            <h3 className="dm-card__title">Nova reposição</h3>
            <form className="dm-filter-bar" onSubmit={handleCreateReposicao}>
              <label className="dm-field">
                <span>Filial</span>
                <select value={filial} onChange={(event) => setFilial(event.target.value)}>
                  <option value="01">01 — Matriz</option>
                  <option value="02">02 — ES</option>
                </select>
              </label>
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
                Registrar reposição
              </button>
            </form>
          </section>

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
            <div className="dm-table-wrap">
              <table className="dm-table">
                <thead>
                  <tr>
                    <th>Data</th>
                    <th>Peça</th>
                    <th>Golpes</th>
                    <th>Motivo</th>
                  </tr>
                </thead>
                <tbody>
                  {reposicoes.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="dm-table__empty">
                        Nenhuma reposição registrada.
                      </td>
                    </tr>
                  ) : null}
                  {reposicoes.map((item) => (
                    <tr key={item.reposicao_id}>
                      <td data-label="Data">{new Date(item.data_reposicao).toLocaleString("pt-BR")}</td>
                      <td data-label="Peça">{item.codigo_peca}</td>
                      <td data-label="Golpes">{item.golpes}</td>
                      <td data-label="Motivo">{item.motivo_descricao ?? item.motivo_id}</td>
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
