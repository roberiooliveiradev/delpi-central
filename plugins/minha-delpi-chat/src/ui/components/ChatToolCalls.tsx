import type { ChatToolCall } from "../../data/api/chatTypes";

type ChatToolCallsProps = {
  toolCalls?: ChatToolCall[];
};

export function ChatToolCalls({ toolCalls }: ChatToolCallsProps) {
  if (!toolCalls || toolCalls.length === 0) {
    return null;
  }

  return (
    <div className="mdc-chat-tool-calls" aria-label="Ferramentas consultadas">
      <strong>Ferramentas consultadas</strong>

      <ul>
        {toolCalls.map((toolCall, index) => (
          <li key={`${toolCall.name}-${index}`}>
            <span>{toolCall.name || "Ferramenta"}</span>
            {toolCall.reason ? <small>{toolCall.reason}</small> : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
