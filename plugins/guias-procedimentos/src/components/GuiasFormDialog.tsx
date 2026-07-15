import type { ReactNode } from "react";
import { useEffect } from "react";
import { createPortal } from "react-dom";

type GuiasFormDialogProps = {
  open: boolean;
  title: string;
  children: ReactNode;
  busy?: boolean;
  confirmLabel?: string;
  cancelLabel?: string;
  confirmDisabled?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
};

export function GuiasFormDialog({
  open,
  title,
  children,
  busy = false,
  confirmLabel = "Salvar",
  cancelLabel = "Cancelar",
  confirmDisabled = false,
  onConfirm,
  onCancel,
}: GuiasFormDialogProps) {
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
        className="gp-modal gp-modal--form"
        role="dialog"
        aria-modal="true"
        aria-labelledby="gp-form-dialog-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="gp-modal__header">
          <h2 id="gp-form-dialog-title" className="gp-modal__title">
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
          {children}
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
              className="gp-primary-btn"
              onClick={onConfirm}
              disabled={busy || confirmDisabled}
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
