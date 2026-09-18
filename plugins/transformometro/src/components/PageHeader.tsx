import type { ReactNode } from "react";
import { RefreshCw } from "lucide-react";
import { PageHero, pageHeroBemClasses } from "@delpi/plugin-ui/index";

import { PORTAL_PRODUCT_NAME } from "../constants/portalExperience";
import { DS_GHOST_BTN } from "./ghostChrome";
import { PortalTopBar } from "./TransformometroNav";
import "./PageHeader.css";

type PageHeaderProps = {
  title: string;
  subtitle: string;
  eyebrow?: string;
  currentPath?: string;
  onNavigate: (path: string) => void;
  onRefresh?: () => void;
  refreshing?: boolean;
  actions?: ReactNode;
  children?: ReactNode;
};

const HERO = pageHeroBemClasses("ds");

export function PageHeader({
  title,
  subtitle,
  eyebrow = PORTAL_PRODUCT_NAME,
  currentPath,
  onNavigate,
  onRefresh,
  refreshing = false,
  actions,
  children,
}: PageHeaderProps) {
  return (
    <>
      <PortalTopBar currentPath={currentPath} onNavigate={onNavigate} />
      <PageHero
        classNames={HERO}
        density="compact"
        eyebrow={eyebrow}
        title={title}
        description={subtitle}
        actions={
          <>
            {onRefresh ? (
              <button
                type="button"
                className={DS_GHOST_BTN}
                onClick={onRefresh}
                disabled={refreshing}
              >
                <RefreshCw size={16} aria-hidden="true" />
                {refreshing ? "Atualizando…" : "Atualizar"}
              </button>
            ) : null}
            {actions}
          </>
        }
      >
        {children}
      </PageHero>
    </>
  );
}
