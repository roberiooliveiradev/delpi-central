import { useCallback, useEffect, useMemo, useState } from "react";

import {
  postInteractionMessage,
  updateInteractionMessage,
  uploadRoomMessageAttachment,
  type InteractionMessageDto,
} from "../../api/interactionRoomsApi";
import {
  CM_PORTAL_SCOPE,
  CommercialActionButton,
  CommercialMentionComposer,
} from "../../app/commercialUi";
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
import type { InteractionMentionHit } from "./mentionSuggestAdapter";
import { useInteractionMentionSuggest } from "./useInteractionMentionSuggest";

export const ROOM_ATTACH_ACCEPT =
  ".pdf,.png,.jpg,.jpeg,.webp,.gif,.txt,.doc,.docx,.xls,.xlsx,application/pdf,image/*,text/plain";

type PendingFile = {
  id: string;
  file: File;
};

type Props = {
  roomId: string;
  disabled?: boolean;
  /** compose (default) = POST + anexos; edit = PATCH body/mentions in-place. */
  mode?: "compose" | "edit";
  editMessageId?: string | null;
  initialMarkdown?: string;
  /** Existing mentions when opening edit (so PATCH does not wipe them). */
  initialMentions?: readonly {
    kind: string;
    ref: Record<string, unknown>;
    label: string;
  }[];
  onMessageCreated: (message: InteractionMessageDto) => void;
  onMessageUpdated?: (message: InteractionMessageDto) => void;
  /** After POST uploads finish (success or partial failure). */
  onMessageAttachmentsSettled?: (messageId: string) => void;
  onCancelEdit?: () => void;
  onError: (message: string) => void;
  onAddFilesReady?: (addFiles: (files: File[]) => void) => void;
};

/**
 * Composer da sala: MentionComposer + anexos (owner_type=room_message após POST).
 * Rascunho (texto + arquivos) sobrevive a F5 por roomId no modo compose.
 * Modo edit: PATCH body + replace de mentions; sem anexos nesta S*.
 */
export function InteractionRoomMessageComposer({
  roomId,
  disabled = false,
  mode = "compose",
  editMessageId = null,
  initialMarkdown = "",
  initialMentions = [],
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
  const [pending, setPending] = useState<PendingFile[]>([]);
  const [draftHydrated, setDraftHydrated] = useState(isEdit);
  const [submitting, setSubmitting] = useState(false);
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

  const pendingAttachments = useMemo(
    () =>
      pending.map((item) => ({
        id: item.id,
        fileName: item.file.name,
        contentType: item.file.type || null,
        file: item.file,
        detail: `${Math.max(1, Math.round(item.file.size / 1024))} KB`,
      })),
    [pending],
  );

  useEffect(() => {
    if (isEdit) {
      setDraft(initialMarkdown);
      setPending([]);
      setDraftHydrated(true);
      seedMentions(
        initialMentions.map((mention) => ({
          kind: mention.kind,
          ref: { ...mention.ref },
          label: mention.label,
        })),
      );
      return;
    }
    let cancelled = false;
    setDraft(readComposerDraftText(roomId));
    setPending([]);
    setDraftHydrated(false);
    resetMentions();
    void readComposerDraftFiles(roomId).then((files) => {
      if (cancelled) return;
      setPending(files);
      setDraftHydrated(true);
    });
    return () => {
      cancelled = true;
    };
    // Seed mentions only when opening/switching the edited message — not on every parent re-render.
    // eslint-disable-next-line react-hooks/exhaustive-deps -- initialMentions snapshot on editMessageId
  }, [roomId, isEdit, editMessageId, initialMarkdown, resetMentions, seedMentions]);

  useEffect(() => {
    if (isEdit || !draftHydrated) return;
    writeComposerDraftText(roomId, draft);
  }, [roomId, draft, draftHydrated, isEdit]);

  useEffect(() => {
    if (isEdit || !draftHydrated) return;
    void writeComposerDraftFiles(roomId, pending);
  }, [roomId, pending, draftHydrated, isEdit]);

  const onFilesSelected = useCallback(
    (files: File[]) => {
      if (isEdit || !files.length) return;
      const gated = gatePendingAttachments(pending.length, files);
      if (!gated.ok) {
        onError(gated.message);
        return;
      }
      setPending((prev) => [
        ...prev,
        ...gated.files.map((file) => ({
          id: `pending-${file.name}-${file.size}-${file.lastModified}-${Math.random().toString(36).slice(2, 8)}`,
          file,
        })),
      ]);
    },
    [pending.length, onError, isEdit],
  );

  useEffect(() => {
    if (isEdit) return;
    onAddFilesReady?.(onFilesSelected);
  }, [onAddFilesReady, onFilesSelected, isEdit]);

  const onSubmit = useCallback(async (bodyMarkdown?: string) => {
    const id = roomId.trim();
    const body = (bodyMarkdown ?? draft).trim();
    if (!id || submitting || disabled) return;

    if (isEdit && editMessageId) {
      if (!body) return;
      setSubmitting(true);
      try {
        if (interactionMessageLooksLikeRawHtml(body)) {
          onError(content.bodyHtmlRejected);
          return;
        }
        const mentions = takeMentionsForBody(body);
        const updated = await updateInteractionMessage(id, editMessageId, {
          body_text: body,
          mentions,
        });
        resetMentions();
        onMessageUpdated?.(updated);
        onCancelEdit?.();
      } catch (err: unknown) {
        onError(err instanceof Error ? err.message : content.roomUpdateError);
      } finally {
        setSubmitting(false);
      }
      return;
    }

    if (!body && pending.length === 0) return;

    setSubmitting(true);
    try {
      const bodyText = body || content.attachmentOnlyBody;
      if (interactionMessageLooksLikeRawHtml(bodyText)) {
        onError(content.bodyHtmlRejected);
        return;
      }
      const mentions = takeMentionsForBody(bodyText);
      const created = await postInteractionMessage(id, {
        body_text: bodyText,
        mentions,
      });
      const files = [...pending];
      setDraft("");
      setPending([]);
      resetMentions();
      void clearComposerDraft(id);
      onMessageCreated(created);

      for (const item of files) {
        try {
          await uploadRoomMessageAttachment(created.id, item.file);
        } catch (err: unknown) {
          onError(
            err instanceof Error ? err.message : content.attachUploadError,
          );
        }
      }
      if (files.length > 0) {
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
    content.attachmentOnlyBody,
    content.attachUploadError,
    content.bodyHtmlRejected,
    content.roomSendError,
    content.roomUpdateError,
    takeMentionsForBody,
    resetMentions,
    onMessageCreated,
    onMessageUpdated,
    onMessageAttachmentsSettled,
    onCancelEdit,
    onError,
  ]);

  return (
    <div>
      {isEdit && onCancelEdit ? (
        <div className="cm-room-thread__edit-cancel">
          <CommercialActionButton
            type="button"
            variant="ghost"
            onClick={onCancelEdit}
            disabled={submitting}
          >
            {content.editCancelLabel}
          </CommercialActionButton>
        </div>
      ) : null}
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
        showAttach={!isEdit}
        onFilesSelected={isEdit ? undefined : onFilesSelected}
        fileAccept={ROOM_ATTACH_ACCEPT}
        pendingAttachments={isEdit ? [] : pendingAttachments}
        onRemovePendingAttachment={
          isEdit
            ? undefined
            : (id) => {
                setPending((prev) => prev.filter((row) => row.id !== id));
              }
        }
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
        }}
      />
    </div>
  );
}
