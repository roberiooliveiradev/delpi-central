export type ConcurrentChangeNoticeProps = {
  message: string;
  actionLabel?: string;
  onAction: () => void;
  onDismiss?: () => void;
};

export function ConcurrentChangeNotice({
  message,
  actionLabel = "Recarregar",
  onAction,
  onDismiss,
}: ConcurrentChangeNoticeProps) {
  return (
    <div className="delpi-ui-concurrent-change" role="status" aria-live="polite">
      <p className="delpi-ui-concurrent-change__message">{message}</p>
      <button type="button" className="delpi-ui-concurrent-change__action" onClick={onAction}>
        {actionLabel}
      </button>
      {onDismiss ? (
        <button
          type="button"
          className="delpi-ui-concurrent-change__dismiss"
          onClick={onDismiss}
        >
          Dispensar
        </button>
      ) : null}
    </div>
  );
}
