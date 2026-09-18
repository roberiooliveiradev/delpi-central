import { BarChart3, BookOpen, FileText, List, Settings } from "lucide-react";
import { useMemo, useState, type ReactNode } from "react";
import {
  CatalogSearchBar,
  EmptyState,
  SectionCard,
  SectionRouteCard,
  catalogSearchBarBemClasses,
  emptyStateCardBemClasses,
  sectionCardPacBemClasses,
  sectionRouteCardBemClasses,
} from "@delpi/plugin-ui/index";

import type { AppProps } from "../../App";
import { PageHeader } from "../../components/PageHeader";
import { TransformometroShell } from "../../components/TransformometroShell";
import { PORTAL_LAUNCHER_GROUPS, PORTAL_PAGE_COPY, filterPortalCatalog } from "../../constants/portalExperience";
import { useCanManagePortal } from "../../state/portalChrome";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";

const SECTION = sectionCardPacBemClasses("ds");
const ROUTE_CARD = sectionRouteCardBemClasses("ds");
const SEARCH = catalogSearchBarBemClasses("ds");
const EMPTY = emptyStateCardBemClasses("ds");
const SECTION_LABELS = {
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
};

const GROUP_ICONS: Record<string, ReactNode> = {
  management: <BarChart3 size={20} strokeWidth={1.75} aria-hidden="true" />,
  processes: <List size={20} strokeWidth={1.75} aria-hidden="true" />,
  records: <FileText size={20} strokeWidth={1.75} aria-hidden="true" />,
  administration: <Settings size={20} strokeWidth={1.75} aria-hidden="true" />,
  help: <BookOpen size={20} strokeWidth={1.75} aria-hidden="true" />,
};

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
            ? `${group.title} ${group.description} ${link.label} ${link.description}`
                .toLowerCase()
                .includes(needle)
            : true;
        }),
      })).filter((group) => group.links.length > 0),
    [canManage, needle],
  );
  const hits = useMemo(
    () =>
      filterPortalCatalog(query, { includeAdministration: canManage }).map((item) => ({
        id: item.path,
        label: item.label,
        groupLabel: item.group,
      })),
    [canManage, query],
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
      <SectionCard
        classNames={SECTION}
        labels={SECTION_LABELS}
        title="Caminhos e funcionalidades"
        subtitle="Busque ou abra uma funcionalidade do portal."
      >
        <div className="tm-home-paths">
          <CatalogSearchBar
            classNames={SEARCH}
            value={query}
            onChange={setQuery}
            hits={hits}
            onSelectHit={(id) => onNavigate(id)}
            placeholder="Buscar caminhos e funcionalidades…"
            clearLabel="Limpar busca"
            emptyHitsLabel="Nenhuma funcionalidade encontrada."
            aria-label="Buscar caminhos e funcionalidades"
          />
          {groups.length === 0 ? (
            <EmptyState classNames={EMPTY} defaultMessage="Nenhuma funcionalidade encontrada." />
          ) : (
            <div className="tm-home-sections-grid" aria-label="Caminhos e funcionalidades">
              {groups.map((group) => (
                <SectionRouteCard
                  key={group.id}
                  classNames={ROUTE_CARD}
                  title={group.title}
                  description={group.description}
                  icon={GROUP_ICONS[group.id]}
                  routes={group.links.map((link) => ({
                    id: link.id,
                    label: link.label,
                    onClick: () => onNavigate(link.path),
                  }))}
                />
              ))}
            </div>
          )}
        </div>
      </SectionCard>
    </TransformometroShell>
  );
}
