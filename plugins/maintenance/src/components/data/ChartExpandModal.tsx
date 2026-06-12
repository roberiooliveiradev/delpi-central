import { useEffect, type ReactNode } from "react";
import { X } from "lucide-react";

type ChartExpandModalProps = {
  open: boolean;
  title: string;
  onClose: () => void;
  actions?: ReactNode;
  children: ReactNode;
};

export function ChartExpandModal({
  open,
  title,
  onClose,
  actions,
  children,
}: ChartExpandModalProps) {
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
    <div className="dm-chart-modal" role="dialog" aria-modal="true" aria-label={title}>
      <button
        type="button"
        className="dm-chart-modal__backdrop"
        onClick={onClose}
        aria-label="Fechar gráfico expandido"
      />
      <div className="dm-chart-modal__panel">
        <header className="dm-chart-modal__header">
          <div className="dm-chart-modal__header-text">
            <h2 className="dm-chart-modal__title">{title}</h2>
            {actions ? <div className="dm-chart-modal__actions">{actions}</div> : null}
          </div>
          <button type="button" className="dm-ghost-btn dm-chart-modal__close" onClick={onClose}>
            <X size={16} aria-hidden="true" />
            Fechar
          </button>
        </header>
        <div className="dm-chart-modal__body">
          <div className="dm-chart-wrap dm-chart-wrap--expanded">{children}</div>
        </div>
      </div>
    </div>
  );
}
