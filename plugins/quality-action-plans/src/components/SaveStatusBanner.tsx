import { CheckCircle2, Loader2, XCircle } from "lucide-react";

type SaveStatusBannerProps = {
  saving: string | null;
  success: string | null;
  error: string | null;
  onDismiss?: () => void;
};

export function SaveStatusBanner({ saving, success, error, onDismiss }: SaveStatusBannerProps) {
  if (!saving && !success && !error) {
    return null;
  }

  const variant = saving ? "saving" : error ? "error" : "success";
  const message = saving
    ? "Salvando alterações…"
    : error ?? success ?? "";

  return (
    <div
      className={`pac-save-banner pac-save-banner--${variant}`}
      role={error ? "alert" : "status"}
      aria-live="polite"
    >
      <span className="pac-save-banner__icon" aria-hidden="true">
        {saving ? <Loader2 size={18} className="pac-save-banner__spin" /> : null}
        {!saving && error ? <XCircle size={18} /> : null}
        {!saving && success ? <CheckCircle2 size={18} /> : null}
      </span>
      <span className="pac-save-banner__text">{message}</span>
      {!saving && onDismiss ? (
        <button type="button" className="pac-save-banner__dismiss" onClick={onDismiss}>
          Fechar
        </button>
      ) : null}
    </div>
  );
}
