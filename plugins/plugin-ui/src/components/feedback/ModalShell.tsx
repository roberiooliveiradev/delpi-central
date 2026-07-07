import { X } from "lucide-react";
import { useEffect, useId, type ReactNode } from "react";
import { createPortal } from "react-dom";

export type ModalShellClassNames = {
  overlay: string;
  dialog: string;
  header: string;
  title: string;
  closeButton: string;
  body: string;
};

export type ModalShellProps = {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
  classNames: ModalShellClassNames;
  className?: string;
  overlayClassName?: string;
  closeAriaLabel?: string;
};

export function modalShellBemClasses(prefix: string): ModalShellClassNames {
  return {
    overlay: `${prefix}-modal-overlay`,
    dialog: `${prefix}-modal`,
    header: `${prefix}-modal__header`,
    title: `${prefix}-modal__title`,
    closeButton: `${prefix}-ghost-btn ${prefix}-ghost-btn--icon ${prefix}-modal__close`,
    body: `${prefix}-modal__body`,
  };
}

export function ModalShell({
  open,
  title,
  onClose,
  children,
  classNames,
  className,
  overlayClassName,
  closeAriaLabel = "Fechar",
}: ModalShellProps) {
  const titleId = useId();

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

  const dialogClass = [classNames.dialog, className].filter(Boolean).join(" ");
  const overlayClass = [overlayClassName, classNames.overlay].filter(Boolean).join(" ");

  return createPortal(
    <div className={overlayClass} onClick={onClose}>
      <div
        className={dialogClass}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(event) => event.stopPropagation()}
      >
        <header className={classNames.header}>
          <h2 id={titleId} className={classNames.title}>
            {title}
          </h2>
          <button
            type="button"
            className={classNames.closeButton}
            aria-label={closeAriaLabel}
            onClick={onClose}
          >
            <X size={18} aria-hidden="true" />
          </button>
        </header>
        <div className={classNames.body}>{children}</div>
      </div>
    </div>,
    document.body,
  );
}

export type DashboardModalShellProps = Omit<ModalShellProps, "classNames" | "overlayClassName">;

export function createModalShell(config: {
  prefix: string;
  overlayClassName?: string;
  closeAriaLabel?: string;
}) {
  const classNames = modalShellBemClasses(config.prefix);

  return function DashboardModalShell(props: DashboardModalShellProps) {
    return (
      <ModalShell
        classNames={classNames}
        overlayClassName={config.overlayClassName}
        closeAriaLabel={config.closeAriaLabel}
        {...props}
      />
    );
  };
}
