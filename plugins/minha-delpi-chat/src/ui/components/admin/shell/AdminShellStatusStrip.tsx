import "./AdminShellStatusStrip.css";

type AdminShellStatusStripProps = {
  error: string | null;
  successMessage: string | null;
  lastRefreshedAt: Date | null;
  isLoading: boolean;
  onRefresh: () => void;
};

function formatRefreshedAt(value: Date | null): string {
  if (!value) {
    return "Ainda não atualizado";
  }

  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "medium",
  }).format(value);
}

export function AdminShellStatusStrip({
  error,
  successMessage,
  lastRefreshedAt,
  isLoading,
  onRefresh,
}: AdminShellStatusStripProps) {
  const hasAlert = Boolean(error || successMessage);

  return (
    <div
      className={`mdc-admin-status-strip${hasAlert ? " mdc-admin-status-strip--has-alert" : ""}`}
      role="region"
      aria-label="Status do painel"
    >
      <div className="mdc-admin-status-strip__meta">
        <span className="mdc-admin-status-strip__label">Última atualização</span>
        <time dateTime={lastRefreshedAt?.toISOString()}>{formatRefreshedAt(lastRefreshedAt)}</time>
        {isLoading ? <span className="mdc-admin-status-strip__loading">Atualizando…</span> : null}
      </div>

      <button
        type="button"
        className="mdc-admin-status-strip__refresh"
        onClick={onRefresh}
        disabled={isLoading}
      >
        Atualizar dados
      </button>

      {error ? (
        <p className="mdc-admin-status-strip__alert mdc-admin-status-strip__alert--error" role="alert">
          {error}
        </p>
      ) : null}

      {successMessage ? (
        <p className="mdc-admin-status-strip__alert mdc-admin-status-strip__alert--success" role="status">
          {successMessage}
        </p>
      ) : null}
    </div>
  );
}
