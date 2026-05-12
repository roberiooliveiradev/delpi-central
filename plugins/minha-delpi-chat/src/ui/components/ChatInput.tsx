import "./ChatInput.css";

type ChatInputProps = {
  value: string;
  disabled?: boolean;
  isSending?: boolean;
  variant?: "dock" | "center";
  onChange: (value: string) => void;
  onSubmit: () => void;
  onCancel?: () => void;
};

export function ChatInput({
  value,
  disabled,
  isSending,
  variant = "dock",
  onChange,
  onSubmit,
  onCancel,
}: ChatInputProps) {
  return (
    <form
      className={
        variant === "center"
          ? "mdc-chat-input mdc-chat-input--center"
          : "mdc-chat-input"
      }
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <textarea
        value={value}
        disabled={disabled || isSending}
        placeholder="Digite uma pergunta..."
        rows={variant === "center" ? 2 : 3}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            onSubmit();
          }
        }}
      />

      {isSending ? (
        <button type="button" onClick={onCancel}>
          Cancelar
        </button>
      ) : (
        <button type="submit" disabled={disabled || !value.trim()}>
          Enviar
        </button>
      )}

      <small>
        A resposta será exibida em tempo real e salva no histórico ao concluir.
      </small>
    </form>
  );
}
