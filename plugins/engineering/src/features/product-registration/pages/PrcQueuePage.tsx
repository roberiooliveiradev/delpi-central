/** Fila do Controle e Cadastro de Produtos — escopo vem da API. */

import { useCallback, useEffect, useState } from "react";
import { fetchPrcQueue, type PrcRequestSummary } from "../api/productRegistrationApi";
import { navigatePrc } from "../prcNavigate";

const STATUS_LABELS: Record<string, string> = {
  submitted: "Enviada",
  in_progress: "Em atendimento",
  needs_information: "Aguardando informações",
  under_review: "Em revisão",
  completed: "Concluída",
  rejected: "Rejeitada",
};

const TYPE_LABELS: Record<string, string> = {
  create: "Criação",
  update: "Alteração",
};

export function PrcQueuePage({ basePath }: { basePath: string }) {
  const [items, setItems] = useState<PrcRequestSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const [type, setType] = useState("");
  const [search, setSearch] = useState("");
  const [state, setState] = useState<"loading" | "ok" | "error" | "forbidden">(
    "loading",
  );
  const [error, setError] = useState("");
  const pageSize = 25;

  const load = useCallback(
    async (p = page) => {
      setState("loading");
      try {
        const env = await fetchPrcQueue({
          status, type, search, page: p, pageSize,
        });
        setItems(env.data.items);
        setTotal(env.data.total);
        setState("ok");
      } catch (e) {
        const err = e as { status?: number; message?: string };
        setError(err.message || "Falha ao carregar a fila.");
        setState(err.status === 403 ? "forbidden" : "error");
      }
    },
    [status, type, search, page],
  );

  useEffect(() => {
    load(page);
  }, [status, type, page]);

  const pages = Math.max(1, Math.ceil(total / pageSize));

  if (state === "forbidden") {
    return (
      <section className="engineering-page" role="alert">
        <h2>Acesso restrito</h2>
        <p>
          Você não possui permissão para acessar o Controle e Cadastro de
          Produtos.
        </p>
      </section>
    );
  }

  return (
    <section className="engineering-page">
      <header>
        <h2>Controle e Cadastro de Produtos</h2>
        <p className="engineering-subtitle">
          Fila de solicitações de cadastro e alteração de matérias-primas
        </p>
      </header>

      <div className="engineering-filters" role="search">
        <input
          type="search"
          placeholder="Buscar por código ou descrição"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              setPage(1);
              load(1);
            }
          }}
          aria-label="Buscar solicitação"
        />
        <select
          value={status}
          onChange={(e) => {
            setStatus(e.target.value);
            setPage(1);
          }}
          aria-label="Filtrar por status"
        >
          <option value="">Todos os status</option>
          {Object.entries(STATUS_LABELS).map(([v, l]) => (
            <option key={v} value={v}>
              {l}
            </option>
          ))}
        </select>
        <select
          value={type}
          onChange={(e) => {
            setType(e.target.value);
            setPage(1);
          }}
          aria-label="Filtrar por tipo"
        >
          <option value="">Todos os tipos</option>
          <option value="create">Criação</option>
          <option value="update">Alteração</option>
        </select>
        <button type="button" onClick={() => load()}>
          Atualizar
        </button>
      </div>

      {state === "loading" ? <p role="status">Carregando…</p> : null}
      {state === "error" ? <p role="alert">{error}</p> : null}
      {state === "ok" && items.length === 0 ? (
        <p>Nenhuma solicitação no escopo atual.</p>
      ) : null}

      {items.length > 0 ? (
        <div className="engineering-table-wrapper">
          <table className="engineering-table">
            <thead>
              <tr>
                <th>Solicitação</th>
                <th>Tipo</th>
                <th>Solicitante</th>
                <th>Origem</th>
                <th>Código oficial</th>
                <th>Abertura</th>
                <th>Status</th>
                <th>Responsável</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>
                    <button
                      type="button"
                      className="engineering-link"
                      onClick={() =>
                        navigatePrc(`product-registration/${item.id}`, basePath)
                      }
                    >
                      {item.id.slice(0, 8)}
                    </button>
                  </td>
                  <td>{TYPE_LABELS[item.requestType] || item.requestType}</td>
                  <td>{item.requester.displayName || item.requester.subject}</td>
                  <td>{item.source}</td>
                  <td>{item.officialCode || "—"}</td>
                  <td>{new Date(item.createdAt).toLocaleString("pt-BR")}</td>
                  <td>{STATUS_LABELS[item.status] || item.status}</td>
                  <td>{item.assignedTo || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      <nav className="engineering-pagination" aria-label="Paginação">
        <button
          type="button"
          disabled={page <= 1}
          onClick={() => setPage((p) => p - 1)}
        >
          Anterior
        </button>
        <span>
          Página {page} de {pages} ({total} itens)
        </span>
        <button
          type="button"
          disabled={page >= pages}
          onClick={() => setPage((p) => p + 1)}
        >
          Próxima
        </button>
      </nav>
    </section>
  );
}
