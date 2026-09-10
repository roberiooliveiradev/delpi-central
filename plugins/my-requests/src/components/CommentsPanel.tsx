import { useEffect, useMemo, useRef, useState } from "react";

import { createComment, listComments } from "../api/requestsApi";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { formatDateTimePtBr } from "../content/presentationLabels";
import { useParticipantAvatarUrls } from "../hooks/useParticipantAvatarUrls";
import type { RequestComment } from "../types/requests";
import {
  MR_PORTAL_SCOPE,
  MyRequestsMentionComposer,
  MyRequestsMessageThread,
  MyRequestsRoomConversationChatColumn,
  MyRequestsRoomPanel,
  MyRequestsSectionCard,
  MyRequestsStateBanner,
  type MessageThreadItem,
} from "../ui/mrUi";
import { shouldStickThreadToBottom } from "../utils/threadStickToBottom";

type CommentsPanelProps = {
  requestId: string;
  canComment?: boolean;
  refreshKey?: number;
};

const COMPOSER_LABELS = {
  placeholder: "Escreva uma mensagem sobre a solicitação…",
  sendAriaLabel: "Enviar mensagem",
  attachAriaLabel: "Anexar",
  mentionListAriaLabel: "Menções",
  mentionEmptyLabel: "Nenhuma menção",
};

function toThreadItems(
  comments: RequestComment[],
  avatarByUserId: ReadonlyMap<string, string>,
): MessageThreadItem[] {
  // API returns created_at DESC; chat UI needs ASC (oldest top, newest bottom).
  const chronological = [...comments].reverse();
  return chronological.map((item) => {
    const authorId = (item.author_user_id || "").trim();
    return {
      id: item.id,
      kind: "text",
      bodyText: item.body,
      createdAtLabel: item.created_at
        ? formatDateTimePtBr(item.created_at)
        : "",
      authorName: item.author_name || "Usuário",
      authorUserId: authorId || null,
      authorSrc: authorId ? avatarByUserId.get(authorId) || null : null,
      mine: Boolean(item.is_mine),
    };
  });
}

/** Conversation UI over RequestComment — kit MessageThread + MentionComposer. */
export function CommentsPanel({
  requestId,
  canComment = false,
  refreshKey = 0,
}: CommentsPanelProps) {
  const [items, setItems] = useState<RequestComment[]>([]);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const msgsRef = useRef<HTMLDivElement | null>(null);
  const stickToBottomRef = useRef(true);

  const authorIds = useMemo(
    () => items.map((row) => row.author_user_id),
    [items],
  );
  const avatarByUserId = useParticipantAvatarUrls(authorIds);

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
  }, [requestId, refreshKey]);

  const threadItems = useMemo(
    () => toThreadItems(items, avatarByUserId),
    [items, avatarByUserId],
  );

  useEffect(() => {
    const el = msgsRef.current;
    if (!el || !stickToBottomRef.current) return;
    el.scrollTop = el.scrollHeight;
  }, [threadItems, refreshKey]);

  async function onSend(markdown: string) {
    const text = markdown.trim();
    if (!canComment || !text || busy) return;
    setBusy(true);
    setError(null);
    try {
      await createComment(requestId, text);
      setDraft("");
      stickToBottomRef.current = true;
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao enviar mensagem");
    } finally {
      setBusy(false);
    }
  }

  return (
    <MyRequestsSectionCard
      title="Conversa sobre a solicitação"
      hint={MY_REQUESTS_HELP_TOOLTIPS.comments.section}
    >
      <div
        className="my-requests-detail-conversation"
        data-help="comments"
      >
        {error ? (
          <MyRequestsStateBanner variant="error">{error}</MyRequestsStateBanner>
        ) : null}

        <div className="my-requests-detail-conversation__frame">
          <MyRequestsRoomPanel aria-label="Conversa sobre a solicitação">
            <MyRequestsRoomConversationChatColumn
              msgsRef={msgsRef}
              onMsgsScroll={(event) => {
                stickToBottomRef.current = shouldStickThreadToBottom(
                  event.currentTarget,
                );
              }}
              dock={
                canComment ? (
                  <MyRequestsMentionComposer
                    value={draft}
                    onChange={setDraft}
                    onSubmit={(md) => void onSend(md)}
                    disabled={busy}
                    submitting={busy}
                    showAttach={false}
                    portalScopeClassName={MR_PORTAL_SCOPE}
                    labels={COMPOSER_LABELS}
                  />
                ) : (
                  <MyRequestsStateBanner>
                    Você pode ler a conversa, mas não tem permissão para enviar
                    mensagens neste momento.
                  </MyRequestsStateBanner>
                )
              }
            >
              <MyRequestsMessageThread
                messages={threadItems}
                listAriaLabel="Mensagens da solicitação"
                emptyLabel="Nenhuma mensagem ainda. Inicie a conversa."
                portalScopeClassName={MR_PORTAL_SCOPE}
              />
            </MyRequestsRoomConversationChatColumn>
          </MyRequestsRoomPanel>
        </div>
      </div>
    </MyRequestsSectionCard>
  );
}
