type StateBoxProps = {
  title: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
};

export function ErrorState({ title, message, actionLabel, onAction }: StateBoxProps) {
  return (
    <div className="sm-state-box sm-state-box--error" role="alert">
      <h2>{title}</h2>
      <p>{message}</p>
      {actionLabel && onAction ? (
        <button type="button" className="sm-btn sm-btn--primary" onClick={onAction}>
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
}

export function EmptyState({ title, message }: Omit<StateBoxProps, "actionLabel" | "onAction">) {
  return (
    <div className="sm-state-box">
      <h2>{title}</h2>
      <p>{message}</p>
    </div>
  );
}

export function LoadingState({ percent }: { percent: number }) {
  return (
    <div className="sm-state-box sm-state-box--loading" aria-busy="true">
      <h2>Carregando painel…</h2>
      <p>{percent > 0 ? `${percent}%` : "Consultando API de refugos"}</p>
      <div className="sm-progress">
        <div className="sm-progress__bar" style={{ width: `${Math.max(percent, 8)}%` }} />
      </div>
    </div>
  );
}
