import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  listInlineAttachmentIdsFromMarkdown,
  listInlinePendingIdsFromMarkdown,
  rewriteInlinePendingInMarkdown,
} from "@delpi/plugin-ui/index";

import {
  createComment,
  downloadCommentAttachmentBlob,
  listComments,
  patchComment,
  uploadCommentAttachment,
} from "../api/requestsApi";
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
  attachAriaLabel: "Anexar imagem",
  mentionListAriaLabel: "Menções",
  mentionEmptyLabel: "Nenhuma menção",
  formatToggleAriaLabel: "Formatar",
  formatBoldAriaLabel: "Negrito",
  formatItalicAriaLabel: "Itálico",
  formatStrikeAriaLabel: "Riscado",
  formatUnderlineAriaLabel: "Sublinhado",
  formatListAriaLabel: "Lista",
  formatOrderedListAriaLabel: "Lista numerada",
  formatCodeAriaLabel: "Código",
  formatQuoteAriaLabel: "Citação",
  formatLinkAriaLabel: "Link",
  formatAlignLeftAriaLabel: "Alinhar à esquerda",
  formatAlignCenterAriaLabel: "Centralizar",
  formatAlignRightAriaLabel: "Alinhar à direita",
  formatAlignJustifyAriaLabel: "Justificar",
  formatFontSizeAriaLabel: "Tamanho da fonte",
  formatFontSizeDecreaseAriaLabel: "Diminuir fonte",
  formatFontSizeIncreaseAriaLabel: "Aumentar fonte",
  formatUndoAriaLabel: "Desfazer",
  formatRedoAriaLabel: "Refazer",
  formatEmojiAriaLabel: "Emoji",
  emojiMenuAriaLabel: "Inserir emoji",
};

const IMAGE_ACCEPT = "image/png,image/jpeg,image/jpg,image/webp,image/gif,.png,.jpg,.jpeg,.webp,.gif";
const MAX_INLINE_IMAGES = 10;
const MAX_IMAGE_BYTES = 20 * 1024 * 1024;

type PendingAttachment = {
  id: string;
  file: File;
  kind: "clip" | "inline";
};

