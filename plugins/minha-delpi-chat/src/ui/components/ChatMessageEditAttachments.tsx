import { Paperclip } from "lucide-react";
import { useId, useRef } from "react";

import type { ChatAttachmentCardModel } from "./ChatAttachmentCard";
import { ChatAttachmentCard } from "./ChatAttachmentCard";
import "./ChatAttachmentCard.css";

type ChatMessageEditAttachmentsProps = {
  attachments: ChatAttachmentCardModel[];
  disabled?: boolean;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  onAddFiles: (files: File[]) => void;
  onRemoveAttachment: (key: string) => void;
  onPreviewAttachment: (attachment: ChatAttachmentCardModel) => void;
};

export function ChatMessageEditAttachments({
  attachments,
  disabled,
  getAccessToken,
  onAddFiles,
  onRemoveAttachment,
  onPreviewAttachment,
}: ChatMessageEditAttachmentsProps) {
  const inputId = useId();
  const inputRef = useRef<HTMLInputElement | null>(null);

  return (
    <div className="mdc-chat-message-edit-attachments">
      <div className="mdc-chat-message-edit-attachments__header">
        <span>
          <Paperclip size={14} aria-hidden="true" /> {attachments.length} arquivo(s) neste reenvio
        </span>

        <label
          htmlFor={inputId}
          className="mdc-chat-message-edit-attachments__add"
          aria-disabled={disabled}
        >
          Anexar mais
          <input
            id={inputId}
            ref={inputRef}
            type="file"
            multiple
            disabled={disabled}
            onChange={(event) => {
              const files = Array.from(event.target.files ?? []).filter((file) => file.size > 0);
              if (files.length > 0) {
                onAddFiles(files);
              }
              event.target.value = "";
            }}
          />
        </label>
      </div>

      {attachments.length > 0 ? (
        <div className="mdc-chat-message-attachment-cards">
          {attachments.map((attachment) => (
            <ChatAttachmentCard
              key={attachment.key}
              attachment={attachment}
              editable
              getAccessToken={getAccessToken}
              onPreview={onPreviewAttachment}
              onRemove={onRemoveAttachment}
            />
          ))}
        </div>
      ) : (
        <p className="mdc-chat-message-edit-attachments__empty">
          Nenhum arquivo anexado. Você pode adicionar novos antes de reenviar.
        </p>
      )}
    </div>
  );
}
