import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  deleteRoomMessageAttachment,
  downloadRoomMessageAttachmentBlob,
  listRoomMessageAttachments,
  postInteractionMessage,
  updateInteractionMessage,
  uploadRoomMessageAttachment,
  type InteractionMessageDto,
} from "../../api/interactionRoomsApi";
import { CommercialMentionComposer, CM_PORTAL_SCOPE } from "../../app/commercialUi";
import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";
import {
  clearComposerDraft,
  readComposerDraftFiles,
  readComposerDraftText,
  writeComposerDraftFiles,
  writeComposerDraftText,
} from "./interactionRoomComposerDraftStorage";
import {
  gatePendingAttachments,
  interactionMessageLooksLikeRawHtml,
} from "./interactionMessageAttachmentGate";
import {
  countFilesTowardAttachmentCap,
  listInlineAttachmentIdsFromMarkdown,
  listInlinePendingIdsFromMarkdown,
  rewriteInlinePendingInMarkdown,
} from "./interactionRoomInlineAttachments";
import type { InteractionMentionHit } from "./mentionSuggestAdapter";
import { useInteractionMentionSuggest } from "./useInteractionMentionSuggest";

export const ROOM_ATTACH_ACCEPT =
  ".pdf,.png,.jpg,.jpeg,.webp,.gif,.txt,.doc,.docx,.xls,.xlsx,application/pdf,image/*,text/plain";

type PendingLocal = {
  kind: "local";
  id: string;
  file: File;
};

type PendingRemote = {
  kind: "remote";
  id: string;
  fileName: string;
  contentType: string | null;
  byteSize: number;
  previewUrl: string | null;
};

type PendingItem = PendingLocal | PendingRemote;

