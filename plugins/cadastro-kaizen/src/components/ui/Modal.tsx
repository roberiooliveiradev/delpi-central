import { X } from "lucide-react";
import { useEffect, type ReactNode } from "react";
import { createPortal } from "react-dom";

type ModalProps = {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
  className?: string;
};

export function Modal({ open, title, onClose, children, className }: ModalProps) {
  useEffect(() => {
    if (!open) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };

    document.addEventListener("keydown", handleKeyDown);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [open, onClose]);

  if (!open) return null;

  const modalClass = ["kz-modal", className].filter(Boolean).join(" ");

  return createPortal(
    <div className="kz-modal-overlay dashboard-cadastro-kaizen" onClick={onClose}>
      <div
        className={modalClass}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onClick={(event) => event.stopPropagation()}
      >
        <header className="kz-modal__header">
          <h2 className="kz-modal__title">{title}</h2>
          <button
            type="button"
            className="kz-ghost-btn kz-modal__close"
            aria-label="Fechar"
            onClick={onClose}
          >
            <X size={18} aria-hidden="true" />
          </button>
        </header>
        <div className="kz-modal__body">{children}</div>
      </div>
    </div>,
    document.body,
  );
}
