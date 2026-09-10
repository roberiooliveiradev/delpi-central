import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ActionButton,
  listInlineAttachmentIdsFromMarkdown,
  listInlinePendingIdsFromMarkdown,
  rewriteInlinePendingInMarkdown,
} from "@delpi/plugin-ui/index";

import {
  createComment,
  downloadCommentAttachmentBlob,
  listCommentAttachments,
  listComments,
  patchComment,
  uploadCommentAttachment,
  type CommentAttachmentMeta,
} from "../api/requestsApi";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { commentTimeLabel } from "../content/presentationLabels";
import { useParticipantAvatarUrls } from "../hooks/useParticipantAvatarUrls";
import type { RequestComment } from "../types/requests";
import {
  MR_PORTAL_SCOPE,
  MyRequestsAttachmentPreviewStrip,
  MyRequestsMentionComposer,
  MyRequestsMessageThread,
  MyRequestsRoomConversationChatColumn,
  MyRequestsRoomPanel,
  MyRequestsSectionCard,
  MyRequestsStateBanner,
  type MessageThreadAction,
  type MessageThreadItem,
} from "../ui/mrUi";
import { appendAttachmentMarkdown } from "../utils/commentAttachmentMarkdown";
import { formatBytes } from "../utils/formatBytes";
import { shouldStickThreadToBottom } from "../utils/threadStickToBottom";
import {
  RequestFilePreviewModal,
  type RequestFilePreviewTarget,
} from "./RequestFilePreviewModal";

