import { useAutoGrowTextarea } from "../hooks/useAutoGrowTextarea";

type ChatMessageEditFieldProps = {
  value: string;
  disabled?: boolean;
  onChange: (value: string) => void;
  onCancel: () => void;
  onSubmit: () => void;
};

export function ChatMessageEditField({
  value,
  disabled,
  onChange,
  onCancel,
  onSubmit,
}: ChatMessageEditFieldProps) {
  const { ref, syncHeight } = useAutoGrowTextarea({
    value,
    bottomInset: 24,
    maxHeightCapPx: 224,
  });

  return (
    <div className="mdc-chat-message-edit mdc-chat-message-edit--inline">
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
