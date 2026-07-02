import { useEffect, type ReactNode } from "react";
import { X } from "lucide-react";

type FccModalProps = {
  open: boolean;
  title: string;
  subtitle?: string;
  onClose: () => void;
  children: ReactNode;
};

export function FccModal({ open, title, subtitle, onClose, children }: FccModalProps) {
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
    <div className="fcc-modal" role="dialog" aria-modal="true" aria-label={title}>
      <button
        className="fcc-modal__backdrop"
        type="button"
        onClick={onClose}
        aria-label="Fechar modal"
      />
      <div className="fcc-modal__panel">
        <header className="fcc-modal__header">
          <div>
            <h2 className="fcc-modal__title">{title}</h2>
            {subtitle ? <p className="fcc-modal__subtitle">{subtitle}</p> : null}
          </div>
          <button type="button" className="fcc-btn fcc-btn--secondary fcc-modal__close" onClick={onClose}>
            <X size={16} aria-hidden="true" />
            Fechar
          </button>
        </header>
        <div className="fcc-modal__body">{children}</div>
      </div>
    </div>
  );
}