function toThreadItems(
  comments: RequestComment[],
  avatarByUserId: ReadonlyMap<string, string>,
): MessageThreadItem[] {
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

function isImageFile(file: File): boolean {
  const type = (file.type || "").toLowerCase();
  if (type.startsWith("image/")) return true;
  const name = file.name.toLowerCase();
  return /\.(png|jpe?g|webp|gif)$/.test(name);
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
  const [pending, setPending] = useState<PendingAttachment[]>([]);
  const [attachmentSrcById, setAttachmentSrcById] = useState<Map<string, string>>(
    () => new Map(),
  );
  const msgsRef = useRef<HTMLDivElement | null>(null);
  const stickToBottomRef = useRef(true);
  const inlineFilesRef = useRef<Record<string, File>>({});

  const [pendingSrcById, setPendingSrcById] = useState<Map<string, string>>(
    () => new Map(),
  );

  const authorIds = useMemo(
    () => items.map((row) => row.author_user_id),
    [items],
  );
  const avatarByUserId = useParticipantAvatarUrls(authorIds);

  useEffect(() => {
    const next = new Map<string, string>();
    const created: string[] = [];
    for (const row of pending) {
      if (row.kind !== "inline") continue;
      const url = URL.createObjectURL(row.file);
      created.push(url);
      next.set(row.id, url);
    }
    setPendingSrcById(next);
    return () => {
      for (const url of created) URL.revokeObjectURL(url);
    };
  }, [pending]);

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

  useEffect(() => {
    const ac = new AbortController();
    const created: string[] = [];
    void (async () => {
      const next = new Map<string, string>();
      for (const comment of items) {
        const ids = listInlineAttachmentIdsFromMarkdown(comment.body || "");
        if (!ids.length) continue;
        await Promise.all(
          ids.map(async (attachmentId) => {
            if (next.has(attachmentId)) return;
            try {
              const blob = await downloadCommentAttachmentBlob(
                requestId,
                comment.id,
                attachmentId,
                { signal: ac.signal },
              );
              if (ac.signal.aborted) return;
              const url = URL.createObjectURL(blob);
              created.push(url);
              next.set(attachmentId, url);
            } catch {
              /* missing */
            }
          }),
        );
      }
      if (ac.signal.aborted) {
        for (const url of created) URL.revokeObjectURL(url);
        return;
      }
      setAttachmentSrcById((prev) => {
        for (const url of prev.values()) URL.revokeObjectURL(url);
        return next;
      });
    })();
    return () => {
      ac.abort();
      for (const url of created) URL.revokeObjectURL(url);
    };
  }, [items, requestId]);

  const threadItems = useMemo(
    () => toThreadItems(items, avatarByUserId),
    [items, avatarByUserId],
  );

  useEffect(() => {
    const el = msgsRef.current;
    if (!el || !stickToBottomRef.current) return;
    el.scrollTop = el.scrollHeight;
  }, [threadItems, refreshKey]);

  const resolveAttachmentImageSrc = useCallback(
    (attachmentId: string) => {
      const id = (attachmentId || "").trim();
      if (!id) return null;
      return (
        attachmentSrcById.get(id) ||
        pendingSrcById.get(id) ||
        null
      );
    },
    [attachmentSrcById, pendingSrcById],
  );

  const onInlineImagesInserted = useCallback(
    (inserts: readonly { pendingId: string; file: File }[]) => {
      setPending((prev) => {
        const next = [...prev];
        for (const item of inserts) {
          if (!isImageFile(item.file)) continue;
          if (item.file.size > MAX_IMAGE_BYTES) continue;
          inlineFilesRef.current[item.pendingId] = item.file;
          if (next.some((row) => row.id === item.pendingId)) continue;
          next.push({ id: item.pendingId, file: item.file, kind: "inline" });
        }
        return next.slice(0, MAX_INLINE_IMAGES);
      });
    },
    [],
  );

  const onInlineImageRemoved = useCallback((pendingId: string) => {
    delete inlineFilesRef.current[pendingId];
    setPending((prev) => prev.filter((row) => row.id !== pendingId));
  }, []);

  const onFilesSelected = useCallback((files: File[]) => {
    setPending((prev) => {
      const next = [...prev];
      for (const file of files) {
        if (!isImageFile(file)) continue;
        if (file.size > MAX_IMAGE_BYTES) continue;
        const id = crypto.randomUUID();
        next.push({ id, file, kind: "clip" });
      }
      return next.slice(0, MAX_INLINE_IMAGES);
    });
  }, []);

  const onRemovePending = useCallback((id: string) => {
    delete inlineFilesRef.current[id];
    setPending((prev) => prev.filter((row) => row.id !== id));
  }, []);

  async function onSend(markdown: string) {
    const text = markdown.trim();
    if (!canComment || busy) return;
    if (!text && pending.length === 0) return;
    setBusy(true);
    setError(null);
    try {
      let bodyText = text || " ";
      const created = await createComment(requestId, bodyText);
      const pendingIds = listInlinePendingIdsFromMarkdown(bodyText);
      const pendingToUuid: Record<string, string> = {};
      for (const pendingId of pendingIds) {
        const file = inlineFilesRef.current[pendingId];
        if (!file) continue;
        const uploaded = await uploadCommentAttachment(
          requestId,
          created.id,
          file,
        );
        pendingToUuid[pendingId] = uploaded.id;
      }
      for (const row of pending.filter((item) => item.kind === "clip")) {
        await uploadCommentAttachment(requestId, created.id, row.file);
      }
      if (Object.keys(pendingToUuid).length) {
        bodyText = rewriteInlinePendingInMarkdown(bodyText, pendingToUuid);
        await patchComment(requestId, created.id, bodyText);
      }
      setDraft("");
      setPending([]);
      inlineFilesRef.current = {};
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
                    showAttach
                    fileAccept={IMAGE_ACCEPT}
                    pendingAttachments={pending}
                    onFilesSelected={onFilesSelected}
                    onRemovePendingAttachment={onRemovePending}
                    onInlineImagesInserted={onInlineImagesInserted}
                    onInlineImageRemoved={onInlineImageRemoved}
                    onInlineAttachmentRemoved={onInlineImageRemoved}
                    resolveAttachmentImageSrc={resolveAttachmentImageSrc}
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
                resolveAttachmentImageSrc={resolveAttachmentImageSrc}
              />
            </MyRequestsRoomConversationChatColumn>
          </MyRequestsRoomPanel>
        </div>
      </div>
    </MyRequestsSectionCard>
  );
}
