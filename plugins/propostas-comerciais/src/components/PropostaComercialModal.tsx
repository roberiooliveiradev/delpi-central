import { useEffect } from "react";
import { X } from "lucide-react";

type PropostaComercialModalProps = {
  open: boolean;
  title: string;
  subtitle?: string;
  onClose: () => void;
  children: React.ReactNode;
  footer?: React.ReactNode;
};

export function PropostaComercialModal({
  open,
  title,
  subtitle,
  onClose,
  children,
  footer,
}: PropostaComercialModalProps) {
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
    <div className="pc-modal" role="dialog" aria-modal="true" aria-label={title}>
      <button
        className="pc-modal__backdrop"
        type="button"
        onClick={onClose}
        aria-label="Fechar modal"
      />
      <div className="pc-modal__panel">
        <header className="pc-modal__header">
          <div>
            <h2>{title}</h2>
            {subtitle ? <p>{subtitle}</p> : null}
          </div>
          <button className="pc-btn pc-btn--ghost pc-modal__close" type="button" onClick={onClose}>
            <X size={16} aria-hidden="true" />
            Fechar
          </button>
        </header>
        <div className="pc-modal__body">{children}</div>
        {footer ? <footer className="pc-modal__footer">{footer}</footer> : null}
      </div>
    </div>
  );
}
