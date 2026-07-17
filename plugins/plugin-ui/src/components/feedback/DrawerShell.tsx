import { useEffect, useId, useRef, type ReactNode } from "react";
import { createPortal } from "react-dom";

import { delpiUiClass } from "../../utils/delpiUiClass";
import { useDelpiUiPortalTheme } from "../shape/useDelpiUiPortalTheme";

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
  /**
   * Classe root do plugin MFE (ex.: `dashboard-estoque-seguranca`).
   * Portais vão para `document.body` — sem este escopo o CSS do plugin não aplica.
   */
  portalScopeClassName?: string;
};

export function drawerShellBemClasses(prefix: string): DrawerShellClassNames {
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(`${prefix}-drawer-root`, "delpi-ui-drawer-root"),
    backdrop: pair(`${prefix}-drawer-root__backdrop`, "delpi-ui-drawer-root__backdrop"),
    panel: pair(`${prefix}-drawer`, "delpi-ui-drawer"),
    header: pair(`${prefix}-drawer__header`, "delpi-ui-drawer__header"),
    title: pair(`${prefix}-drawer__title`, "delpi-ui-drawer__title"),
    closeButton: pair(`${prefix}-drawer__close`, "delpi-ui-drawer__close"),
    body: pair(`${prefix}-drawer__body`, "delpi-ui-drawer__body"),
    headerText: pair(`${prefix}-drawer__header-text`, "delpi-ui-drawer__header-text"),
    description: pair(`${prefix}-drawer__description`, "delpi-ui-drawer__description"),
    footer: pair(`${prefix}-drawer__footer`, "delpi-ui-drawer__footer"),
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
  portalScopeClassName,
}: DrawerShellProps) {
  const titleId = useId();
  const descriptionId = useId();
  const onCloseRef = useRef(onClose);
  const panelRef = useRef<HTMLElement | null>(null);
  const structuredHeader = Boolean(classNames.headerText);
  const portalTheme = useDelpiUiPortalTheme(open);

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

    const rafId = requestAnimationFrame(() => {
      const focusTarget = panelRef.current?.querySelector<HTMLElement>(
        "button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])",
      );
      focusTarget?.focus();
    });

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      unlockPageScroll();
      cancelAnimationFrame(rafId);
    };
  }, [open, lockPageScroll]);

  if (!open) {
    return null;
  }

  const panelClass = [classNames.panel, className].filter(Boolean).join(" ");
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

  return createPortal(
    <div className={scopeClass} style={portalTheme.style} data-theme={portalTheme.dataTheme ?? undefined}>
      <div className={classNames.root} role="presentation">
        <button
          type="button"
          className={classNames.backdrop}
          aria-label={backdropAriaLabel}
          onClick={onClose}
        />

        <aside
          ref={panelRef}
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
      </div>
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
  portalScopeClassName?: string;
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
        portalScopeClassName={config.portalScopeClassName}
        {...props}
      />
    );
  };
}
