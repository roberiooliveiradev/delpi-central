import { useEffect, useId, useRef, type ReactNode } from "react";
import { createPortal } from "react-dom";

export type DrawerShellClassNames = {
  root: string;
  backdrop: string;
  panel: string;
  header: string;
  title: string;
  closeButton: string;
  body: string;
  headerText?: string;
  description?: string;
  footer?: string;
};

export type DrawerShellProps = {
  open: boolean;
  title: string;
  description?: string;
  footer?: ReactNode;
  onClose: () => void;
  children: ReactNode;
  classNames: DrawerShellClassNames;
  className?: string;
  closeAriaLabel?: string;
  backdropAriaLabel?: string;
  /** Substitui o lock padrão (`document.body.style.overflow`). */
  lockPageScroll?: () => () => void;
};

export function drawerShellBemClasses(prefix: string): DrawerShellClassNames {
  return {
    root: `${prefix}-drawer-root`,
    backdrop: `${prefix}-drawer-root__backdrop`,
    panel: `${prefix}-drawer`,
    header: `${prefix}-drawer__header`,
    title: `${prefix}-drawer__title`,
    closeButton: `${prefix}-drawer__close`,
    body: `${prefix}-drawer__body`,
  };
}

export function DrawerShell({
  open,
  title,
  description,
  footer,
  onClose,
  children,
  classNames,
  className,
  closeAriaLabel = "Fechar",
  backdropAriaLabel = "Fechar painel",
  lockPageScroll,
}: DrawerShellProps) {
  const titleId = useId();
  const descriptionId = useId();
  const onCloseRef = useRef(onClose);
  const structuredHeader = Boolean(classNames.headerText);

  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    if (!open) {
      return;
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onCloseRef.current();
      }
    }

    window.addEventListener("keydown", handleKeyDown);

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
      window.removeEventListener("keydown", handleKeyDown);
      unlockPageScroll();
    };
  }, [open, lockPageScroll]);

  if (!open) {
    return null;
  }

  const panelClass = [classNames.panel, className].filter(Boolean).join(" ");

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

  return createPortal(
    <div className={classNames.root} role="presentation">
      <button
        type="button"
        className={classNames.backdrop}
        aria-label={backdropAriaLabel}
        onClick={onClose}
      />

      <aside
        className={panelClass}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={description && classNames.description ? descriptionId : undefined}
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

          <button
            type="button"
            className={classNames.closeButton}
            aria-label={closeAriaLabel}
            onClick={onClose}
          >
            ×
          </button>
        </header>

        <div className={classNames.body}>{children}</div>

        {footer && classNames.footer ? (
          <footer className={classNames.footer}>{footer}</footer>
        ) : null}
      </aside>
    </div>,
    document.body,
  );
}

export type DashboardDrawerShellProps = Omit<DrawerShellProps, "classNames">;

export function createDrawerShell(config: {
  prefix: string;
  closeAriaLabel?: string;
  backdropAriaLabel?: string;
  classNames?: Partial<DrawerShellClassNames>;
}) {
  const classNames: DrawerShellClassNames = {
    ...drawerShellBemClasses(config.prefix),
    ...config.classNames,
  };

  return function DashboardDrawerShell(props: DashboardDrawerShellProps) {
    return (
      <DrawerShell
        classNames={classNames}
        closeAriaLabel={config.closeAriaLabel}
        backdropAriaLabel={config.backdropAriaLabel}
        {...props}
      />
    );
  };
}