function formatBytes(value: number): string {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function isImageAttachment(fileName: string, contentType: string | null): boolean {
  const ct = (contentType || "").toLowerCase();
  if (ct.startsWith("image/")) return true;
  return /\.(png|jpe?g|webp|gif|bmp|svg)$/i.test(fileName || "");
}

type Props = {
  roomId: string;
  disabled?: boolean;
  /** compose (default) = POST; edit = PATCH body/mentions + sync anexos no dock. */
  mode?: "compose" | "edit";
  editMessageId?: string | null;
  initialMarkdown?: string;
  /** Existing mentions when opening edit (so PATCH does not wipe them). */
  initialMentions?: readonly {
    kind: string;
    ref: Record<string, unknown>;
    label: string;
  }[];
  /** When set (compose mode), POST includes parent_id. */
  replyToMessageId?: string | null;
  replyBanner?: { label: string; preview?: string } | null;
  onCancelReply?: () => void;
  /** Banner do modo edit (reusa faixa replyTo do kit). */
  editBanner?: { label: string; preview?: string } | null;
  onMessageCreated: (message: InteractionMessageDto) => void;
  onMessageUpdated?: (message: InteractionMessageDto) => void;
  /** After POST/PATCH attachment sync finishes. */
  onMessageAttachmentsSettled?: (messageId: string) => void;
  onCancelEdit?: () => void;
  onError: (message: string) => void;
  onAddFilesReady?: (addFiles: (files: File[]) => void) => void;
};

/**
 * Composer da sala no dock: compose + edição completa (texto e anexos).
 * Ao entrar em edit, limpa rascunho local e carrega body + anexos da mensagem.
 */
export function InteractionRoomMessageComposer({
  roomId,
  disabled = false,
  mode = "compose",
  editMessageId = null,
  initialMarkdown = "",
  initialMentions = [],
  replyToMessageId = null,
  replyBanner = null,
  onCancelReply,
  editBanner = null,
  onMessageCreated,
  onMessageUpdated,
  onMessageAttachmentsSettled,
  onCancelEdit,
  onError,
  onAddFilesReady,
}: Props) {
  const content = INTERACTION_ROOMS_CONTENT;
  const isEdit = mode === "edit" && Boolean(editMessageId);
  const [draft, setDraft] = useState(() =>
    isEdit ? initialMarkdown : readComposerDraftText(roomId),
  );
  const [pending, setPending] = useState<PendingItem[]>([]);
  const [inlineFiles, setInlineFiles] = useState<Record<string, File>>({});
  const [inlineThumbUrls, setInlineThumbUrls] = useState<Record<string, string>>({});
  const [draftHydrated, setDraftHydrated] = useState(isEdit);
  const [submitting, setSubmitting] = useState(false);
  const [baselineRemoteIds, setBaselineRemoteIds] = useState<string[]>([]);
  const previewUrlsRef = useRef<string[]>([]);
  const {
    hits,
    onMentionQueryChange,
    onMentionInserted,
    takeMentionsForBody,
    resetMentions,
    seedMentions,
  } = useInteractionMentionSuggest();

  const hitsById = useMemo(() => {
    const map = new Map<string, InteractionMentionHit>();
    for (const hit of hits) map.set(hit.id, hit);
    return map;
  }, [hits]);

  const revokePreviewUrls = useCallback(() => {
    for (const url of previewUrlsRef.current) {
      URL.revokeObjectURL(url);
    }
    previewUrlsRef.current = [];
    setInlineThumbUrls({});
  }, []);

  const pendingAttachments = useMemo(
    () =>
      pending.map((item) => {
        if (item.kind === "local") {
          return {
            id: item.id,
            fileName: item.file.name,
            contentType: item.file.type || null,
            file: item.file,
            detail: formatBytes(item.file.size),
          };
        }
        return {
          id: item.id,
          fileName: item.fileName,
          contentType: item.contentType,
          previewUrl: item.previewUrl,
          detail: formatBytes(item.byteSize),
        };
      }),
    [pending],
  );

  useEffect(() => {
    let cancelled = false;

    const loadEdit = async () => {
      const messageId = (editMessageId || "").trim();
      if (!isEdit || !messageId) return;

      // Limpa o que havia no input (texto/anexos de compose).
      void clearComposerDraft(roomId);
      revokePreviewUrls();
      setDraft(initialMarkdown);
      setPending([]);
      setInlineFiles({});
      setBaselineRemoteIds([]);
      setDraftHydrated(false);
      seedMentions(
        initialMentions.map((mention) => ({
          kind: mention.kind,
          ref: { ...mention.ref },
          label: mention.label,
        })),
      );

      try {
        const items = await listRoomMessageAttachments(messageId);
        if (cancelled) return;
        const inlineIds = new Set(listInlineAttachmentIdsFromMarkdown(initialMarkdown));
        const remotes: PendingRemote[] = [];
        const inlineThumbs: Record<string, string> = {};
        const createdUrls: string[] = [];
        const allRemoteIds: string[] = [];
        for (const item of items) {
          allRemoteIds.push(item.id);
          let previewUrl: string | null = null;
          if (isImageAttachment(item.file_name, item.content_type)) {
            try {
              const blob = await downloadRoomMessageAttachmentBlob(item.id);
              if (cancelled) {
                for (const url of createdUrls) URL.revokeObjectURL(url);
                return;
              }
              previewUrl = URL.createObjectURL(blob);
              createdUrls.push(previewUrl);
            } catch {
              /* thumb opcional */
            }
          }
          if (inlineIds.has(item.id)) {
            if (previewUrl) inlineThumbs[item.id] = previewUrl;
            continue;
          }
          remotes.push({
            kind: "remote",
            id: item.id,
            fileName: item.file_name,
            contentType: item.content_type || null,
            byteSize: item.byte_size,
            previewUrl,
          });
        }
        if (cancelled) {
          for (const url of createdUrls) URL.revokeObjectURL(url);
          return;
        }
        previewUrlsRef.current = createdUrls;
        setInlineThumbUrls(inlineThumbs);
        setPending(remotes);
        setBaselineRemoteIds(allRemoteIds);
        setDraftHydrated(true);
      } catch (err: unknown) {
        if (cancelled) return;
        setDraftHydrated(true);
        onError(
          err instanceof Error ? err.message : content.attachUploadError,
        );
      }
    };

    if (isEdit) {
      void loadEdit();
      return () => {
        cancelled = true;
      };
    }

    revokePreviewUrls();
    setDraft(readComposerDraftText(roomId));
    setPending([]);
    setInlineFiles({});
    setBaselineRemoteIds([]);
    setDraftHydrated(false);
    resetMentions();
    void readComposerDraftFiles(roomId).then((files) => {
      if (cancelled) return;
      setPending(
        files.map((item) => ({
          kind: "local" as const,
          id: item.id,
          file: item.file,
        })),
      );
      setDraftHydrated(true);
    });
    return () => {
      cancelled = true;
    };
    // Seed mentions / anexos só ao abrir/trocar a mensagem editada.
    // eslint-disable-next-line react-hooks/exhaustive-deps -- initialMentions snapshot on editMessageId
  }, [roomId, isEdit, editMessageId, initialMarkdown, resetMentions, seedMentions, revokePreviewUrls]);

  useEffect(() => {
    return () => {
      revokePreviewUrls();
    };
  }, [revokePreviewUrls]);

  useEffect(() => {
    if (isEdit || !draftHydrated) return;
    writeComposerDraftText(roomId, draft);
  }, [roomId, draft, draftHydrated, isEdit]);

  useEffect(() => {
    if (isEdit || !draftHydrated) return;
    const locals = pending.filter((item): item is PendingLocal => item.kind === "local");
    void writeComposerDraftFiles(
      roomId,
      locals.map((item) => ({ id: item.id, file: item.file })),
    );
  }, [roomId, pending, draftHydrated, isEdit]);

  const onFilesSelected = useCallback(
    (files: File[]) => {
      if (!files.length) return;
      const current = countFilesTowardAttachmentCap(
        pending.length,
        Object.keys(inlineFiles).length,
      );
      const gated = gatePendingAttachments(current, files);
      if (!gated.ok) {
        onError(gated.message);
        return;
      }
      setPending((prev) => [
        ...prev,
        ...gated.files.map((file) => ({
          kind: "local" as const,
          id: `pending-${file.name}-${file.size}-${file.lastModified}-${Math.random().toString(36).slice(2, 8)}`,
          file,
        })),
      ]);
    },
    [pending.length, inlineFiles, onError],
  );

  const onInlineImagesInserted = useCallback(
    (items: readonly { pendingId: string; file: File }[]) => {
      if (!items.length) return;
      const current = countFilesTowardAttachmentCap(
        pending.length,
        Object.keys(inlineFiles).length,
      );
      const gated = gatePendingAttachments(
        current,
        items.map((item) => item.file),
      );
      if (!gated.ok) {
        onError(gated.message);
        return;
      }
      setInlineFiles((prev) => {
        const next = { ...prev };
        for (const item of items) {
          next[item.pendingId] = item.file;
        }
        return next;
      });
    },
    [pending.length, inlineFiles, onError],
  );

  const onInlineImageRemoved = useCallback((pendingId: string) => {
    setInlineFiles((prev) => {
      if (!(pendingId in prev)) return prev;
      const next = { ...prev };
      delete next[pendingId];
      return next;
    });
  }, []);

  const onInlineAttachmentRemoved = useCallback((attachmentId: string) => {
    setInlineThumbUrls((prev) => {
      const url = prev[attachmentId];
      if (!url) return prev;
      URL.revokeObjectURL(url);
      previewUrlsRef.current = previewUrlsRef.current.filter((item) => item !== url);
      const next = { ...prev };
      delete next[attachmentId];
      return next;
    });
  }, []);

  const resolveAttachmentImageSrc = useCallback(
    (attachmentId: string) => inlineThumbUrls[attachmentId] ?? null,
    [inlineThumbUrls],
  );

  useEffect(() => {
    onAddFilesReady?.(onFilesSelected);
  }, [onAddFilesReady, onFilesSelected]);

  const onRemovePending = useCallback((id: string) => {
    setPending((prev) => {
      const next: PendingItem[] = [];
      for (const item of prev) {
        if (item.id !== id) {
          next.push(item);
          continue;
        }
        if (item.kind === "remote" && item.previewUrl) {
          URL.revokeObjectURL(item.previewUrl);
          previewUrlsRef.current = previewUrlsRef.current.filter(
            (url) => url !== item.previewUrl,
          );
        }
      }
      return next;
    });
  }, []);

  const onCancelEditClick = useCallback(() => {
    revokePreviewUrls();
    setPending([]);
    setInlineFiles({});
    setBaselineRemoteIds([]);
    setDraft("");
    resetMentions();
    onCancelEdit?.();
  }, [onCancelEdit, resetMentions, revokePreviewUrls]);

  const uploadInlineAndRewrite = useCallback(
    async (messageId: string, bodyText: string): Promise<string> => {
      const pendingIds = listInlinePendingIdsFromMarkdown(bodyText);
      if (pendingIds.length === 0) return bodyText;
      const pendingToUuid: Record<string, string> = {};
      for (const pendingId of pendingIds) {
        const file = inlineFiles[pendingId];
        if (!file) {
          throw new Error(content.bodyInlineImageMissing);
        }
        const uploaded = await uploadRoomMessageAttachment(messageId, file);
        pendingToUuid[pendingId] = uploaded.id;
      }
      const rewritten = rewriteInlinePendingInMarkdown(bodyText, pendingToUuid);
      if (listInlinePendingIdsFromMarkdown(rewritten).length > 0) {
        throw new Error(content.bodyInlineImageRewriteFailed);
      }
      return rewritten;
    },
    [
      inlineFiles,
      content.bodyInlineImageMissing,
      content.bodyInlineImageRewriteFailed,
    ],
  );

  const onSubmit = useCallback(async (bodyMarkdown?: string) => {
    const id = roomId.trim();
    const body = (bodyMarkdown ?? draft).trim();
    if (!id || submitting || disabled) return;

    if (isEdit && editMessageId) {
      const remotesKept = pending.filter(
        (item): item is PendingRemote => item.kind === "remote",
      );
      const locals = pending.filter(
        (item): item is PendingLocal => item.kind === "local",
      );
      const inlinePending = listInlinePendingIdsFromMarkdown(body);
      if (!body && remotesKept.length === 0 && locals.length === 0) return;

      setSubmitting(true);
      try {
        if (body && interactionMessageLooksLikeRawHtml(body)) {
          onError(content.bodyHtmlRejected);
          return;
        }
        let bodyText = body;
        if (inlinePending.length > 0) {
          bodyText = await uploadInlineAndRewrite(editMessageId, bodyText);
        }
        const mentions = takeMentionsForBody(bodyText);
        const updated = await updateInteractionMessage(id, editMessageId, {
          body_text: bodyText,
          mentions,
        });

        const keptIds = new Set([
          ...remotesKept.map((item) => item.id),
          ...listInlineAttachmentIdsFromMarkdown(bodyText),
        ]);
        const toDelete = baselineRemoteIds.filter((remoteId) => !keptIds.has(remoteId));
        for (const attachmentId of toDelete) {
          try {
            await deleteRoomMessageAttachment(attachmentId);
          } catch (err: unknown) {
            onError(
              err instanceof Error ? err.message : content.attachUploadError,
            );
          }
        }
        for (const item of locals) {
          try {
            await uploadRoomMessageAttachment(editMessageId, item.file);
          } catch (err: unknown) {
            onError(
              err instanceof Error ? err.message : content.attachUploadError,
            );
          }
        }

        revokePreviewUrls();
        setPending([]);
        setInlineFiles({});
        setBaselineRemoteIds([]);
        setDraft("");
        resetMentions();
        onMessageUpdated?.(updated);
        onMessageAttachmentsSettled?.(editMessageId);
        onCancelEdit?.();
      } catch (err: unknown) {
        onError(err instanceof Error ? err.message : content.roomUpdateError);
      } finally {
        setSubmitting(false);
      }
      return;
    }

    const inlinePending = listInlinePendingIdsFromMarkdown(body);
    if (!body && pending.length === 0) return;

    setSubmitting(true);
    try {
      let bodyText = body;
      if (bodyText && interactionMessageLooksLikeRawHtml(bodyText)) {
        onError(content.bodyHtmlRejected);
        return;
      }
      const mentions = takeMentionsForBody(bodyText);
      const created = await postInteractionMessage(id, {
        body_text: bodyText,
        mentions,
        parent_id: replyToMessageId?.trim() || null,
      });
      const files = pending.filter(
        (item): item is PendingLocal => item.kind === "local",
      );

      if (inlinePending.length > 0) {
        bodyText = await uploadInlineAndRewrite(created.id, bodyText);
        const rewritten = await updateInteractionMessage(id, created.id, {
          body_text: bodyText,
          mentions: takeMentionsForBody(bodyText),
        });
        onMessageCreated(rewritten);
      } else {
        onMessageCreated(created);
      }

      setDraft("");
      setPending([]);
      setInlineFiles({});
      resetMentions();
      void clearComposerDraft(id);
      onCancelReply?.();

      for (const item of files) {
        try {
          await uploadRoomMessageAttachment(created.id, item.file);
        } catch (err: unknown) {
          onError(
            err instanceof Error ? err.message : content.attachUploadError,
          );
        }
      }
      if (files.length > 0 || inlinePending.length > 0) {
        onMessageAttachmentsSettled?.(created.id);
      }
    } catch (err: unknown) {
      onError(err instanceof Error ? err.message : content.roomSendError);
    } finally {
      setSubmitting(false);
    }
  }, [
    roomId,
    draft,
    pending,
    submitting,
    disabled,
    isEdit,
    editMessageId,
    baselineRemoteIds,
    replyToMessageId,
    content.attachUploadError,
    content.bodyHtmlRejected,
    content.roomSendError,
    content.roomUpdateError,
    takeMentionsForBody,
    resetMentions,
    onMessageCreated,
    onMessageUpdated,
    onMessageAttachmentsSettled,
    onCancelReply,
    onCancelEdit,
    onError,
    revokePreviewUrls,
    uploadInlineAndRewrite,
  ]);

  const banner = isEdit ? editBanner : replyBanner;
  const onCancelBanner = isEdit ? onCancelEditClick : onCancelReply;

  return (
    <div>
      <CommercialMentionComposer
        value={draft}
        onChange={setDraft}
        onSubmit={(body) => {
          void onSubmit(body);
        }}
        submitting={submitting}
        disabled={disabled || submitting}
        portalScopeClassName={CM_PORTAL_SCOPE}
        mentionHits={hits}
        onMentionQueryChange={onMentionQueryChange}
        onMentionInserted={(hit) => {
          const full = hitsById.get(hit.id);
          if (full) onMentionInserted(full);
        }}
        showAttach
        onFilesSelected={onFilesSelected}
        fileAccept={ROOM_ATTACH_ACCEPT}
        onInlineImagesInserted={onInlineImagesInserted}
        onInlineImageRemoved={onInlineImageRemoved}
        onInlineAttachmentRemoved={onInlineAttachmentRemoved}
        resolveAttachmentImageSrc={resolveAttachmentImageSrc}
        pendingAttachments={pendingAttachments}
        onRemovePendingAttachment={onRemovePending}
        replyTo={banner ?? null}
        onCancelReply={onCancelBanner}
        labels={{
          placeholder: content.composerPlaceholder,
          sendAriaLabel: isEdit
            ? content.composerSaveEditAriaLabel
            : content.composerSendAriaLabel,
          attachAriaLabel: content.composerAttachAriaLabel,
          formatToggleAriaLabel: content.formatToggleAriaLabel,
          formatBoldAriaLabel: content.formatBoldAriaLabel,
          formatItalicAriaLabel: content.formatItalicAriaLabel,
          formatStrikeAriaLabel: content.formatStrikeAriaLabel,
          formatUnderlineAriaLabel: content.formatUnderlineAriaLabel,
          formatListAriaLabel: content.formatListAriaLabel,
          formatOrderedListAriaLabel: content.formatOrderedListAriaLabel,
          formatCodeAriaLabel: content.formatCodeAriaLabel,
          formatQuoteAriaLabel: content.formatQuoteAriaLabel,
          formatLinkAriaLabel: content.formatLinkAriaLabel,
          formatAlignLeftAriaLabel: content.formatAlignLeftAriaLabel,
          formatAlignCenterAriaLabel: content.formatAlignCenterAriaLabel,
          formatAlignRightAriaLabel: content.formatAlignRightAriaLabel,
          formatAlignJustifyAriaLabel: content.formatAlignJustifyAriaLabel,
          formatFontSizeAriaLabel: content.formatFontSizeAriaLabel,
          formatFontSizeDecreaseAriaLabel: content.formatFontSizeDecreaseAriaLabel,
          formatFontSizeIncreaseAriaLabel: content.formatFontSizeIncreaseAriaLabel,
          formatUndoAriaLabel: content.formatUndoAriaLabel,
          formatRedoAriaLabel: content.formatRedoAriaLabel,
          formatEmojiAriaLabel: content.formatEmojiAriaLabel,
          emojiMenuAriaLabel: content.emojiMenuAriaLabel,
          mentionListAriaLabel: content.composerMentionListAriaLabel,
          mentionEmptyLabel: content.composerMentionEmptyLabel,
          pendingDocumentsHeading: content.pendingAttachmentsHeading,
          pendingDocumentOpenAriaLabel: (fileName) => `Abrir prévia de ${fileName}`,
          pendingRemoveAriaLabel: (fileName) => `Remover ${fileName}`,
          replyCancelAriaLabel: isEdit
            ? content.editCancelLabel
            : content.replyCancelAriaLabel,
        }}
      />
    </div>
  );
}
