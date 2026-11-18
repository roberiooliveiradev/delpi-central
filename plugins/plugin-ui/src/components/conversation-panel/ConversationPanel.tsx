/** ConversationPanel — conversa governada compartilhada (PRC, Issue #207).
 *
 * Mesma experiência do painel de comentários do My Requests, desacoplada
 * de bounded context: o consumidor injeta um `ConversationApi` tipado e
 * um resolvedor de avatar opcional. Autorização é sempre backend — o
 * painel apenas reflete `canComment`/`conversationFrozen` informados.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { Maximize2, Minimize2 } from "lucide-react";

import { ActionButton } from "../actions/ActionButton";
import { IconButton } from "../actions/IconButton";
import { createHostContainedModalShell } from "../feedback/ModalShell";
import { createDashboardAttachmentPreviewStrip } from "../forms/AttachmentPreviewStrip";
import { attachmentPreviewStripBemClasses } from "../forms/AttachmentPreviewStrip";
import { createDashboardMessageThread } from "../collaboration/MessageThread";
import type {
  MessageThreadAction,
  MessageThreadItem,
} from "../collaboration/MessageThread";
import { createDashboardMentionComposer } from "../collaboration/MentionComposer";
import { createDashboardRoomConversationShell } from "../collaboration/RoomConversationShell";
import { createDashboardSectionCard } from "../layout/SectionCard";
import { sectionCardPacBemClasses } from "../layout/SectionCard";
import { createDashboardStateBanner } from "../feedback/StateBanner";
import { stateBannerBemClasses } from "../feedback/StateBanner";
import { FilePreviewModal } from "../preview/FilePreviewModal";
import {
  listInlineAttachmentIdsFromMarkdown,
  listInlinePendingIdsFromMarkdown,
  rewriteInlinePendingInMarkdown,
} from "../rich-text/index";

const PANEL_PREFIX = "delpi-ui";

const PanelSectionCard = createDashboardSectionCard({
  classNames: sectionCardPacBemClasses(PANEL_PREFIX),
  labels: { titleHelpAriaLabel: (title) => `Ajuda: ${title}` },
});
const PanelStateBanner = createDashboardStateBanner({
  classNames: stateBannerBemClasses(PANEL_PREFIX),
});
const PanelAttachmentPreviewStrip = createDashboardAttachmentPreviewStrip({
  classNames: attachmentPreviewStripBemClasses(PANEL_PREFIX),
  labels: {
    empty: "Nenhum arquivo.",
    openAriaLabel: (fileName) => `Abrir ${fileName}`,
    removeAriaLabel: (fileName) => `Remover ${fileName}`,
  },
});
const PanelMessageThread = createDashboardMessageThread(PANEL_PREFIX);
const PanelMentionComposer = createDashboardMentionComposer(PANEL_PREFIX);
const roomShell = createDashboardRoomConversationShell(PANEL_PREFIX);
const PanelRoomConversationChatColumn = roomShell.ChatColumn;
const PanelRoomPanel = roomShell.Panel;

// ---------------------------------------------------------------------
// Contrato neutro — o adapter do MFE traduz o envelope da sua API.
// ---------------------------------------------------------------------

export type ConversationComment = {
  id: string;
  requestId: string;
  authorId: string | null;
  authorName: string;
  body: string;
  version: number | null;
  isMine: boolean;
  createdAt: string;
  updatedAt: string | null;
  edited: boolean;
};

export type ConversationAttachment = {
  id: string;
  fileName: string;
  mediaType: string | null;
  sizeBytes: number | null;
  /** P1: PENDING_SCAN/AVAILABLE/REJECTED/QUARANTINED/DELETED. */
  state?: string | null;
};

export type ConversationAttachmentFile = {
  file: File;
  /** Referência do lado do cliente (ex.: `pending:{id}` inline)
   * — ecoada no resultado para mapear o id persistido. */
  clientRef?: string | null;
};

export type ConversationCreateResult = {
  comment: ConversationComment;
  attachments: (ConversationAttachment & {
    clientRef?: string | null;
  })[];
};