type CommentsPanelProps = {
  requestId: string;
  canComment?: boolean;
  /** Terminal request — conversation read-only for everyone. */
  conversationFrozen?: boolean;
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

const EDIT_COMPOSER_LABELS = {
  ...COMPOSER_LABELS,
  placeholder: "Editar mensagem…",
  sendAriaLabel: "Salvar edição",
};

const IMAGE_ACCEPT =
  "image/png,image/jpeg,image/jpg,image/webp,image/gif,.png,.jpg,.jpeg,.webp,.gif";
const MAX_INLINE_IMAGES = 10;
const MAX_IMAGE_BYTES = 20 * 1024 * 1024;

type PendingLocal = {
  kind: "clip" | "inline";
  id: string;
  file: File;
};

type PendingRemote = {
  kind: "remote";
  id: string;
  commentId: string;
  fileName: string;
  contentType: string | null;
  sizeBytes: number | null;
  previewUrl: string | null;
};

type PendingAttachment = PendingLocal | PendingRemote;

type AttachmentIndexEntry = CommentAttachmentMeta & { comment_id: string };

function isImageFile(file: File): boolean {
  const type = (file.type || "").toLowerCase();
  if (type.startsWith("image/")) return true;
  const name = file.name.toLowerCase();
  return /\.(png|jpe?g|webp|gif)$/.test(name);
}

function isImageMeta(item: CommentAttachmentMeta): boolean {
  const ct = (item.mime_type || "").toLowerCase();
  if (ct.startsWith("image/")) return true;
  return /\.(png|jpe?g|webp|gif)$/i.test(item.original_name || "");
}

/** Conversation UI over RequestComment — kit MessageThread + MentionComposer. */
export function CommentsPanel({
  requestId,
  canComment = false,
  conversationFrozen = false,
  refreshKey = 0,
}: CommentsPanelProps) {
  const [items, setItems] = useState<RequestComment[]>([]);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [pending, setPending] = useState<PendingAttachment[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [attachmentSrcById, setAttachmentSrcById] = useState<Map<string, string>>(
    () => new Map(),
  );
  const [attachmentsByCommentId, setAttachmentsByCommentId] = useState<
    Map<string, CommentAttachmentMeta[]>
  >(() => new Map());
  const [preview, setPreview] = useState<RequestFilePreviewTarget>(null);
  const msgsRef = useRef<HTMLDivElement | null>(null);
  const stickToBottomRef = useRef(true);
  const inlineFilesRef = useRef<Record<string, File>>({});
  const attachmentIndexRef = useRef<Map<string, AttachmentIndexEntry>>(new Map());

  const [pendingSrcById, setPendingSrcById] = useState<Map<string, string>>(
    () => new Map(),
  );

  const isEditing = Boolean(editingId);
  const authorIds = useMemo(
    () => items.map((row) => row.author_user_id),
    [items],
  );
  const avatarByUserId = useParticipantAvatarUrls(authorIds);

  useEffect(() => {
    const next = new Map<string, string>();
    const created: string[] = [];
    for (const row of pending) {
      if (row.kind === "remote") {
        if (row.previewUrl) next.set(row.id, row.previewUrl);
        continue;
      }
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
    if (!canComment || conversationFrozen) {
      setEditingId(null);
      setDraft("");
      setPending([]);
      inlineFilesRef.current = {};
    }
  }, [canComment, conversationFrozen]);

  useEffect(() => {
    const ac = new AbortController();
    const created: string[] = [];
    void (async () => {
      const nextSrc = new Map<string, string>();
      const nextByComment = new Map<string, CommentAttachmentMeta[]>();
      const index = new Map<string, AttachmentIndexEntry>();

      for (const comment of items) {
        let metas: CommentAttachmentMeta[] = [];
        try {
          metas = await listCommentAttachments(requestId, comment.id, {
            signal: ac.signal,
          });
        } catch {
          metas = [];
        }
        if (ac.signal.aborted) return;
        nextByComment.set(comment.id, metas);
        for (const meta of metas) {
          index.set(meta.id, { ...meta, comment_id: comment.id });
        }

        const inlineIds = listInlineAttachmentIdsFromMarkdown(comment.body || "");
        const toLoad = new Set([
          ...inlineIds,
          ...metas.filter(isImageMeta).map((item) => item.id),
        ]);
        await Promise.all(
          [...toLoad].map(async (attachmentId) => {
            if (nextSrc.has(attachmentId)) return;
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
              nextSrc.set(attachmentId, url);
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
      attachmentIndexRef.current = index;
      setAttachmentsByCommentId(nextByComment);
      setAttachmentSrcById((prev) => {
        for (const url of prev.values()) URL.revokeObjectURL(url);
        return nextSrc;
      });
    })();
    return () => {
      ac.abort();
      for (const url of created) URL.revokeObjectURL(url);
    };
  }, [items, requestId]);

  const openAttachmentPreview = useCallback(
    (attachmentId: string, commentId?: string) => {
      const id = (attachmentId || "").trim();
      if (!id) return;
      const indexed = attachmentIndexRef.current.get(id);
      const resolvedCommentId = (commentId || indexed?.comment_id || "").trim();
      if (!resolvedCommentId) return;
      setPreview({
        kind: "comment_attachment",
        requestId,
        commentId: resolvedCommentId,
        id,
        fileName: indexed?.original_name || "imagem",
        contentType: indexed?.mime_type ?? null,
        byteSize: indexed?.size_bytes ?? null,
      });
    },
    [requestId],
  );

  const threadItems = useMemo((): MessageThreadItem[] => {
    const chronological = [...items].reverse();
    return chronological.map((item) => {
      const authorId = (item.author_user_id || "").trim();
      const attachments = attachmentsByCommentId.get(item.id) || [];
      const inlineIds = new Set(listInlineAttachmentIdsFromMarkdown(item.body || ""));
      return {
        id: item.id,
        kind: "text",
        bodyText: item.body,
        createdAtLabel: commentTimeLabel(item.created_at, item.updated_at),
        authorName: item.author_name || "Usuário",
        authorUserId: authorId || null,
        authorSrc: authorId ? avatarByUserId.get(authorId) || null : null,
        mine: Boolean(item.is_mine),
        belowBody:
          attachments.length > 0 ? (
            <div className="my-requests-comment-attachments">
              <MyRequestsAttachmentPreviewStrip
                mode="preview"
                items={attachments.map((row) => ({
                  id: row.id,
                  fileName: row.original_name,
                  contentType: row.mime_type,
                  // Inline images already render in the markdown body — keep the
                  // strip as name + real size (and click-to-enlarge) without a
                  // second large thumb.
                  previewUrl: inlineIds.has(row.id)
                    ? null
                    : attachmentSrcById.get(row.id) || null,
                  detail: formatBytes(row.size_bytes),
                }))}
                onOpen={(row) => openAttachmentPreview(row.id, item.id)}
              />
            </div>
          ) : undefined,
      };
    });
  }, [
    items,
    avatarByUserId,
    attachmentsByCommentId,
    attachmentSrcById,
    openAttachmentPreview,
  ]);

  useEffect(() => {
    const el = msgsRef.current;
    if (!el || !stickToBottomRef.current) return;
    el.scrollTop = el.scrollHeight;
  }, [threadItems, refreshKey]);

  const resolveAttachmentImageSrc = useCallback(
    (attachmentId: string) => {
      const id = (attachmentId || "").trim();
      if (!id) return null;
      return attachmentSrcById.get(id) || pendingSrcById.get(id) || null;
    },
    [attachmentSrcById, pendingSrcById],
  );

  const composerPending = useMemo(
    () =>
      pending.map((item) => {
        if (item.kind === "remote") {
          return {
            id: item.id,
            fileName: item.fileName,
            contentType: item.contentType,
            previewUrl: item.previewUrl,
            detail: formatBytes(item.sizeBytes),
          };
        }
        return {
          id: item.id,
          fileName: item.file.name,
          contentType: item.file.type || null,
          file: item.file,
          detail: formatBytes(item.file.size),
          kind: item.kind,
        };
      }),
    [pending],
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
    setPending((prev) => prev.filter((item) => item.id !== id));
  }, []);

  const cancelEdit = useCallback(() => {
    setEditingId(null);
    setDraft("");
    setPending([]);
    inlineFilesRef.current = {};
  }, []);

  const beginEdit = useCallback(
    (messageId: string) => {
      const row = items.find((item) => item.id === messageId);
      if (!row || !canComment) return;
      const body = row.body || "";
      const inlineIds = new Set(listInlineAttachmentIdsFromMarkdown(body));
      const metas = attachmentsByCommentId.get(row.id) || [];
      const remotes: PendingRemote[] = [];
      for (const meta of metas) {
        if (inlineIds.has(meta.id)) continue;
        remotes.push({
          kind: "remote",
          id: meta.id,
          commentId: row.id,
          fileName: meta.original_name,
          contentType: meta.mime_type,
          sizeBytes: meta.size_bytes,
          previewUrl: attachmentSrcById.get(meta.id) || null,
        });
      }
      inlineFilesRef.current = {};
      setEditingId(messageId);
      setDraft(body);
      setPending(remotes);
      stickToBottomRef.current = true;
    },
    [items, canComment, attachmentsByCommentId, attachmentSrcById],
  );

  const resolveActions = useCallback(
    (message: MessageThreadItem): MessageThreadAction[] => {
      if (!canComment || conversationFrozen || !message.mine) return [];
      if (editingId) return [];
      return [
        {
          id: "edit",
          label: "Editar",
          onClick: () => beginEdit(message.id),
        },
      ];
    },
    [canComment, conversationFrozen, editingId, beginEdit],
  );

  async function applyUploadsAndBody(
    commentId: string,
    markdown: string,
  ): Promise<string> {
    let bodyText = markdown.trim() || " ";
    const pendingIds = listInlinePendingIdsFromMarkdown(bodyText);
    const pendingToUuid: Record<string, string> = {};
    for (const pendingId of pendingIds) {
      const file = inlineFilesRef.current[pendingId];
      if (!file) continue;
      const uploaded = await uploadCommentAttachment(requestId, commentId, file);
      pendingToUuid[pendingId] = uploaded.id;
    }
    const clipUploaded: Array<{ id: string; fileName: string }> = [];
    for (const row of pending.filter((item): item is PendingLocal => item.kind === "clip")) {
      const uploaded = await uploadCommentAttachment(
        requestId,
        commentId,
        row.file,
      );
      clipUploaded.push({ id: uploaded.id, fileName: row.file.name });
    }
    if (Object.keys(pendingToUuid).length) {
      bodyText = rewriteInlinePendingInMarkdown(bodyText, pendingToUuid);
    }
    if (clipUploaded.length) {
      bodyText = appendAttachmentMarkdown(
        bodyText === " " ? "" : bodyText,
        clipUploaded,
      );
    }
    return bodyText.trim() || " ";
  }

  async function onSend(markdown: string) {
    const text = markdown.trim();
    if (!canComment || busy) return;
    if (!text && pending.length === 0) return;
    setBusy(true);
    setError(null);
    try {
      if (editingId) {
        const finalBody = await applyUploadsAndBody(editingId, text || " ");
        // Re-append remotes still in tray that are not already in body.
        let bodyWithRemotes = finalBody;
        const present = new Set(listInlineAttachmentIdsFromMarkdown(bodyWithRemotes));
        const remotesToKeep = pending.filter(
          (item): item is PendingRemote => item.kind === "remote",
        );
        bodyWithRemotes = appendAttachmentMarkdown(
          bodyWithRemotes === " " ? "" : bodyWithRemotes,
          remotesToKeep
            .filter((item) => !present.has(item.id))
            .map((item) => ({ id: item.id, fileName: item.fileName })),
        );
        await patchComment(requestId, editingId, bodyWithRemotes.trim() || " ", {
          markAsEdited: true,
        });
        cancelEdit();
      } else {
        let bodyText = text || " ";
        const created = await createComment(requestId, bodyText);
        bodyText = await applyUploadsAndBody(created.id, bodyText);
        const needsPatch =
          bodyText !== (text || " ") ||
          pending.some((item) => item.kind === "clip" || item.kind === "inline");
        if (needsPatch) {
          await patchComment(requestId, created.id, bodyText, {
            markAsEdited: false,
          });
        }
        setDraft("");
        setPending([]);
        inlineFilesRef.current = {};
      }
      stickToBottomRef.current = true;
      await reload();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : isEditing
            ? "Falha ao editar mensagem"
            : "Falha ao enviar mensagem",
      );
    } finally {
      setBusy(false);
    }
  }

  const dockMessage = conversationFrozen
    ? "Esta solicitação foi finalizada. A conversa está somente leitura."
    : "Você pode ler a conversa, mas não tem permissão para enviar mensagens neste momento.";

  return (
    <MyRequestsSectionCard
      title="Conversa sobre a solicitação"
      hint={MY_REQUESTS_HELP_TOOLTIPS.comments.section}
    >
      <div className="my-requests-detail-conversation" data-help="comments">
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
                  <div className="my-requests-comment-composer">
                    {isEditing ? (
                      <div className="my-requests-comment-composer__edit-bar">
                        <p className="my-requests-comment-composer__edit-label">
                          Editando mensagem
                        </p>
                        <ActionButton
                          type="button"
                          variant="ghost"
                          disabled={busy}
                          onClick={cancelEdit}
                        >
                          Cancelar
                        </ActionButton>
                      </div>
                    ) : null}
                    <MyRequestsMentionComposer
                      value={draft}
                      onChange={setDraft}
                      onSubmit={(md) => void onSend(md)}
                      disabled={busy}
                      submitting={busy}
                      showAttach
                      fileAccept={IMAGE_ACCEPT}
                      pendingAttachments={composerPending}
                      onFilesSelected={onFilesSelected}
                      onRemovePendingAttachment={onRemovePending}
                      onInlineImagesInserted={onInlineImagesInserted}
                      onInlineImageRemoved={onInlineImageRemoved}
                      onInlineAttachmentRemoved={onInlineImageRemoved}
                      resolveAttachmentImageSrc={resolveAttachmentImageSrc}
                      portalScopeClassName={MR_PORTAL_SCOPE}
                      labels={isEditing ? EDIT_COMPOSER_LABELS : COMPOSER_LABELS}
                    />
                  </div>
                ) : (
                  <MyRequestsStateBanner>{dockMessage}</MyRequestsStateBanner>
                )
              }
            >
              <MyRequestsMessageThread
                messages={threadItems}
                listAriaLabel="Mensagens da solicitação"
                emptyLabel="Nenhuma mensagem ainda. Inicie a conversa."
                portalScopeClassName={MR_PORTAL_SCOPE}
                resolveAttachmentImageSrc={resolveAttachmentImageSrc}
                onAttachmentImageClick={(attachmentId) =>
                  openAttachmentPreview(attachmentId)
                }
                resolveActions={resolveActions}
              />
            </MyRequestsRoomConversationChatColumn>
          </MyRequestsRoomPanel>
        </div>
      </div>

      <RequestFilePreviewModal
        open={Boolean(preview)}
        target={preview}
        onClose={() => setPreview(null)}
      />
    </MyRequestsSectionCard>
  );
}
