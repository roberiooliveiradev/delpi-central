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
      if (event.key === "Escape") {
        onClose();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [open, onClose]);

  if (!open) {
    return null;
  }

  const modalClass = ["pac-modal", className].filter(Boolean).join(" ");

  return createPortal(
    <div className="pac-modal-overlay" onClick={onClose}>
      <div
        className={modalClass}
        role="dialog"
        aria-modal="true"
        aria-labelledby="pac-modal-title"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="pac-modal__header">
          <h2 id="pac-modal-title" className="pac-modal__title">
            {title}
          </h2>
          <button
            type="button"
            className="pac-ghost-btn pac-ghost-btn--icon pac-modal__close"
            aria-label="Fechar"
            onClick={onClose}
          >
            <X size={18} aria-hidden="true" />
          </button>
        </header>
        <div className="pac-modal__body">{children}</div>
      </div>
    </div>,
    document.body,
  );
}
