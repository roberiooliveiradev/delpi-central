import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import "./ChatMarkdown.css";

type ChatMarkdownProps = {
  content: string;
  compact?: boolean;
};

export function ChatMarkdown({ content, compact }: ChatMarkdownProps) {
  return (
    <div
      className={
        compact ? "mdc-chat-markdown mdc-chat-markdown--compact" : "mdc-chat-markdown"
      }
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  );
}
