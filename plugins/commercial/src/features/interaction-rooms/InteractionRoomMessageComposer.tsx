import { useCallback, useMemo, useState } from "react";

import {
  postInteractionMessage,
  uploadRoomMessageAttachment,
  type InteractionMessageDto,
} from "../../api/interactionRoomsApi";
import {
  CM_PORTAL_SCOPE,
  CommercialAttachmentPreviewStrip,
  CommercialFileDropzone,
  CommercialMentionComposer,
} from "../../app/commercialUi";
import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";
import type { InteractionMentionHit } from "./mentionSuggestAdapter";
import { useInteractionMentionSuggest } from "./useInteractionMentionSuggest";

const ATTACH_ACCEPT =
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
};

/**
 * Composer da sala: MentionComposer + FileDropzone (owner_type=room_message após POST).
 */
export function InteractionRoomMessageComposer({
  roomId,
  disabled = false,
  onMessageCreated,
  onError,
}: Props) {
  const content = INTERACTION_ROOMS_CONTENT;
  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState<PendingFile[]>([]);
  const [showDropzone, setShowDropzone] = useState(false);
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

  const onFilesSelected = useCallback((files: File[]) => {
    if (!files.length) return;
    setPending((prev) => [
      ...prev,
      ...files.map((file) => ({
        id: `pending-${file.name}-${file.size}-${file.lastModified}-${Math.random().toString(36).slice(2, 8)}`,
        file,
      })),
    ]);
    setShowDropzone(true);
  }, []);

  const onSubmit = useCallback(async () => {
    const id = roomId.trim();
    const body = draft.trim();
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
      setShowDropzone(false);
      resetMentions();
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
    showDropzone || pending.length > 0 ? (
      <>
        <CommercialFileDropzone
          multiple
          accept={ATTACH_ACCEPT}
          busy={submitting}
          disabled={disabled || submitting}
          onFilesSelected={onFilesSelected}
          labels={{
            title: submitting ? content.dropzoneBusyTitle : content.dropzoneTitle,
            hint: content.dropzoneHint,
          }}
        />
        {pending.length > 0 ? (
          <CommercialAttachmentPreviewStrip
            mode="manage"
            heading={content.pendingAttachmentsHeading}
            items={stripItems}
            onOpen={() => undefined}
            onRemove={(item) => {
              setPending((prev) => prev.filter((row) => row.id !== item.id));
            }}
          />
        ) : null}
      </>
    ) : null;

  return (
    <CommercialMentionComposer
      value={draft}
      onChange={setDraft}
      onSubmit={() => {
        void onSubmit();
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
      onAttachClick={() => setShowDropzone((value) => !value)}
      footer={footer}
      labels={{
        placeholder: content.composerPlaceholder,
        sendAriaLabel: content.composerSendAriaLabel,
        attachAriaLabel: content.composerAttachAriaLabel,
        mentionListAriaLabel: content.composerMentionListAriaLabel,
        mentionEmptyLabel: content.composerMentionEmptyLabel,
      }}
    />
  );
}
