import "./ChatMilestoneCelebration.css";

export type MilestoneCelebration = {
  id: string;
  label?: string;
  message: string;
};

type ChatMilestoneCelebrationProps = {
  celebrations: MilestoneCelebration[];
};

export function ChatMilestoneCelebration({ celebrations }: ChatMilestoneCelebrationProps) {
  if (celebrations.length === 0) {
    return null;
  }

  return (
    <div className="mdc-chat-milestone" role="status" aria-live="polite">
      {celebrations.map((item) => (
        <p key={item.id}>
          {item.label ? <strong>{item.label}. </strong> : null}
          <span>{item.message}</span>
        </p>
      ))}
    </div>
  );
}
