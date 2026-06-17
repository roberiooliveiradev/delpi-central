import "./ChatMessageList.css";

type ChatThinkingDotsProps = {
  label?: string | null;
};

/** Indicador de carregamento estilo ChatGPT (três pontos pulsando). */
export function ChatThinkingDots({ label }: ChatThinkingDotsProps) {
  const text = label?.trim();

  return (
    <div className="mdc-chat-thinking" role="status" aria-live="polite">
      <span className="mdc-chat-thinking__dot" />
      <span className="mdc-chat-thinking__dot" />
      <span className="mdc-chat-thinking__dot" />
      {text ? <p>{text}</p> : null}
    </div>
  );
}
