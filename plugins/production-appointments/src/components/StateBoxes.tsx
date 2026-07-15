type StateBoxProps = {
  title: string;
  message?: string;
};

export function LoadingState({ title, message }: StateBoxProps) {
  return (
    <div className="pa-state-box" role="status">
      <strong>{title}</strong>
      {message ? <p>{message}</p> : null}
    </div>
  );
}

export function EmptyState({ title, message }: StateBoxProps) {
  return (
    <div className="pa-state-box">
      <strong>{title}</strong>
      {message ? <p>{message}</p> : null}
    </div>
  );
}

export function ErrorState({ title, message }: StateBoxProps) {
  return (
    <div className="pa-state-box pa-state-box--error" role="alert">
      <strong>{title}</strong>
      {message ? <p>{message}</p> : null}
    </div>
  );
}
