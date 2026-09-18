import { Settings } from "lucide-react";
import { SectionRouteCard, sectionRouteCardBemClasses } from "@delpi/plugin-ui/index";

import type { AppProps } from "../../App";
import { PageHeader } from "../../components/PageHeader";
import { TransformometroShell } from "../../components/TransformometroShell";
import { PORTAL_ADMIN_LINKS, PORTAL_PAGE_COPY } from "../../constants/portalExperience";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";

const ROUTE_CARD = sectionRouteCardBemClasses("ds");

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
      <div className="tm-home-sections-grid">
        <SectionRouteCard
          classNames={ROUTE_CARD}
          title="Configurações"
          description="Unidades, departamentos e catálogo de recursos compartilhados."
          icon={<Settings size={20} strokeWidth={1.75} aria-hidden="true" />}
          routes={settings.map((link) => ({
            id: link.id,
            label: link.label,
            onClick: () => onNavigate(link.path),
          }))}
        />
      </div>
    </TransformometroShell>
  );
}
