import { ArrowDown } from "lucide-react";

/** Scroll chrome only. The consumer owns viewport measurement and navigation. */
export type ConversationScrollNavigatorProps = {
  visible: boolean;
  onGoToLatest: () => void;
  disabled?: boolean;
  label?: string;
  className?: string;
};

export function ConversationScrollNavigator({
  visible,
  onGoToLatest,
  disabled = false,
  label = "Ir para o final da conversa",
  className,
}: ConversationScrollNavigatorProps) {
  if (!visible) return null;

  return (
    <div
      className={["delpi-ui-conversation-scroll-navigator", className]
        .filter(Boolean)
        .join(" ")}
    >
      <button
        type="button"
        className="delpi-ui-conversation-scroll-navigator__button"
        onClick={onGoToLatest}
        disabled={disabled}
        aria-label={label}
        title={label}
      >
        <ArrowDown aria-hidden="true" size={16} />
        <span>Ir para o final</span>
      </button>
    </div>
  );
}
