type ChatInputProps = {
  value: string;
  disabled?: boolean;
  onChange: (value: string) => void;
};

export function ChatInput({ value, disabled, onChange }: ChatInputProps) {
  return (
    <form className="mdc-chat-input" onSubmit={(event) => event.preventDefault()}>
      <textarea
        value={value}
        disabled={disabled}
        placeholder="Digite uma pergunta..."
        rows={3}
        onChange={(event) => onChange(event.target.value)}
      />

      <button type="submit" disabled>
        Enviar
      </button>

      <small>
        O envio de mensagens ao modelo será habilitado na Etapa 9, após integração com Ollama.
      </small>
    </form>
  );
}