export type ConversationApi = {
  listComments(
    requestId: string,
    opts?: { signal?: AbortSignal },
  ): Promise<ConversationComment[]>;
  createComment(
    requestId: string,
    body: string,
    opts?: { idempotencyKey?: string },
  ): Promise<ConversationComment>;
  /** FIX-03 — criação composta numa só operação: texto, anexos ou
   * ambos. O backend valida tudo antes de persistir (sem corpo
   * artificial nem comentário órfão). */
  createCommentWithAttachments(
    requestId: string,
    input: { body: string; files: ConversationAttachmentFile[] },
    opts?: { idempotencyKey?: string },
  ): Promise<ConversationCreateResult>;
  updateComment(
    requestId: string,
    commentId: string,
    body: string,
    opts?: { expectedVersion?: number | null },
  ): Promise<ConversationComment>;
  listAttachments(
    requestId: string,
    commentId: string,
    opts?: { signal?: AbortSignal },
  ): Promise<ConversationAttachment[]>;
  uploadAttachment(
    requestId: string,
    commentId: string,
    file: File,
  ): Promise<ConversationAttachment>;
  downloadAttachment(
    requestId: string,
    commentId: string,
    attachmentId: string,
    opts?: { signal?: AbortSignal },
  ): Promise<Blob>;
  deleteAttachment(
    requestId: string,
    commentId: string,
    attachmentId: string,
  ): Promise<void>;
};

export type ConversationPanelProps = {
  requestId: string;
  api: ConversationApi;
  canComment?: boolean;
  /** Caso terminal — conversa somente leitura para todos. */
  conversationFrozen?: boolean;
  refreshKey?: number;
  /** Resolvedor de avatar governado do MFE; ausente → iniciais. */
  loadAvatar?: (
    userId: string,
    signal: AbortSignal,
  ) => Promise<Blob | null>;
  portalScopeClassName?: string;
  sectionTitle?: string;
  sectionHint?: string;
  fileAccept?: string;
  maxFileBytes?: number;
  /**
   * Opt-in: botão «Expandir» no header da seção — abre a MESMA conversa
   * em modal contido no host do MFE (`createHostContainedModalShell` +
   * `fill`), sem cobrir a sidebar do portal. O painel não remonta:
   * rascunho, anexos pendentes e edição em andamento são preservados.
   */
  expandable?: boolean;
  /** Linha contextual no cabeçalho do modal (ex.: `Solicitação PRC · A1B2C3D4`). */
  expandDialogDescription?: string;
};

