import { useEffect, useState, type FormEvent } from "react";

import { createComment, listComments } from "../api/requestsApi";
import type { RequestComment } from "../types/requests";

type CommentsPanelProps = {
  requestId: string;
};

export function CommentsPanel({ requestId }: CommentsPanelProps) {
  const [items, setItems] = useState<RequestComment[]>([]);
  const [body, setBody] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function reload(signal?: AbortSignal) {
    const data = await listComments(requestId, { signal });
    setItems(data.items || []);
  }

  useEffect(() => {
    const ac = new AbortController();
    reload(ac.signal).catch((err: Error) => {
      if (err.name !== "AbortError") setError(err.message);
    });
    return () => ac.abort();
  }, [requestId]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!body.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await createComment(requestId, body.trim());
      setBody("");
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao comentar");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="dashboard-my-requests__panel" data-help="comments">
      <h2>Comentários</h2>
      {error ? <p className="dashboard-my-requests__error">{error}</p> : null}
      <ul className="dashboard-my-requests__list">
        {items.map((item) => (
          <li key={item.id}>
            <strong>{item.author_name || "Usuário"}</strong>: {item.body}
          </li>
        ))}
      </ul>
      <form className="dashboard-my-requests__form" onSubmit={onSubmit}>
        <label>
          Novo comentário
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            rows={3}
            disabled={busy}
          />
        </label>
        <button type="submit" className="dashboard-my-requests__btn" disabled={busy || !body.trim()}>
          Enviar
        </button>
      </form>
    </section>
  );
}
