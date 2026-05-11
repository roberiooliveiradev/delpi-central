type ChatInputProps = {
  value: string;
  disabled?: boolean;
  isSending?: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
};

export function ChatInput({
  value,
  disabled,
  isSending,
  onChange,
  onSubmit,
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

      <button type="submit" disabled={disabled || isSending || !value.trim()}>
        {isSending ? "Enviando..." : "Enviar"}
      </button>

      <small>
        A resposta será gerada localmente pelo Ollama e salva no histórico da sessão.
      </small>
    </form>
  );
}
