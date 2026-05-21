import { useEffect, useId, type PropsWithChildren, type ReactNode } from "react";
import "./DrawerPanel.css";

type DrawerPanelProps = PropsWithChildren<{
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  footer?: ReactNode;
  size?: "md" | "lg" | "xl";
}>;

export function DrawerPanel({
  open,
  onClose,
  title,
  description,
  footer,
  size = "lg",
  children,
}: DrawerPanelProps) {
  const titleId = useId();
  const descriptionId = useId();

  useEffect(() => {
    if (!open) return;

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", onKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="si-drawer-root" role="presentation">
      <button
        type="button"
        className="si-drawer-root__backdrop"
        aria-label="Fechar painel"
        onClick={onClose}
      />

      <aside
        className={`si-drawer si-drawer--${size}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={description ? descriptionId : undefined}
      >
        <header className="si-drawer__header">
          <div className="si-drawer__header-text">
            <h2 id={titleId} className="si-drawer__title">
              {title}
            </h2>
            {description ? (
              <p id={descriptionId} className="si-drawer__description">
                {description}
              </p>
            ) : null}
          </div>

          <button
            type="button"
            className="si-drawer__close"
            aria-label="Fechar"
            onClick={onClose}
          >
            ×
          </button>
        </header>

        <div className="si-drawer__body">{children}</div>

        {footer ? <footer className="si-drawer__footer">{footer}</footer> : null}
      </aside>
    </div>
  );
}
