import type { ReactNode } from "react";
import { useEffect } from "react";
import { createPortal } from "react-dom";

type GuiasConfirmDialogProps = {
  open: boolean;
  title: string;
  message: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  busy?: boolean;
  variant?: "default" | "danger";
  onConfirm: () => void;
  onCancel: () => void;
};

/**
 * Modal de confirmação local (escopo do plugin).
 * Evita acoplar o typecheck ao source do plugin-ui via Module Federation.
 */
export function GuiasConfirmDialog({
  open,
  title,
  message,
  confirmLabel = "Confirmar",
  cancelLabel = "Cancelar",
  busy = false,
  variant = "default",
  onConfirm,
  onCancel,
}: GuiasConfirmDialogProps) {
  useEffect(() => {
    if (!open) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [open]);

  if (!open || typeof document === "undefined") return null;

  return createPortal(
    <div
      className="dashboard-guias-procedimentos gp-modal-overlay"
      role="presentation"
      onClick={onCancel}
    >
      <div
        className="gp-modal gp-modal--confirm"
        role="dialog"
        aria-modal="true"
        aria-labelledby="gp-confirm-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="gp-modal__header">
          <h2 id="gp-confirm-title" className="gp-modal__title">
            {title}
          </h2>
          <button
            type="button"
            className="gp-modal__close"
            aria-label="Fechar"
            onClick={onCancel}
          >
            ×
          </button>
        </div>
        <div className="gp-modal__body">
          <p className="gp-confirm-modal__message">{message}</p>
          <div className="gp-form-actions gp-form-actions--end">
            <button
              type="button"
              className="gp-btn gp-btn--ghost"
              onClick={onCancel}
              disabled={busy}
            >
              {cancelLabel}
            </button>
            <button
              type="button"
              className={
                variant === "danger" ? "gp-danger-btn" : "gp-primary-btn"
              }
              onClick={onConfirm}
              disabled={busy}
            >
              {busy ? "Aguarde…" : confirmLabel}
            </button>
          </div>
        </div>
      </div>
    </div>,
    document.body,
  );
}
