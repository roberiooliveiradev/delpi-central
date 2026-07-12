import { X } from "lucide-react";
import { useEffect, useId, useRef, type ReactNode, type RefObject } from "react";
import { createPortal } from "react-dom";

import { useDelpiUiPortalTheme } from "../shape/useDelpiUiPortalTheme";

export type ModalShellClassNames = {
  overlay: string;
  dialog: string;
  header: string;
  title: string;
  closeButton: string;
  body: string;
  headerText?: string;
  description?: string;
  footer?: string;
  headerActions?: string;
};

export type ModalShellProps = {
  open: boolean;
  title: string;
  description?: string;
  footer?: ReactNode;
  headerActions?: ReactNode;
  onClose: () => void;
  children: ReactNode;
  classNames: ModalShellClassNames;
  className?: string;
  overlayClassName?: string;
  closeAriaLabel?: string;
  initialFocusSelector?: string;
  dialogRef?: RefObject<HTMLDivElement | null>;
  /** Substitui o lock padrão (`document.body.style.overflow`). */
  lockPageScroll?: () => () => void;
  overlayAriaHidden?: boolean;
  /**
   * Classe root do plugin MFE (ex.: `dashboard-tv-dashboard`).
   * Portais vão para `document.body` — sem este escopo o CSS do plugin não aplica.
   */
  portalScopeClassName?: string;
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
  description,
  footer,
  headerActions,
  onClose,
  children,
  classNames,
  className,
  overlayClassName,
  closeAriaLabel = "Fechar",
  initialFocusSelector,
  dialogRef,
  lockPageScroll,
  overlayAriaHidden = false,
  portalScopeClassName,
}: ModalShellProps) {
  const titleId = useId();
  const descriptionId = useId();
  const internalDialogRef = useRef<HTMLDivElement | null>(null);
  const resolvedDialogRef = dialogRef ?? internalDialogRef;
  const onCloseRef = useRef(onClose);
  const hasAutoFocusedRef = useRef(false);
  const structuredHeader = Boolean(classNames.headerText);
  const portalTheme = useDelpiUiPortalTheme(open);

  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    if (!open) {
      hasAutoFocusedRef.current = false;
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onCloseRef.current();
      }
    };

    document.addEventListener("keydown", handleKeyDown);

    const unlockPageScroll = lockPageScroll
      ? lockPageScroll()
      : (() => {
          const previousOverflow = document.body.style.overflow;
          document.body.style.overflow = "hidden";
          return () => {
            document.body.style.overflow = previousOverflow;
          };
        })();

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      unlockPageScroll();
      hasAutoFocusedRef.current = false;
    };
  }, [open, lockPageScroll]);

  useEffect(() => {
    if (!open || hasAutoFocusedRef.current) {
      return;
    }

    const rafId = requestAnimationFrame(() => {
      const dialog = resolvedDialogRef.current;
      if (!dialog) {
        return;
      }

      if (initialFocusSelector) {
        const focusTarget = dialog.querySelector<HTMLElement>(initialFocusSelector);
        if (focusTarget) {
          focusTarget.focus();
          hasAutoFocusedRef.current = true;
          return;
        }
      }

      const fallback = dialog.querySelector<HTMLElement>(
        "input, select, textarea, button, [tabindex]:not([tabindex='-1'])",
      );
      fallback?.focus();
      hasAutoFocusedRef.current = true;
    });

    return () => {
      cancelAnimationFrame(rafId);
    };
  }, [open, initialFocusSelector, resolvedDialogRef]);

  if (!open) {
    return null;
  }

  const dialogClass = [classNames.dialog, className].filter(Boolean).join(" ");
  const overlayClass = [overlayClassName, classNames.overlay].filter(Boolean).join(" ");
  const scopeClass = [portalScopeClassName, portalTheme.hostClassName].filter(Boolean).join(" ");

  const titleNode = (
    <h2 id={titleId} className={classNames.title}>
      {title}
    </h2>
  );

  const descriptionNode =
    description && classNames.description ? (
      <p id={descriptionId} className={classNames.description}>
        {description}
      </p>
    ) : null;

  const overlay = (
    <div
      className={overlayClass}
      onClick={onClose}
      aria-hidden={overlayAriaHidden ? true : undefined}
    >
      <div
        ref={resolvedDialogRef}
        className={dialogClass}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={description && classNames.description ? descriptionId : undefined}
        onClick={(event) => event.stopPropagation()}
      >
        <header className={classNames.header}>
          {structuredHeader ? (
            <div className={classNames.headerText}>
              {titleNode}
              {descriptionNode}
            </div>
          ) : (
            <>
              {titleNode}
              {descriptionNode}
            </>
          )}
          {headerActions && classNames.headerActions ? (
            <div className={classNames.headerActions}>{headerActions}</div>
          ) : null}
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
        {footer && classNames.footer ? <div className={classNames.footer}>{footer}</div> : null}
      </div>
    </div>
  );

  return createPortal(
    <div className={scopeClass} style={portalTheme.style} data-theme={portalTheme.dataTheme ?? undefined}>
      {overlay}
    </div>,
    document.body,
  );
}

export type DashboardModalShellProps = Omit<
  ModalShellProps,
  "classNames" | "overlayClassName" | "portalScopeClassName"
>;

export function createModalShell(config: {
  prefix: string;
  overlayClassName?: string;
  closeAriaLabel?: string;
  /** Escopo CSS do MFE para portais no body — ver `portalScopeClassName` em ModalShell. */
  portalScopeClassName?: string;
}) {
  const classNames = modalShellBemClasses(config.prefix);

  return function DashboardModalShell(props: DashboardModalShellProps) {
    return (
      <ModalShell
        classNames={classNames}
        overlayClassName={config.overlayClassName}
        closeAriaLabel={config.closeAriaLabel}
        portalScopeClassName={config.portalScopeClassName}
        {...props}
      />
    );
  };
}