const COMPOSER_LABELS = {
  placeholder: "Escreva uma mensagem sobre a solicitação…",
  sendAriaLabel: "Enviar mensagem",
  attachAriaLabel: "Anexar arquivo",
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

const DEFAULT_ACCEPT =
  "image/png,image/jpeg,image/jpg,image/webp,application/pdf,.png,.jpg,.jpeg,.webp,.pdf";
const MAX_INLINE_IMAGES = 10;

function formatBytes(size: number | null | undefined): string | null {
  if (!size || size <= 0) return null;
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function timeLabel(createdAt: string, _updatedAt: string | null, edited: boolean): string {
  const base = new Date(createdAt);
  const label = Number.isNaN(base.getTime())
    ? ""
    : base.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
  return edited ? `${label} · editado` : label;
}

function stickToBottom(el: HTMLElement): boolean {
  return el.scrollHeight - el.scrollTop - el.clientHeight < 48;
}

function isImageFile(file: File): boolean {
  const type = (file.type || "").toLowerCase();
  if (type.startsWith("image/")) return true;
  return /\.(png|jpe?g|webp|gif)$/i.test(file.name);
}

function isImageMeta(item: ConversationAttachment): boolean {
  const ct = (item.mediaType || "").toLowerCase();
  if (ct.startsWith("image/")) return true;
  return /\.(png|jpe?g|webp|gif)$/i.test(item.fileName || "");
}

function attachmentAvailable(item: ConversationAttachment): boolean {
  return !item.state || item.state === "AVAILABLE";
}

type PendingLocal = { kind: "clip" | "inline"; id: string; file: File };
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
type AttachmentIndexEntry = ConversationAttachment & { commentId: string };
type PreviewTarget = {
  commentId: string;
  attachmentId: string;
  fileName: string;
  contentType: string | null;
  byteSize: number | null;
} | null;

export function ConversationPanel({
  requestId,
  api,
  canComment = false,
  conversationFrozen = false,
  refreshKey = 0,
  loadAvatar,
  portalScopeClassName,
  sectionTitle = "Conversa sobre a solicitação",
  sectionHint,
  fileAccept = DEFAULT_ACCEPT,
  maxFileBytes = 10 * 1024 * 1024,
  expandable = false,
  expandDialogDescription,
}: ConversationPanelProps) {
  const [items, setItems] = useState<ConversationComment[]>([]);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [pending, setPending] = useState<PendingAttachment[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [attachmentSrcById, setAttachmentSrcById] = useState<Map<string, string>>(
    () => new Map(),
  );
  const [attachmentsByCommentId, setAttachmentsByCommentId] = useState<
    Map<string, ConversationAttachment[]>
  >(() => new Map());
  const [preview, setPreview] = useState<PreviewTarget>(null);
  const [avatarByUserId, setAvatarByUserId] = useState<Map<string, string>>(
    () => new Map(),
  );
  const msgsRef = useRef<HTMLDivElement | null>(null);
  const stickToBottomRef = useRef(true);
  const inlineFilesRef = useRef<Record<string, File>>({});
  const attachmentIndexRef = useRef<Map<string, AttachmentIndexEntry>>(new Map());
  const baselineRemoteIdsRef = useRef<string[]>([]);
  const [pendingSrcById, setPendingSrcById] = useState<Map<string, string>>(
    () => new Map(),
  );
  const [expanded, setExpanded] = useState(false);
  const expandTriggerWrapRef = useRef<HTMLSpanElement | null>(null);

  /* Modal host-contained (`fill`) — instância estável por portalScope;
   * o diálogo portala para o root do MFE e não cobre a sidebar. */
  const ExpandedModal = useMemo(
    () =>
      expandable && portalScopeClassName
        ? createHostContainedModalShell({
            prefix: "delpi-ui-conversation-panel",
            portalScopeClassName,
            containedLayout: "fill",
          })
        : null,
    [expandable, portalScopeClassName],
  );

  /* Submodal (preview de anexo) absorve o Escape: o ModalShell escuta
   * `document` e não empilha — sem este guard, um Escape no preview
   * recolheria a conversa expandida junto. */
  const collapseExpanded = useCallback(() => {
    if (preview) return;
    setExpanded(false);
    requestAnimationFrame(() => {
      expandTriggerWrapRef.current?.querySelector("button")?.focus();
    });
  }, [preview]);

  /* A thread remonta ao trocar de superfície; reancora no rodapé quando
   * o usuário já acompanhava as últimas mensagens. */
  useEffect(() => {
    if (!expanded) return;
    const raf = requestAnimationFrame(() => {
      const el = msgsRef.current;
      if (el && stickToBottomRef.current) el.scrollTop = el.scrollHeight;
    });
    return () => cancelAnimationFrame(raf);
  }, [expanded]);

  const isEditing = Boolean(editingId);
  const authorIds = useMemo(
    () => items.map((row) => row.authorId),
    [items],
  );

  // Avatar governado — best-effort; falha/404 → iniciais do kit.
  const authorKey = useMemo(() => {
    const unique = [
      ...new Set(authorIds.map((id) => (id ?? "").trim()).filter(Boolean)),
    ].sort();
    return unique.join("|");
  }, [authorIds]);

  useEffect(() => {
    if (!loadAvatar || !authorKey) {
      setAvatarByUserId(new Map());
      return;
    }
    const ids = authorKey.split("|");
    const controller = new AbortController();
    const created: string[] = [];
    void (async () => {
      const next = new Map<string, string>();
      await Promise.all(
        ids.map(async (uid) => {
          try {
            const blob = await loadAvatar(uid, controller.signal);
            if (!blob || controller.signal.aborted) return;
            const url = URL.createObjectURL(blob);
            created.push(url);
            next.set(uid, url);
          } catch {
            /* sem foto / abort */
          }
        }),
      );
      if (controller.signal.aborted) {
        for (const url of created) URL.revokeObjectURL(url);
        return;
      }
      setAvatarByUserId(next);
    })();
    return () => {
      controller.abort();
      for (const url of created) URL.revokeObjectURL(url);
    };
  }, [authorKey, loadAvatar]);

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

  const reload = useCallback(
    async (signal?: AbortSignal) => {
      const data = await api.listComments(requestId, { signal });
      setItems(data || []);
    },
    [api, requestId],
  );

  useEffect(() => {
    const ac = new AbortController();
    reload(ac.signal).catch((err: Error) => {
      if (err.name !== "AbortError") setError(err.message);
    });
    return () => ac.abort();
  }, [reload, refreshKey]);

  useEffect(() => {
    if (!canComment || conversationFrozen) {
      setEditingId(null);
      setDraft("");
      setPending([]);
      inlineFilesRef.current = {};
      baselineRemoteIdsRef.current = [];
    }
  }, [canComment, conversationFrozen]);

  useEffect(() => {
    const ac = new AbortController();
    const created: string[] = [];
    void (async () => {
      const nextSrc = new Map<string, string>();
      const nextByComment = new Map<string, ConversationAttachment[]>();
      const index = new Map<string, AttachmentIndexEntry>();

      for (const comment of items) {
        let metas: ConversationAttachment[] = [];
        try {
          metas = await api.listAttachments(requestId, comment.id, {
            signal: ac.signal,
          });
        } catch {
          metas = [];
        }
        if (ac.signal.aborted) return;
        nextByComment.set(comment.id, metas);
        for (const meta of metas) {
          index.set(meta.id, { ...meta, commentId: comment.id });
        }

        const inlineIds = listInlineAttachmentIdsFromMarkdown(comment.body || "");
        const toLoad = new Set([
          ...inlineIds,
          ...metas.filter((m) => isImageMeta(m) && attachmentAvailable(m)).map((m) => m.id),
        ]);
        await Promise.all(
          [...toLoad].map(async (attachmentId) => {
            if (nextSrc.has(attachmentId)) return;
            try {
              const blob = await api.downloadAttachment(
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
              /* indisponível */
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
  }, [items, api, requestId]);

  const openAttachmentPreview = useCallback(
    (attachmentId: string, commentId?: string) => {
      const id = (attachmentId || "").trim();
      if (!id) return;
      const indexed = attachmentIndexRef.current.get(id);
      const resolvedCommentId = (commentId || indexed?.commentId || "").trim();
      if (!resolvedCommentId || !indexed || !attachmentAvailable(indexed)) return;
      setPreview({
        commentId: resolvedCommentId,
        attachmentId: id,
        fileName: indexed?.fileName || "arquivo",
        contentType: indexed?.mediaType ?? null,
        byteSize: indexed?.sizeBytes ?? null,
      });
    },
    [],
  );

  const threadItems = useMemo((): MessageThreadItem[] => {
    /* P3-FIX-02 — contrato oficial: `created_at ASC, id ASC`. A
     * normalização é explícita e única aqui (o adapter passa a ordem
     * do backend); nunca agrupar por autor/isMine. */
    const chronological = [...items].sort((a, b) => {
      const byTime = String(a.createdAt).localeCompare(String(b.createdAt));
      return byTime !== 0 ? byTime : String(a.id).localeCompare(String(b.id));
    });
    return chronological.map((item) => {
      const authorId = (item.authorId || "").trim();
      const attachments = attachmentsByCommentId.get(item.id) || [];
      const inlineIds = new Set(listInlineAttachmentIdsFromMarkdown(item.body || ""));
      const stripAttachments = attachments.filter((row) => !inlineIds.has(row.id));
      return {
        id: item.id,
        kind: "text",
        bodyText: item.body,
        createdAtLabel: timeLabel(item.createdAt, item.updatedAt, item.edited),
        authorName: item.authorName || "Usuário",
        authorUserId: authorId || null,
        authorSrc: authorId ? avatarByUserId.get(authorId) || null : null,
        mine: Boolean(item.isMine),
        belowBody:
          stripAttachments.length > 0 ? (
            <div className="delpi-ui-conversation-panel__attachments">
              <PanelAttachmentPreviewStrip
                mode="preview"
                items={stripAttachments.map((row) => ({
                  id: row.id,
                  fileName: row.fileName,
                  contentType: row.mediaType,
                  previewUrl: attachmentSrcById.get(row.id) || null,
                  detail:
                    (attachmentAvailable(row)
                      ? formatBytes(row.sizeBytes)
                      : "Em análise") ?? undefined,
                }))}
                onOpen={(row: { id: string }) =>
                  openAttachmentPreview(row.id, item.id)
                }
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
      pending
        .filter((item) => item.kind !== "inline")
        .map((item) => {
          if (item.kind === "remote") {
            return {
              id: item.id,
              fileName: item.fileName,
              contentType: item.contentType,
              previewUrl: item.previewUrl,
              detail: formatBytes(item.sizeBytes) ?? undefined,
            };
          }
          return {
            id: item.id,
            fileName: item.file.name,
            contentType: item.file.type || null,
            file: item.file,
            detail: formatBytes(item.file.size) ?? undefined,
          };
        }),
    [pending],
  );

  const onInlineImagesInserted = useCallback(
    (inserts: readonly { pendingId: string; file: File }[]) => {
      setPending((prev) => {
        const next = [...prev];
        for (const item of inserts) {
          if (!isImageFile(item.file)) {
            setError("Só é possível colar imagens (PNG, JPEG ou WebP).");
            continue;
          }
          if (item.file.size > maxFileBytes) {
            setError("A imagem colada excede o limite de 10 MB.");
            continue;
          }
          inlineFilesRef.current[item.pendingId] = item.file;
          if (next.some((row) => row.id === item.pendingId)) continue;
          next.push({ id: item.pendingId, file: item.file, kind: "inline" });
        }
        return next.slice(0, MAX_INLINE_IMAGES);
      });
    },
    [maxFileBytes],
  );

  const onInlineImageRemoved = useCallback((pendingId: string) => {
    delete inlineFilesRef.current[pendingId];
    setPending((prev) => prev.filter((row) => row.id !== pendingId));
  }, []);

  const onFilesSelected = useCallback(
    (files: File[]) => {
      setPending((prev) => {
        const next = [...prev];
        let rejected = false;
        for (const file of files) {
          const isPdf =
            file.type === "application/pdf" ||
            /\.pdf$/i.test(file.name);
          if (!isImageFile(file) && !isPdf) {
            rejected = true;
            continue;
          }
          if (file.size > maxFileBytes) {
            rejected = true;
            continue;
          }
          next.push({ id: crypto.randomUUID(), file, kind: "clip" });
        }
        setError(
          rejected
            ? "Anexos aceitos: PDF ou imagem (PNG, JPEG, WebP), máx. 10 MB."
            : null,
        );
        return next.slice(0, MAX_INLINE_IMAGES);
      });
    },
    [maxFileBytes],
  );

  const onRemovePending = useCallback((id: string) => {
    delete inlineFilesRef.current[id];
    setPending((prev) => prev.filter((item) => item.id !== id));
  }, []);

  const cancelEdit = useCallback(() => {
    setEditingId(null);
    setDraft("");
    setPending([]);
    inlineFilesRef.current = {};
    baselineRemoteIdsRef.current = [];
  }, []);

  const beginEdit = useCallback(
    (messageId: string) => {
      const row = items.find((item) => item.id === messageId);
      if (!row || !canComment) return;
      const body = row.body || "";
      const inlineIds = new Set(listInlineAttachmentIdsFromMarkdown(body));
      const metas = attachmentsByCommentId.get(row.id) || [];
      const remotes: PendingRemote[] = [];
      const allRemoteIds: string[] = [];
      for (const meta of metas) {
        allRemoteIds.push(meta.id);
        if (inlineIds.has(meta.id)) continue;
        remotes.push({
          kind: "remote",
          id: meta.id,
          commentId: row.id,
          fileName: meta.fileName,
          contentType: meta.mediaType,
          sizeBytes: meta.sizeBytes,
          previewUrl: attachmentSrcById.get(meta.id) || null,
        });
      }
      inlineFilesRef.current = {};
      baselineRemoteIdsRef.current = allRemoteIds;
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
        { id: "edit", label: "Editar", onClick: () => beginEdit(message.id) },
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
      if (!file) {
        throw new Error(
          "Uma imagem colada não pôde ser enviada. Remova-a e cole novamente.",
        );
      }
      const uploaded = await api.uploadAttachment(requestId, commentId, file);
      pendingToUuid[pendingId] = uploaded.id;
    }
    for (const row of pending.filter(
      (item): item is PendingLocal => item.kind === "clip",
    )) {
      await api.uploadAttachment(requestId, commentId, row.file);
    }
    if (Object.keys(pendingToUuid).length) {
      bodyText = rewriteInlinePendingInMarkdown(bodyText, pendingToUuid);
    }
    if (listInlinePendingIdsFromMarkdown(bodyText).length > 0) {
      throw new Error(
        "Uma imagem colada não pôde ser enviada. Remova-a e cole novamente.",
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
        const editing = items.find((row) => row.id === editingId);
        const finalBody = await applyUploadsAndBody(editingId, text || " ");
        const remotesKept = pending.filter(
          (item): item is PendingRemote => item.kind === "remote",
        );
        const keptIds = new Set([
          ...remotesKept.map((item) => item.id),
          ...listInlineAttachmentIdsFromMarkdown(finalBody),
        ]);
        const toDelete = baselineRemoteIdsRef.current.filter(
          (remoteId) => !keptIds.has(remoteId),
        );
        for (const attachmentId of toDelete) {
          await api.deleteAttachment(requestId, editingId, attachmentId);
        }
        await api.updateComment(requestId, editingId, finalBody.trim() || " ", {
          expectedVersion: editing?.version ?? null,
        });
        cancelEdit();
      } else {
        // FIX-03 — criação composta: texto, anexos ou ambos numa só
        // chamada. Nunca corpo artificial (" ") — o backend aplica a
        // invariante texto OU >=1 anexo válido.
        const inlinePendingIds = listInlinePendingIdsFromMarkdown(text);
        if (
          inlinePendingIds.some((id) => !inlineFilesRef.current[id])
        ) {
          throw new Error(
            "Uma imagem colada não pôde ser enviada. Remova-a e cole novamente.",
          );
        }
        const files: ConversationAttachmentFile[] = [
          ...pending
            .filter((item): item is PendingLocal => item.kind === "clip")
            .map((item) => ({ file: item.file })),
          ...inlinePendingIds.map((pendingId) => ({
            file: inlineFilesRef.current[pendingId] as File,
            clientRef: pendingId,
          })),
        ];
        if (files.length === 0) {
          await api.createComment(requestId, text, {
            idempotencyKey: crypto.randomUUID(),
          });
        } else {
          const created = await api.createCommentWithAttachments(
            requestId,
            { body: text, files },
            { idempotencyKey: crypto.randomUUID() },
          );
          const refToUuid: Record<string, string> = {};
          for (const att of created.attachments || []) {
            if (att.clientRef) refToUuid[att.clientRef] = att.id;
          }
          if (Object.keys(refToUuid).length) {
            const rewritten = rewriteInlinePendingInMarkdown(
              text,
              refToUuid,
            );
            if (rewritten !== text) {
              await api.updateComment(
                requestId,
                created.comment.id,
                rewritten,
                { expectedVersion: created.comment.version },
              );
            }
          }
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

  const conversationSurface = (isExpanded: boolean) => (
    <div
      className={
        isExpanded
          ? "delpi-ui-conversation-panel delpi-ui-conversation-panel--expanded"
          : "delpi-ui-conversation-panel"
      }
    >
        {error ? (
          <PanelStateBanner variant="error">{error}</PanelStateBanner>
        ) : null}

        <div className="delpi-ui-conversation-panel__frame">
          <PanelRoomPanel aria-label={sectionTitle}>
            <PanelRoomConversationChatColumn
              msgsRef={msgsRef}
              onMsgsScroll={(event) => {
                stickToBottomRef.current = stickToBottom(event.currentTarget);
              }}
              dock={
                canComment ? (
                  <div className="delpi-ui-conversation-panel__composer">
                    {isEditing ? (
                      <div className="delpi-ui-conversation-panel__edit-bar">
                        <p className="delpi-ui-conversation-panel__edit-label">
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
                    <PanelMentionComposer
                      value={draft}
                      onChange={setDraft}
                      onSubmit={(md) => void onSend(md)}
                      disabled={busy}
                      submitting={busy}
                      showAttach
                      fileAccept={fileAccept}
                      pendingAttachments={composerPending}
                      onFilesSelected={onFilesSelected}
                      onRemovePendingAttachment={onRemovePending}
                      onInlineImagesInserted={onInlineImagesInserted}
                      onInlineImageRemoved={onInlineImageRemoved}
                      onInlineAttachmentRemoved={onInlineImageRemoved}
                      resolveAttachmentImageSrc={resolveAttachmentImageSrc}
                      portalScopeClassName={portalScopeClassName}
                      labels={isEditing ? EDIT_COMPOSER_LABELS : COMPOSER_LABELS}
                    />
                  </div>
                ) : (
                  <PanelStateBanner>{dockMessage}</PanelStateBanner>
                )
              }
            >
              <PanelMessageThread
                messages={threadItems}
                showMineIdentity
                listAriaLabel="Mensagens da solicitação"
                emptyLabel="Nenhuma mensagem ainda. Inicie a conversa."
                portalScopeClassName={portalScopeClassName}
                resolveAttachmentImageSrc={resolveAttachmentImageSrc}
                onAttachmentImageClick={(attachmentId) =>
                  openAttachmentPreview(attachmentId)
                }
                resolveActions={resolveActions}
              />
            </PanelRoomConversationChatColumn>
          </PanelRoomPanel>
        </div>
    </div>
  );

  return (
    <PanelSectionCard
      title={sectionTitle}
      hint={sectionHint}
      actions={
        ExpandedModal ? (
          <span ref={expandTriggerWrapRef}>
            <IconButton
              aria-label="Expandir conversa"
              disabled={expanded}
              onClick={() => setExpanded(true)}
            >
              <Maximize2 size={16} aria-hidden="true" />
            </IconButton>
          </span>
        ) : undefined
      }
    >
      {expanded ? (
        <div
          className="delpi-ui-conversation-panel delpi-ui-conversation-panel--placeholder"
          aria-hidden="true"
        >
          <p className="delpi-ui-conversation-panel__placeholder-text">
            Conversa aberta no modo expandido.
          </p>
        </div>
      ) : (
        conversationSurface(false)
      )}

      {expanded && ExpandedModal ? (
        <ExpandedModal
          open
          title={sectionTitle}
          description={expandDialogDescription}
          onClose={collapseExpanded}
          closeAriaLabel="Recolher conversa"
          initialFocusSelector=".delpi-ui-conversation-panel--expanded [contenteditable='true']"
          headerActions={
            <ActionButton
              type="button"
              variant="ghost"
              aria-label="Recolher conversa"
              onClick={collapseExpanded}
            >
              <Minimize2 size={15} aria-hidden="true" /> Recolher
            </ActionButton>
          }
        >
          {conversationSurface(true)}
        </ExpandedModal>
      ) : null}

      <FilePreviewModal
        open={Boolean(preview)}
        title={preview?.fileName || "Pré-visualização"}
        source={
          preview
            ? () =>
                api.downloadAttachment(
                  requestId,
                  preview.commentId,
                  preview.attachmentId,
                )
            : null
        }
        mimeType={preview?.contentType ?? null}
        fileName={preview?.fileName ?? null}
        metaItems={[
          preview?.contentType || null,
          formatBytes(preview?.byteSize ?? null),
        ]}
        portalScopeClassName={portalScopeClassName}
        onClose={() => setPreview(null)}
      />
    </PanelSectionCard>
  );
}
