import type { MouseEventHandler, ReactNode } from "react";
import { createDashboardInlineNavLink } from "@delpi/plugin-ui/index";

import { navigatePluginPath } from "../app/pluginNavigation";

const BaseLink = createDashboardInlineNavLink("cm");

export type CommercialEntityLinkProps = {
  href: string;
  /** Indicação nativa do destino («Abrir…»). */
  title: string;
  children: ReactNode;
  className?: string;
  "aria-label"?: string;
  stopPropagation?: boolean;
  onNavigate?: MouseEventHandler<HTMLAnchorElement>;
};

/**
 * Link de entidade do Portal Comercial — `<a href>` real + SPA same-tab.
 * Visual vem só de `className` (ex.: `cm-link-button`).
 */
export function CommercialEntityLink({
  href,
  title,
  children,
  className,
  "aria-label": ariaLabel,
  stopPropagation = true,
  onNavigate,
}: CommercialEntityLinkProps) {
  return (
    <BaseLink
      href={href}
      title={title}
      className={className}
      aria-label={ariaLabel}
      stopPropagation={stopPropagation}
      onNavigate={
        onNavigate ??
        (() => {
          navigatePluginPath(href);
        })
      }
    >
      {children}
    </BaseLink>
  );
}
