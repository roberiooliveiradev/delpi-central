import { BarChart3, BookOpen, ClipboardList, FileText, List, Settings } from "lucide-react";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  CatalogSearchBar,
  EmptyState,
  EventsSection,
  RecentAccessStrip,
  SectionCard,
  SectionRouteCard,
  alertQueueBemClasses,
  catalogSearchBarBemClasses,
  emptyStateCardBemClasses,
  hubChipRowBemClasses,
  routeChipBemClasses,
  sectionCardPacBemClasses,
  sectionRouteCardBemClasses,
} from "@delpi/plugin-ui/index";

import type { AppProps } from "../../App";
import { PageHeader } from "../../components/PageHeader";
import { TransformometroShell } from "../../components/TransformometroShell";
import { PORTAL_PAGE_COPY, filterPortalCatalog, visiblePortalLauncherGroups } from "../../constants/portalExperience";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import { useCanManagePortal } from "../../state/portalChrome";
import {
  subscribePortalFavorites,
  togglePortalFavorite,
  visiblePortalFavorites,
  type PortalFavoriteItem,
} from "../../state/portalFavorites";
import {
  subscribePortalRecentAccess,
  visiblePortalRecentAccess,
  type PortalRecentAccessItem,
} from "../../state/portalRecentAccess";
import { usePortalGreeting } from "./usePortalGreeting";
import { usePortalHomeSignals } from "./usePortalHomeSignals";

const SECTION = sectionCardPacBemClasses("ds");
const ROUTE_CARD = sectionRouteCardBemClasses("ds");
const SEARCH = catalogSearchBarBemClasses("ds");
const EMPTY = emptyStateCardBemClasses("ds");
const EVENTS = {
  section: SECTION,
  queue: alertQueueBemClasses("ds"),
};
const RECENTS = {
  row: hubChipRowBemClasses("ds"),
  chip: routeChipBemClasses("ds"),
};
const SECTION_LABELS = {
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
};

const GROUP_ICONS: Record<string, ReactNode> = {
  management: <BarChart3 size={20} strokeWidth={1.75} aria-hidden="true" />,
  operation: <ClipboardList size={20} strokeWidth={1.75} aria-hidden="true" />,
  processes: <List size={20} strokeWidth={1.75} aria-hidden="true" />,
  records: <FileText size={20} strokeWidth={1.75} aria-hidden="true" />,
  administration: <Settings size={20} strokeWidth={1.75} aria-hidden="true" />,
  help: <BookOpen size={20} strokeWidth={1.75} aria-hidden="true" />,
};

type PortalHomePageProps = Pick<AppProps, "pathname" | "getAccessToken"> & {
  onNavigate: (path: string) => void;
};

export function PortalHomePage({ pathname, getAccessToken, onNavigate }: PortalHomePageProps) {
  const [query, setQuery] = useState("");
  const [favorites, setFavorites] = useState<PortalFavoriteItem[]>([]);
  const [recents, setRecents] = useState<PortalRecentAccessItem[]>([]);
  const needle = query.trim().toLowerCase();
  const canManage = useCanManagePortal();
  const visibleFavorites = visiblePortalFavorites(favorites, canManage);
  const visibleRecents = visiblePortalRecentAccess(recents, canManage);
  const favoritePaths = useMemo(() => new Set(visibleFavorites.map((item) => item.path)), [visibleFavorites]);
  const { highlights, events } = usePortalHomeSignals(getAccessToken);
  const greeting = usePortalGreeting(getAccessToken);

  useEffect(() => subscribePortalFavorites(setFavorites), []);
  useEffect(() => subscribePortalRecentAccess(setRecents), []);

  const groups = useMemo(
    () =>
      visiblePortalLauncherGroups(canManage)
        .map((group) => ({
          ...group,
          links: group.links.filter((link) =>
            needle
              ? `${group.title} ${group.description} ${link.label} ${link.description}`
                  .toLowerCase()
                  .includes(needle)
              : true,
          ),
        }))
        .filter((group) => group.links.length > 0),
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
        title={greeting}
        subtitle={PORTAL_PAGE_COPY.home.description}
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.home}
        onNavigate={onNavigate}
        highlights={highlights}
      />
      <EventsSection
        classNames={EVENTS}
        labels={SECTION_LABELS}
        title="Eventos e interações"
        subtitle="Sinais já disponíveis no programa de transformação."
        items={events.map((event) => ({
          ...event,
          actionLabel: "Ver na Visão geral",
          onAction: () => onNavigate(TRANSFORMOMETRO_ROUTES.dashboard),
        }))}
        listAriaLabel="Eventos e interações do Portal Transforma+"
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
          <RecentAccessStrip
            classNames={RECENTS}
            label="Últimos acessos"
            items={visibleRecents.map((item) => ({
              id: item.path,
              label: item.label,
            }))}
            onSelect={(id: string) => onNavigate(id)}
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
                    pinned: favoritePaths.has(link.path),
                    pinLabel: "Adicionar aos favoritos",
                    unpinLabel: "Remover dos favoritos",
                    onPinClick: () => togglePortalFavorite({ path: link.path, label: link.label }),
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
