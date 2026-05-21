import { useCallback, useEffect, useState } from "react";
import type { AppProps } from "../../App";
import {
  createRevisao,
  fetchOptions,
  fetchProcesso,
  fetchRevisoes,
  type OptionsData,
  type Processo,
  type Revisao,
} from "../../data/api/transformometroApi";
import { RevisaoCadastroPanel } from "./RevisaoCadastroPanel";
import "./ProcessosPage.css";

type Props = Pick<AppProps, "getAccessToken"> & {
  processoId: string;
  onBack: () => void;
};

export function ProcessoDetailPage({ getAccessToken, processoId, onBack }: Props) {
  const [processo, setProcesso] = useState<Processo | null>(null);
  const [revisoes, setRevisoes] = useState<Revisao[]>([]);
  const [options, setOptions] = useState<OptionsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showRevisaoForm, setShowRevisaoForm] = useState(false);
  const [selectedRevisaoId, setSelectedRevisaoId] = useState<string | null>(null);
  const [revForm, setRevForm] = useState({
    versao_revisao: "1.0.0",
    cenario_tipo: "baseline",
    data_inicio_vigencia: new Date().toISOString().slice(0, 10),
    revisao_ativa: true,
  });

  const load = useCallback(async () => {
    setError(null);
    try {
      const [proc, revs, opts] = await Promise.all([
        fetchProcesso(processoId, getAccessToken),
        fetchRevisoes(processoId, getAccessToken),
        fetchOptions(getAccessToken),
      ]);
      setProcesso(proc);
      setRevisoes(revs.items);
      setOptions(opts);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar");
    }
  }, [getAccessToken, processoId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleCreateRevisao(e: React.FormEvent) {
    e.preventDefault();
    try {
      await createRevisao(
        {
          processo_id: processoId,
          ...revForm,
        },
        getAccessToken
      );
      setShowRevisaoForm(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar revisão");
    }
  }

  if (!processo) {
    return (
      <div className="tm-page">
        <button type="button" className="tm-btn tm-btn--ghost" onClick={onBack}>
          ← Voltar
        </button>
        <p>{error ?? "Carregando processo…"}</p>
      </div>
    );
  }

  return (
    <div className="tm-page">
      <button type="button" className="tm-btn tm-btn--ghost" onClick={onBack}>
        ← Processos
      </button>

      <header className="tm-page__header">
        <div>
          <h1>
            {processo.codigo_processo} — {processo.nome_processo}
          </h1>
          <p>
            Filial {processo.filial_id} · {processo.setor_id} · {processo.status_processo}
          </p>
        </div>
        <button
          type="button"
          className="tm-btn tm-btn--primary"
          onClick={() => setShowRevisaoForm((v) => !v)}
        >
          {showRevisaoForm ? "Cancelar" : "Nova revisão"}
        </button>
      </header>

      {error ? <div className="tm-alert tm-alert--error">{error}</div> : null}

      {showRevisaoForm && options ? (
        <form className="tm-card tm-form" onSubmit={handleCreateRevisao}>
          <h2>Nova revisão</h2>
          <div className="tm-form__row">
            <label>
              Versão
              <input
                required
                value={revForm.versao_revisao}
                onChange={(e) => setRevForm({ ...revForm, versao_revisao: e.target.value })}
              />
            </label>
            <label>
              Cenário
              <select
                value={revForm.cenario_tipo}
                onChange={(e) => setRevForm({ ...revForm, cenario_tipo: e.target.value })}
              >
                {options.cenario_tipo.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Início vigência
              <input
                type="date"
                required
                value={revForm.data_inicio_vigencia}
                onChange={(e) =>
                  setRevForm({ ...revForm, data_inicio_vigencia: e.target.value })
                }
              />
            </label>
          </div>
          <label>
            <input
              type="checkbox"
              checked={revForm.revisao_ativa}
              onChange={(e) => setRevForm({ ...revForm, revisao_ativa: e.target.checked })}
            />{" "}
            Marcar como revisão ativa
          </label>
          <button type="submit" className="tm-btn tm-btn--primary">
            Salvar revisão
          </button>
        </form>
      ) : null}

      <section className="tm-card">
        <h2>Revisões ({revisoes.length})</h2>
        <p className="tm-muted">
          Clique em uma revisão para cadastrar medição, investimentos e recursos compartilhados.
        </p>
        {revisoes.length === 0 ? (
          <p>Nenhuma revisão. Cadastre baseline e melhoria para mensurar economia.</p>
        ) : (
          <>
            <table className="tm-table">
              <thead>
                <tr>
                  <th>Versão</th>
                  <th>Cenário</th>
                  <th>Vigência</th>
                  <th>Ativa</th>
                </tr>
              </thead>
              <tbody>
                {revisoes.map((r) => (
                  <tr
                    key={r.revisao_id}
                    className={
                      selectedRevisaoId === r.revisao_id ? "tm-table__row--selected" : undefined
                    }
                    onClick={() =>
                      setSelectedRevisaoId((id) =>
                        id === r.revisao_id ? null : r.revisao_id
                      )
                    }
                  >
                    <td>{r.versao_revisao}</td>
                    <td>{r.cenario_tipo}</td>
                    <td>{r.data_inicio_vigencia}</td>
                    <td>
                      {r.revisao_ativa ? (
                        <span className="tm-badge tm-badge--active">ativa</span>
                      ) : (
                        "—"
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {selectedRevisaoId && options && revisoes.find((r) => r.revisao_id === selectedRevisaoId) ? (
              <RevisaoCadastroPanel
                revisao={revisoes.find((r) => r.revisao_id === selectedRevisaoId)!}
                options={options}
                getAccessToken={getAccessToken}
                onError={setError}
                onRevisaoUpdated={load}
              />
            ) : null}
          </>
        )}
      </section>
    </div>
  );
}
