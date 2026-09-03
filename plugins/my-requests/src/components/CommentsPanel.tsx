import { useEffect, useState, type FormEvent } from "react";
import { ActionButton, FieldLabel, NativeTextAreaControl } from "@delpi/plugin-ui/index";

import { createComment, listComments } from "../api/requestsApi";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { RequestComment } from "../types/requests";
import {
  MyRequestsEmptyState,
  MyRequestsFormActions,
  MyRequestsSectionCard,
  MyRequestsStateBanner,
} from "../ui/mrUi";

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
    <MyRequestsSectionCard title="Comentários">
      <div data-help="comments" title={MY_REQUESTS_HELP_TOOLTIPS.comments.section}>
        {error ? (
          <MyRequestsStateBanner variant="error">{error}</MyRequestsStateBanner>
        ) : null}
        {items.length === 0 ? (
          <MyRequestsEmptyState message="Nenhum comentário ainda." />
        ) : (
          <ul className="my-requests-domain-list">
            {items.map((item) => (
              <li key={item.id}>
                <strong>{item.author_name || "Usuário"}</strong>: {item.body}
              </li>
            ))}
          </ul>
        )}
        <form className="my-requests-form-stack" onSubmit={onSubmit}>
          <div>
            <FieldLabel label="Novo comentário" htmlFor="mr-new-comment" />
            <NativeTextAreaControl
              id="mr-new-comment"
              value={body}
              onChange={setBody}
              rows={3}
              disabled={busy}
            />
          </div>
          <MyRequestsFormActions>
            <ActionButton
              type="submit"
              variant="primary"
              disabled={busy || !body.trim()}
            >
              Enviar
            </ActionButton>
          </MyRequestsFormActions>
        </form>
      </div>
    </MyRequestsSectionCard>
  );
}
