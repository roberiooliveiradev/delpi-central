import { useEffect, useId, useRef } from "react";
import type { PropsWithChildren, ReactNode } from "react";
import { X } from "lucide-react";

type ModalSize = "sm" | "md" | "lg" | "xl";

type ModalProps = PropsWithChildren<{
  open: boolean;
  title: string;
  description?: string;
  footer?: ReactNode;
  onClose: () => void;
  size?: ModalSize;
  initialFocusSelector?: string;
}>;

export function Modal({
  open,
  title,
  description,
  children,
  footer,
  onClose,
  size = "md",
  initialFocusSelector,
}: ModalProps) {
  const titleId = useId();
  const descriptionId = useId();
  const dialogRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) return;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    document.addEventListener("keydown", handleKeyDown);

    requestAnimationFrame(() => {
      if (initialFocusSelector) {
        const focusTarget = dialogRef.current?.querySelector<HTMLElement>(
          initialFocusSelector,
        );
        if (focusTarget) {
          focusTarget.focus();
          return;
        }
      }

      const fallback = dialogRef.current?.querySelector<HTMLElement>(
        "button, input, select, textarea, [tabindex]:not([tabindex='-1'])",
      );
      fallback?.focus();
    });

    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open, onClose, initialFocusSelector]);

  if (!open) return null;

  return (
    <div
      className="si-modal-overlay"
      onClick={onClose}
      aria-hidden="true"
    >
      <div
        ref={dialogRef}
        className={`si-modal si-modal--${size}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={description ? descriptionId : undefined}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="si-modal__header">
          <div className="si-modal__header-text">
            <h2 id={titleId} className="si-modal__title">
              {title}
            </h2>
            {description ? (
              <p id={descriptionId} className="si-modal__description">
                {description}
              </p>
            ) : null}
          </div>

          <button
            type="button"
            className="si-modal__close"
            onClick={onClose}
            aria-label="Fechar janela"
          >
            <X size={18} />
          </button>
        </div>

        <div className="si-modal__body">{children}</div>

        {footer ? <div className="si-modal__footer">{footer}</div> : null}
      </div>
    </div>
  );
}