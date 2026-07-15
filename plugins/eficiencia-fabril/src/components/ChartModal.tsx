import { EF_GHOST_BTN } from "../ui/ghostChrome";
import { useEffect } from "react";
import { X } from "lucide-react";

type ChartModalProps = {
  open: boolean;
  title: string;
  subtitle?: string;
  onClose: () => void;
  children: React.ReactNode;
};

export function ChartModal({ open, title, subtitle, onClose, children }: ChartModalProps) {
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
    <div className="ef-modal" role="dialog" aria-modal="true" aria-label={title}>
      <button className="ef-modal__backdrop" type="button" onClick={onClose} aria-label="Fechar modal" />
      <div className="ef-modal__panel">
        <header className="ef-modal__header">
          <div>
            <h2>{title}</h2>
            {subtitle ? <p>{subtitle}</p> : null}
          </div>
          <button className={`${EF_GHOST_BTN} ef-modal__close`} type="button" onClick={onClose}>
            <X size={16} aria-hidden />
            Fechar
          </button>
        </header>
        <div className="ef-modal__body">{children}</div>
      </div>
    </div>
  );
}

