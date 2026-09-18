import { ArrowDownUp, FileText, LayoutDashboard, List, Settings } from "lucide-react";
import { useMemo, useState } from "react";
import {
  FieldLabel,
  NativeTextControl,
  NavigationCard,
  SectionCard,
  navigationCardBemClasses,
  sectionCardPacBemClasses,
} from "@delpi/plugin-ui/index";

import type { AppProps } from "../../App";
import { PageHeader } from "../../components/PageHeader";
import { TransformometroShell } from "../../components/TransformometroShell";
import { PORTAL_LAUNCHER_GROUPS, PORTAL_PAGE_COPY } from "../../constants/portalExperience";
import { useCanManagePortal } from "../../state/portalChrome";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";

const SECTION = sectionCardPacBemClasses("ds");
const NAV_CARD = navigationCardBemClasses("ds");
const SECTION_LABELS = {
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
};

const LINK_ICONS = {
  overview: LayoutDashboard,
  processes: List,
  "meeting-minutes": FileText,
  data: ArrowDownUp,
  administration: Settings,
} as const;

type PortalHomePageProps = Pick<AppProps, "pathname"> & {
  onNavigate: (path: string) => void;
};

export function PortalHomePage({ pathname, onNavigate }: PortalHomePageProps) {
  const [query, setQuery] = useState("");
  const needle = query.trim().toLowerCase();
  const canManage = useCanManagePortal();
  const groups = useMemo(
    () =>
      PORTAL_LAUNCHER_GROUPS.map((group) => ({
        ...group,
        links: group.links.filter((link) => {
          if (!canManage && link.id === "administration") return false;
          return needle
            ? `${group.title} ${link.label} ${link.description}`.toLowerCase().includes(needle)
            : true;
        }),
      })).filter((group) => group.links.length > 0),
    [canManage, needle],
  );

  return (
    <TransformometroShell>
      <PageHeader
        eyebrow={PORTAL_PAGE_COPY.home.eyebrow}
        title={PORTAL_PAGE_COPY.home.title}
        subtitle={PORTAL_PAGE_COPY.home.description}
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.home}
        onNavigate={onNavigate}
      />
      <section className="tm-portal-catalog" aria-label="Caminhos e funcionalidades">
        <div className="tm-portal-catalog__search">
          <FieldLabel className="tm-field__label" label="Caminhos e funcionalidades" />
          <NativeTextControl
            id="tm-portal-catalog-search"
            type="search"
            placeholder="Buscar caminhos e funcionalidades…"
            value={query}
            onChange={setQuery}
          />
        </div>
        <div className="ds-shortcuts-grid">
          {groups.map((group) => (
            <SectionCard
              key={group.id}
              classNames={SECTION}
              labels={SECTION_LABELS}
              title={group.title}
            >
              <div className="tm-portal-nav-grid">
                {group.links.map((link) => {
                  const Icon = LINK_ICONS[link.id as keyof typeof LINK_ICONS];
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
          ))}
        </div>
        {groups.length === 0 ? (
          <p className="ds-hint">Nenhuma funcionalidade encontrada.</p>
        ) : null}
      </section>
    </TransformometroShell>
  );
}
