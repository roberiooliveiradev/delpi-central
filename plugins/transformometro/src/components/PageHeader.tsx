import type { ReactNode } from "react";
import { RefreshCw } from "lucide-react";
import { PageHero, pageHeroBemClasses, LoadingActivityBadge, type PageHeroHighlight } from "@delpi/plugin-ui/index";

import { PORTAL_PRODUCT_NAME } from "../constants/portalExperience";
import { DS_GHOST_BTN } from "./ghostChrome";
import "./PageHeader.css";

type PageHeaderProps = {
  title: ReactNode;
  subtitle: ReactNode;
  eyebrow?: ReactNode;
  lead?: ReactNode;
  /** @deprecated TopBar do portal vive no App; mantido só por compatibilidade de call sites. */
  currentPath?: string;
  /** @deprecated TopBar do portal vive no App; mantido só por compatibilidade de call sites. */
  onNavigate?: (path: string) => void;
  onRefresh?: () => void;
  refreshing?: boolean;
  actions?: ReactNode;
  badge?: ReactNode;
  highlights?: PageHeroHighlight[];
  children?: ReactNode;
};

const HERO = pageHeroBemClasses("ds");

export function PageHeader({
  title,
  subtitle,
  eyebrow = PORTAL_PRODUCT_NAME,
  lead,
  onRefresh,
  refreshing = false,
  actions,
  badge,
  highlights,
  children,
}: PageHeaderProps) {
  return (
    <>
      {lead}
      <PageHero
        classNames={HERO}
        density="compact"
        eyebrow={eyebrow}
        title={title}
        description={subtitle}
        badge={badge}
        highlights={highlights}
        actions={
          <>
            {onRefresh ? (
              <button
                type="button"
                className={DS_GHOST_BTN}
                onClick={onRefresh}
                disabled={refreshing}
                aria-busy={refreshing || undefined}
              >
                <RefreshCw size={16} aria-hidden="true" />
                {refreshing ? "Atualizando…" : "Atualizar"}
              </button>
            ) : null}
            {refreshing ? <LoadingActivityBadge label="Atualizando…" /> : null}
            {actions}
          </>
        }
      >
        {children}
      </PageHero>
    </>
  );
}
