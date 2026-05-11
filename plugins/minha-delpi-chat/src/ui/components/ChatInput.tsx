type ChatInputProps = {
  value: string;
  disabled?: boolean;
  isSending?: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onCancel?: () => void;
};

export function ChatInput({
  value,
  disabled,
  isSending,
  onChange,
  onSubmit,
  onCancel,
}: ChatInputProps) {
  return (
    <form
      className="mdc-chat-input"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <textarea
        value={value}
        disabled={disabled || isSending}
        placeholder="Digite uma pergunta..."
        rows={3}
        onChange={(event) => onChange(event.target.value)}
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
