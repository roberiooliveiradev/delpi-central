import { useCallback, useEffect, useState } from "react";
import type { AppProps } from "../../App";
import {
  createProcesso,
  fetchOptions,
  fetchProcessos,
  type OptionsData,
  type Processo,
} from "../../data/api/transformometroApi";
import "./ProcessosPage.css";

type Props = Pick<AppProps, "getAccessToken"> & {
  onOpenProcesso: (id: string) => void;
};

export function ProcessosPage({ getAccessToken, onOpenProcesso }: Props) {
  const [items, setItems] = useState<Processo[]>([]);
  const [options, setOptions] = useState<OptionsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    nome_processo: "",
    filial_id: "01",
    setor_id: "engenharia",
    status_processo: "ativo",
  });

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [list, opts] = await Promise.all([
        fetchProcessos(getAccessToken),
        fetchOptions(getAccessToken),
      ]);
      setItems(list.items);
      setOptions(opts);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar");
    } finally {
      setLoading(false);
    }
  }, [getAccessToken]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      const created = await createProcesso(form, getAccessToken);
      setShowForm(false);
      await load();
      onOpenProcesso(created.processo_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar");
    }
  }

  return (
    <div className="tm-page">
      <header className="tm-page__header">
        <div>
          <h1>Processos</h1>
          <p>Cadastro mestre das melhorias monitoradas.</p>
        </div>
        <button type="button" className="tm-btn tm-btn--primary" onClick={() => setShowForm((v) => !v)}>
          {showForm ? "Cancelar" : "Novo processo"}
        </button>
      </header>

      {error ? <div className="tm-alert tm-alert--error">{error}</div> : null}

      {showForm && options ? (
        <form className="tm-card tm-form" onSubmit={handleCreate}>
          <h2>Novo processo</h2>
          <label>
            Nome
            <input
              required
              value={form.nome_processo}
              onChange={(e) => setForm({ ...form, nome_processo: e.target.value })}
            />
          </label>
          <div className="tm-form__row">
            <label>
              Filial
              <select
                value={form.filial_id}
                onChange={(e) => setForm({ ...form, filial_id: e.target.value })}
              >
                {options.filiais.map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Setor
              <select
                value={form.setor_id}
                onChange={(e) => setForm({ ...form, setor_id: e.target.value })}
              >
                {options.setores.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Status
              <select
                value={form.status_processo}
                onChange={(e) => setForm({ ...form, status_processo: e.target.value })}
              >
                {options.status_processo.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <button type="submit" className="tm-btn tm-btn--primary">
            Salvar processo
          </button>
        </form>
      ) : null}

      <section className="tm-card">
        {loading ? (
          <p>Carregando…</p>
        ) : items.length === 0 ? (
          <p>Nenhum processo cadastrado. Crie o primeiro acima.</p>
        ) : (
          <table className="tm-table">
            <thead>
              <tr>
                <th>Código</th>
                <th>Processo</th>
                <th>Filial</th>
                <th>Setor</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.processo_id} onClick={() => onOpenProcesso(row.processo_id)}>
                  <td>{row.codigo_processo}</td>
                  <td>{row.nome_processo}</td>
                  <td>{row.filial_id}</td>
                  <td>{row.setor_id}</td>
                  <td>{row.status_processo}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
