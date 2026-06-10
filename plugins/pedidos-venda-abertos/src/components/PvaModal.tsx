import { useEffect } from "react";
import { X } from "lucide-react";

type PvaModalProps = {
  open: boolean;
  title: string;
  subtitle?: string;
  onClose: () => void;
  children: React.ReactNode;
};

export function PvaModal({ open, title, subtitle, onClose, children }: PvaModalProps) {
  useEffect(() => {
    if (!open) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };

    document.addEventListener("keydown", handleKeyDown);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = prevOverflow;
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="pva-modal" role="dialog" aria-modal="true" aria-label={title}>
      <button
        className="pva-modal__backdrop"
        type="button"
        onClick={onClose}
        aria-label="Fechar modal"
      />
      <div className="pva-modal__panel">
        <header className="pva-modal__header">
          <div>
            <h2>{title}</h2>
            {subtitle ? <p>{subtitle}</p> : null}
          </div>
          <button className="pva-btn pva-btn--ghost pva-modal__close" type="button" onClick={onClose}>
            <X size={16} aria-hidden="true" />
            Fechar
          </button>
        </header>
        <div className="pva-modal__body">{children}</div>
      </div>
    </div>
  );
}
