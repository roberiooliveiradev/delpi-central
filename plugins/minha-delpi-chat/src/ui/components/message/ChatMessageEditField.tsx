import { useAutoGrowTextarea } from "../../hooks/useAutoGrowTextarea";
import type { ChatAttachmentCardModel } from "../workspace/ChatAttachmentCard";
import { ChatMessageEditAttachments } from "./ChatMessageEditAttachments";

function resolveEditFieldLayout() {
  // O campo de edição é inline e cresce para BAIXO (a lista rola), então
  // não usa o limite por espaço acima; a proporção da viewport pode ser
  // mais generosa, principalmente em telas baixas, para caber a pergunta.
  if (typeof window === "undefined") {
    return { maxHeightViewportRatio: 0.4 };
  }

  if (window.matchMedia("(max-width: 480px)").matches) {
    return { maxHeightViewportRatio: 0.55 };
  }

  if (window.matchMedia("(max-width: 720px)").matches) {
    return { maxHeightViewportRatio: 0.5 };
  }

  return { maxHeightViewportRatio: 0.4 };
}

type ChatMessageEditFieldProps = {
  value: string;
  disabled?: boolean;
  attachments?: ChatAttachmentCardModel[];
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  onChange: (value: string) => void;
  onCancel: () => void;
  onSubmit: () => void;
  onAddAttachments?: (files: File[]) => void;
  onRemoveAttachment?: (key: string) => void;
  onPreviewAttachment?: (attachment: ChatAttachmentCardModel) => void;
};

export function ChatMessageEditField({
  value,
  disabled,
  attachments = [],
  getAccessToken,
  onChange,
  onCancel,
  onSubmit,
  onAddAttachments,
  onRemoveAttachment,
  onPreviewAttachment,
}: ChatMessageEditFieldProps) {
  const layout = resolveEditFieldLayout();
  const { ref, syncHeight } = useAutoGrowTextarea({
    value,
    disableOffsetCap: true,
    maxHeightViewportRatio: layout.maxHeightViewportRatio,
  });

  return (
    <div className="mdc-chat-message-edit mdc-chat-message-edit--inline">
      {onAddAttachments && onRemoveAttachment && onPreviewAttachment ? (
        <ChatMessageEditAttachments
          attachments={attachments}
          disabled={disabled}
          getAccessToken={getAccessToken}
          onAddFiles={onAddAttachments}
          onRemoveAttachment={onRemoveAttachment}
          onPreviewAttachment={onPreviewAttachment}
        />
      ) : null}

      <textarea
        ref={ref}
        className="mdc-chat-message-edit__input mdc-auto-grow-textarea"
        value={value}
        rows={1}
        autoFocus
        onChange={(event) => {
          onChange(event.target.value);
          requestAnimationFrame(() => syncHeight());
        }}
        onInput={() => {
          requestAnimationFrame(() => syncHeight());
        }}
        onKeyDown={(event) => {
          if (event.key === "Escape") {
            event.preventDefault();
            onCancel();
          }

          if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
            event.preventDefault();
            onSubmit();
          }
        }}
      />

      <div className="mdc-chat-message-edit-actions">
        <button type="button" onClick={onCancel}>
          Cancelar
        </button>
        <button
          type="button"
          className="mdc-chat-message-edit-actions__primary"
          disabled={disabled}
          onClick={onSubmit}
        >
          Enviar
        </button>
      </div>
    </div>
  );
}
