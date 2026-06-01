import { useAutoGrowTextarea } from "../hooks/useAutoGrowTextarea";

function resolveEditFieldLayout() {
  if (typeof window === "undefined") {
    return { topInset: 32, maxHeightViewportRatio: 0.32 };
  }

  if (window.matchMedia("(max-width: 480px)").matches) {
    return { topInset: 112, maxHeightViewportRatio: 0.42 };
  }

  if (window.matchMedia("(max-width: 720px)").matches) {
    return { topInset: 88, maxHeightViewportRatio: 0.38 };
  }

  return { topInset: 40, maxHeightViewportRatio: 0.34 };
}

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
  const layout = resolveEditFieldLayout();
  const { ref, syncHeight } = useAutoGrowTextarea({
    value,
    topInset: layout.topInset,
    maxHeightViewportRatio: layout.maxHeightViewportRatio,
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
