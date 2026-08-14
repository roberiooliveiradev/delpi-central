import type { MouseEvent, MouseEventHandler, ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";
import { isSafeNavigationHref } from "../layout/PagePath";

export type InlineNavLinkClassNames = {
  root: string;
};

export type InlineNavLinkProps = {
  href: string;
  /** Indicação do destino (tooltip nativo + default de aria-label). */
  title: string;
  children: ReactNode;
  className?: string;
  classNames: InlineNavLinkClassNames;
  onNavigate?: MouseEventHandler<HTMLAnchorElement>;
  /** Default: `title`. */
  "aria-label"?: string;
  /** Default true — evita disparar row click da tabela. */
  stopPropagation?: boolean;
};

export function inlineNavLinkBemClasses(prefix: string): InlineNavLinkClassNames {
  return {
    root: delpiUiClass(`${prefix}-inline-nav-link`, "delpi-ui-inline-nav-link"),
  };
}

function requireSafeHref(href: string): string {
  if (!isSafeNavigationHref(href)) {
    throw new Error("InlineNavLink recebeu um href que não é interno ao host.");
  }
  return href.trim();
}

/** Left-click limpo: SPA. Modificadores / middle-click: comportamento nativo do browser. */
export function shouldHandleInlineNavClick(event: MouseEvent<HTMLAnchorElement>): boolean {
  if (event.defaultPrevented) return false;
  if (event.button !== 0) return false;
  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return false;
  return true;
}

/**
 * Anchor de navegação SPA sem skin visual — o consumidor passa `className`.
 * CSS: `styles/inline-nav-link.css` (reset mínimo de UA).
 */
export function InlineNavLink({
  href,
  title,
  children,
  className,
  classNames,
  onNavigate,
  "aria-label": ariaLabel,
  stopPropagation = true,
}: InlineNavLinkProps) {
  const safeHref = requireSafeHref(href);
  const resolvedTitle = title.trim();
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");

  return (
    <a
      className={rootClass}
      href={safeHref}
      title={resolvedTitle}
      aria-label={(ariaLabel ?? resolvedTitle).trim() || undefined}
      onClick={(event) => {
        if (stopPropagation) {
          event.stopPropagation();
        }
        if (!shouldHandleInlineNavClick(event)) {
          return;
        }
        if (!onNavigate) {
          return;
        }
        event.preventDefault();
        onNavigate(event);
      }}
    >
      {children}
    </a>
  );
}

export type DashboardInlineNavLinkProps = Omit<InlineNavLinkProps, "classNames">;

export function createDashboardInlineNavLink(prefix: string) {
  const classNames = inlineNavLinkBemClasses(prefix);

  return function DashboardInlineNavLink(props: DashboardInlineNavLinkProps) {
    return <InlineNavLink classNames={classNames} {...props} />;
  };
}
