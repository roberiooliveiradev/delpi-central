import "./ChatTrustBadges.css";

export type ChatTrustSignal = {
  id: string;
  label: string;
};

export function ChatTrustBadges({
  signals,
}: {
  signals: ChatTrustSignal[];
}) {
  if (!signals.length) {
    return null;
  }

  return (
    <div
      className="mdc-chat-trust-badges"
      role="list"
      aria-label="Sinais de confiança da resposta"
    >
      {signals.map((signal) => (
        <span
          key={signal.id}
          className={`mdc-chat-trust-badge mdc-chat-trust-badge--${signal.id}`}
          role="listitem"
          title={signal.label}
        >
          {signal.label}
        </span>
      ))}
    </div>
  );
}
