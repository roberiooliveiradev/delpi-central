import { Building2, FolderTree, Share2 } from "lucide-react";
import { NavigationCard, SectionCard, navigationCardBemClasses, sectionCardPacBemClasses } from "@delpi/plugin-ui/index";

import type { AppProps } from "../../App";
import { PageHeader } from "../../components/PageHeader";
import { TransformometroShell } from "../../components/TransformometroShell";
import { PORTAL_ADMIN_LINKS, PORTAL_PAGE_COPY } from "../../constants/portalExperience";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";

const SECTION = sectionCardPacBemClasses("ds");
const NAV_CARD = navigationCardBemClasses("ds");
const SECTION_LABELS = {
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
};

const SETTINGS_ICONS = {
  units: Building2,
  departments: FolderTree,
  resources: Share2,
} as const;

type AdministrationPageProps = Pick<AppProps, "pathname"> & {
  onNavigate: (path: string) => void;
};

export function AdministrationPage({ pathname, onNavigate }: AdministrationPageProps) {
  const settings = PORTAL_ADMIN_LINKS.filter((link) => link.id !== "data");

  return (
    <TransformometroShell>
      <PageHeader
        eyebrow={PORTAL_PAGE_COPY.administration.eyebrow}
        title={PORTAL_PAGE_COPY.administration.title}
        subtitle={PORTAL_PAGE_COPY.administration.description}
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.administration}
        onNavigate={onNavigate}
      />
      <div className="tm-portal-catalog">
        <SectionCard classNames={SECTION} labels={SECTION_LABELS} title="Configurações">
          <div className="tm-portal-nav-grid">
            {settings.map((link) => {
              const Icon = SETTINGS_ICONS[link.id as keyof typeof SETTINGS_ICONS];
              return (
                <NavigationCard
                  key={link.id}
                  classNames={NAV_CARD}
                  orientation="horizontal"
                  title={link.label}
                  description={link.description}
                  icon={Icon ? <Icon size={18} aria-hidden="true" /> : undefined}
                  onClick={() => onNavigate(link.path)}
                />
              );
            })}
          </div>
        </SectionCard>
      </div>
    </TransformometroShell>
  );
}
