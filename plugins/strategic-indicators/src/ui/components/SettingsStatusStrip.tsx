type SettingsStatusStripProps = {
  loading: boolean;
  error: string | null;
  successMessage: string | null;
  updatedAt: string | null;
  updatedByEmail: string | null;
  onRetry: () => void;
  onDismissSuccess: () => void;
};

export function SettingsStatusStrip({
  loading,
  error,
  successMessage,
  updatedAt,
  updatedByEmail,
  onRetry,
  onDismissSuccess,
}: SettingsStatusStripProps) {
  if (loading) {
    return (
      <div className="si-settings-status-strip si-settings-status-strip--neutral">
        Carregando configurações reais...
      </div>
    );
  }

  if (error) {
    return (
      <div className="si-settings-status-strip si-settings-status-strip--error">
        <span>{error}</span>
        <button
          type="button"
          className="si-settings-status-strip__button"
          onClick={onRetry}
        >
          Tentar novamente
        </button>
      </div>
    );
  }

  if (successMessage) {
    return (
      <div className="si-settings-status-strip si-settings-status-strip--success">
        <span>{successMessage}</span>
        <button
          type="button"
          className="si-settings-status-strip__button si-settings-status-strip__button--ghost"
          onClick={onDismissSuccess}
        >
          Fechar
        </button>
      </div>
    );
  }

  if (updatedAt) {
    return (
      <div className="si-settings-status-strip si-settings-status-strip--neutral">
        Última atualização registrada em{" "}
        <strong>{new Date(updatedAt).toLocaleString("pt-BR")}</strong>
        {updatedByEmail ? (
          <>
            {" "}por <strong>{updatedByEmail}</strong>
          </>
        ) : null}
      </div>
    );
  }

  return null;
}