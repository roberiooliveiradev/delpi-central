import { useEffect, type ReactNode } from "react";
import { X } from "lucide-react";

type Props = {
  open: boolean;
  title: string;
  titleId: string;
  meta?: string;
  icon: ReactNode;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
  dialogClassName?: string;
};

export function NcBoardModalShell({
  open,
  title,
  titleId,
  meta,
  icon,
  onClose,
  children,
  footer,
  dialogClassName,
}: Props) {
  useEffect(() => {
    if (!open) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKeyDown);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [open, onClose]);

  if (!open) return null;

  const dialogClass = ["a5s-nc-board-treat-dialog", dialogClassName].filter(Boolean).join(" ");

  return (
    <div className="a5s-confirm-overlay" role="presentation" onClick={onClose}>
      <div
        className={dialogClass}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(event) => event.stopPropagation()}
      >
        <header className="a5s-nc-board-treat-dialog__head">
          <div className="a5s-nc-board-treat-dialog__title-wrap">
            {icon}
            <div>
              <h2 id={titleId}>{title}</h2>
              {meta ? <p className="a5s-nc-board-treat-dialog__meta">{meta}</p> : null}
            </div>
          </div>
          <button
            type="button"
            className="a5s-nc-board-treat-dialog__close"
            aria-label="Fechar"
            onClick={onClose}
          >
            <X size={18} aria-hidden />
          </button>
        </header>

        {children}

        {footer ? <footer className="a5s-nc-board-treat-dialog__actions">{footer}</footer> : null}
      </div>
    </div>
  );
}
