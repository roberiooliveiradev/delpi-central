import { useEffect, type ReactNode } from "react";
import { X } from "lucide-react";

type FiModalProps = {
  open: boolean;
  title: string;
  subtitle?: string;
  onClose: () => void;
  children: ReactNode;
};

export function FiModal({ open, title, subtitle, onClose, children }: FiModalProps) {
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

  return (
    <div className="fi-modal" role="dialog" aria-modal="true" aria-labelledby="fi-modal-title">
      <button
        className="fi-modal__backdrop"
        type="button"
        onClick={onClose}
        aria-label="Fechar detalhamento"
      />
      <div className="fi-modal__panel">
        <header className="fi-modal__header">
          <div>
            <h2 id="fi-modal-title" className="fi-modal__title">
              {title}
            </h2>
            {subtitle ? <p className="fi-modal__subtitle">{subtitle}</p> : null}
          </div>
          <button
            type="button"
            className="fi-btn fi-btn--secondary fi-modal__close"
            onClick={onClose}
          >
            <X size={16} aria-hidden="true" />
            Fechar
          </button>
        </header>
        <div className="fi-modal__body">{children}</div>
      </div>
    </div>
  );
}
