import { ArrowDownUp, FileText, LayoutDashboard, List, Settings } from "lucide-react";
import { NavigationCard, navigationCardBemClasses } from "@delpi/plugin-ui/index";

import type { AppProps } from "../../App";
import { PageHeader } from "../../components/PageHeader";
import { TransformometroShell } from "../../components/TransformometroShell";
import {
  PORTAL_HOME_LINKS,
  PORTAL_HOME_SUBTITLE,
  PORTAL_PRODUCT_NAME,
  PORTAL_WELCOME,
} from "../../constants/portalExperience";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";

const NAV_CARD = navigationCardBemClasses("ds");

const HOME_ICONS: Record<string, typeof List> = {
  [TRANSFORMOMETRO_ROUTES.processes]: List,
  [TRANSFORMOMETRO_ROUTES.dashboard]: LayoutDashboard,
  [TRANSFORMOMETRO_ROUTES.meetingMinutes]: FileText,
  [TRANSFORMOMETRO_ROUTES.settingsUnits]: Settings,
  [TRANSFORMOMETRO_ROUTES.data]: ArrowDownUp,
};

type PortalHomePageProps = Pick<AppProps, "pathname"> & {
  onNavigate: (path: string) => void;
};

export function PortalHomePage({ pathname, onNavigate }: PortalHomePageProps) {
  return (
    <TransformometroShell>
      <PageHeader
        title={PORTAL_PRODUCT_NAME}
        subtitle={PORTAL_HOME_SUBTITLE}
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.home}
        onNavigate={onNavigate}
      />
      <p className="ds-hint">{PORTAL_WELCOME}</p>
      <section className="ds-shortcuts-grid" aria-label="Caminhos e funcionalidades">
        {PORTAL_HOME_LINKS.map((link) => {
          const Icon = HOME_ICONS[link.path] ?? List;
          return (
            <NavigationCard
              key={link.path}
              classNames={NAV_CARD}
              title={link.label}
              description={link.description}
              icon={<Icon size={22} strokeWidth={1.75} />}
              onClick={() => onNavigate(link.path)}
            />
          );
        })}
      </section>
    </TransformometroShell>
  );
}
