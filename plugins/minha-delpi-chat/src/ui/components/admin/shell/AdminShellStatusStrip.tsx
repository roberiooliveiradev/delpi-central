import "./AdminShellStatusStrip.css";

type AdminShellStatusStripProps = {
  error?: string | null;
  successMessage?: string | null;
  lastUpdatedAt?: Date | null;
  isLoading?: boolean;
  onRefresh?: () => void;
};

export function AdminShellStatusStrip({
  error,
  successMessage,
  lastUpdatedAt,
  isLoading,
  onRefresh,
}: AdminShellStatusStripProps) {
  const hasMessages = Boolean(error || successMessage || lastUpdatedAt);

  if (!hasMessages) {
    return null;
  }

  return (
    <div className="mdc-admin-status-strip" role="status" aria-live="polite">
      <div className="mdc-admin-status-strip__messages">
        {error ? (
          <p className="mdc-admin-status-strip__error" role="alert">
            {error}
          </p>
        ) : null}
        {successMessage ? (
          <p className="mdc-admin-status-strip__success">{successMessage}</p>
        ) : null}
      </div>

      <div className="mdc-admin-status-strip__meta">
        {lastUpdatedAt ? (
          <span className="mdc-admin-status-strip__updated">
            Atualizado {lastUpdatedAt.toLocaleString("pt-BR")}
          </span>
        ) : null}
        {onRefresh ? (
          <button
            type="button"
            className="mdc-chat-ws-outline-btn mdc-admin-status-strip__refresh"
            onClick={onRefresh}
            disabled={isLoading}
          >
            {isLoading ? "Atualizando..." : "Atualizar dados"}
          </button>
        ) : null}
      </div>
    </div>
  );
}
