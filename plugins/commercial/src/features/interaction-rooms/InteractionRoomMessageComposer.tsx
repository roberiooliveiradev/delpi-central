import { useCallback, useEffect, useMemo, useState } from "react";

import {
  postInteractionMessage,
  uploadRoomMessageAttachment,
  type InteractionMessageDto,
} from "../../api/interactionRoomsApi";
import {
  CM_PORTAL_SCOPE,
  CommercialAttachmentPreviewStrip,
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
  onMessageCreated: (message: InteractionMessageDto) => void;
  onError: (message: string) => void;
  onAddFilesReady?: (addFiles: (files: File[]) => void) => void;
};

/**
 * Composer da sala: MentionComposer + anexos (owner_type=room_message após POST).
 * Rascunho (texto + arquivos) sobrevive a F5 por roomId.
 */
export function InteractionRoomMessageComposer({
  roomId,
  disabled = false,
  onMessageCreated,
  onError,
  onAddFilesReady,
}: Props) {
  const content = INTERACTION_ROOMS_CONTENT;
  const [draft, setDraft] = useState(() => readComposerDraftText(roomId));
  const [pending, setPending] = useState<PendingFile[]>([]);
  const [draftHydrated, setDraftHydrated] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const {
    hits,
    onMentionQueryChange,
    onMentionInserted,
    takeMentionsForBody,
    resetMentions,
  } = useInteractionMentionSuggest();

  const hitsById = useMemo(() => {
    const map = new Map<string, InteractionMentionHit>();
    for (const hit of hits) map.set(hit.id, hit);
    return map;
  }, [hits]);

  const stripItems = useMemo(
    () =>
      pending.map((item) => ({
        id: item.id,
        fileName: item.file.name,
        contentType: item.file.type || null,
        detail: `${Math.max(1, Math.round(item.file.size / 1024))} KB`,
      })),
    [pending],
  );

  useEffect(() => {
    let cancelled = false;
    setDraft(readComposerDraftText(roomId));
    setPending([]);
    setDraftHydrated(false);
    void readComposerDraftFiles(roomId).then((files) => {
      if (cancelled) return;
      setPending(files);
      setDraftHydrated(true);
    });
    return () => {
      cancelled = true;
    };
  }, [roomId]);

  useEffect(() => {
    if (!draftHydrated) return;
    writeComposerDraftText(roomId, draft);
  }, [roomId, draft, draftHydrated]);

  useEffect(() => {
    if (!draftHydrated) return;
    void writeComposerDraftFiles(roomId, pending);
  }, [roomId, pending, draftHydrated]);

  const onFilesSelected = useCallback((files: File[]) => {
    if (!files.length) return;
    setPending((prev) => [
      ...prev,
      ...files.map((file) => ({
        id: `pending-${file.name}-${file.size}-${file.lastModified}-${Math.random().toString(36).slice(2, 8)}`,
        file,
      })),
    ]);
  }, []);

  useEffect(() => {
    onAddFilesReady?.(onFilesSelected);
  }, [onAddFilesReady, onFilesSelected]);

  const onSubmit = useCallback(async (bodyMarkdown?: string) => {
    const id = roomId.trim();
    const body = (bodyMarkdown ?? draft).trim();
    if (!id || submitting || disabled) return;
    if (!body && pending.length === 0) return;

    setSubmitting(true);
    try {
      const bodyText = body || content.attachmentOnlyBody;
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
    content.attachmentOnlyBody,
    content.attachUploadError,
    content.roomSendError,
    takeMentionsForBody,
    resetMentions,
    onMessageCreated,
    onError,
  ]);

  const footer =
    pending.length > 0 ? (
      <CommercialAttachmentPreviewStrip
        mode="manage"
        heading={content.pendingAttachmentsHeading}
        items={stripItems}
        onOpen={() => undefined}
        onRemove={(item) => {
          setPending((prev) => prev.filter((row) => row.id !== item.id));
        }}
      />
    ) : null;

  return (
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
      hasAttachments={pending.length > 0}
      footer={footer}
      labels={{
        placeholder: content.composerPlaceholder,
        sendAriaLabel: content.composerSendAriaLabel,
        attachAriaLabel: content.composerAttachAriaLabel,
        formatToggleAriaLabel: content.formatToggleAriaLabel,
        formatBoldAriaLabel: content.formatBoldAriaLabel,
        formatItalicAriaLabel: content.formatItalicAriaLabel,
        formatStrikeAriaLabel: content.formatStrikeAriaLabel,
        formatListAriaLabel: content.formatListAriaLabel,
        formatOrderedListAriaLabel: content.formatOrderedListAriaLabel,
        formatCodeAriaLabel: content.formatCodeAriaLabel,
        formatQuoteAriaLabel: content.formatQuoteAriaLabel,
        formatLinkAriaLabel: content.formatLinkAriaLabel,
        formatFontSizeAriaLabel: content.formatFontSizeAriaLabel,
        formatFontSizeDecreaseAriaLabel: content.formatFontSizeDecreaseAriaLabel,
        formatFontSizeIncreaseAriaLabel: content.formatFontSizeIncreaseAriaLabel,
        mentionListAriaLabel: content.composerMentionListAriaLabel,
        mentionEmptyLabel: content.composerMentionEmptyLabel,
      }}
    />
  );
}
