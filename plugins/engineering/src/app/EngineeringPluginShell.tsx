import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  BarChart3,
  HelpCircle,
  House,
} from "lucide-react";

import {
  getDisplayNameFromAccessToken,
  getSubjectFromAccessToken,
} from "./authDisplayName";
import {
  buildEngineeringPath,
  navigateEngineeringView,
  type EngineeringView,
} from "./engineeringRoutes";
import {
  getFavoriteSnapshot,
  setFavoritesIdentity,
  subscribeFavorites,
  toggleFavorite,
} from "./favoritesStore";
import {
  findCatalogRoute,
  findCatalogRouteWithSection,
  HOME_COPY,
  searchCatalog,
  type CatalogRoute,
  type CatalogSection,
} from "../content/engineeringRouteCatalog";
import {
  getMyPersonProfile,
  getMyPersonProfilePhoto,
} from "../api/personProfileApi";
import {
  ENG_PORTAL_SCOPE,
  EngineeringCommandPalette,
  EngineeringTopBar,
  EngineeringTopBarFavoritesStrip,
  EngineeringTopBarSearchTrigger,
  EngineeringTopBarUserIdentity,
} from "../ui/engineeringUi";

type EngineeringPluginShellProps = {
  view: EngineeringView;
  basePath: string;
  sections: readonly CatalogSection[];
  getAccessToken?: () => string | undefined;
  onOpenRoute: (route: CatalogRoute) => void;
  children: ReactNode;
};

const NAV_ITEMS: readonly {
  id: EngineeringView;
  label: string;
  icon: ReactNode;
}[] = [
  { id: "home", label: "Início", icon: <House size={16} aria-hidden="true" /> },
  {
    id: "overview",
    label: "Visão geral",
    icon: <BarChart3 size={16} aria-hidden="true" />,
  },
  {
    id: "help",
    label: "Ajuda",
    icon: <HelpCircle size={16} aria-hidden="true" />,
  },
];

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  if (target.isContentEditable) return true;
  const tag = target.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT";
}

/** Favoritos → items da faixa na TopBar, com resolução de destino. */
function useFavoritesStrip(
  sections: readonly CatalogSection[],
  onOpenRoute: (route: CatalogRoute) => void,
) {
  const [favorites, setFavorites] = useState(getFavoriteSnapshot);
  useEffect(() => subscribeFavorites(setFavorites), []);

  const knownIds = useMemo(() => {
    const ids = new Set<string>();
    for (const section of sections) {
      for (const route of section.routes) ids.add(route.id);
    }
    return ids;
  }, [sections]);

  const items = favorites
    .filter((fav) => knownIds.has(fav.routeId))
    .map((fav) => ({
      id: fav.routeId,
      label: findCatalogRoute(fav.routeId)?.label ?? fav.routeId,
    }));

  const open = useCallback(
    (routeId: string) => {
      const route = findCatalogRoute(routeId);
      if (!route || route.comingSoon) return;
      if (!knownIds.has(routeId)) return;
      onOpenRoute(route);
    },
    [knownIds, onOpenRoute],
  );

  const remove = useCallback((routeId: string) => {
    toggleFavorite(routeId);
  }, []);

  return { items, open, remove };
}

/** Identidade visual — display name lido do JWT do host (apresentação
 * apenas; autorização permanece na Core). */
function useDisplayName(
  getAccessToken?: () => string | undefined,
): { name: string | null; subject: string | null } {
  const [identity] = useState<{ name: string | null; subject: string | null }>(
    () => {
      const token = getAccessToken?.();
      return {
        name: getDisplayNameFromAccessToken(token),
        subject: getSubjectFromAccessToken(token),
      };
    },
  );
  useEffect(() => {
    setFavoritesIdentity(identity.subject);
  }, [identity.subject]);
  return identity;
}

/** Foto oficial do perfil (Core `/me/person-profile`) como objectURL —
 * mesmo contrato que o Comercial consome via commercial-api. Falha em
 * qualquer etapa degrada para iniciais; revogação e abort isolam a
 * identidade entre sessões/remontagens. */
function useAvatarPhoto(subject: string | null): string | null {
  const [objectUrl, setObjectUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!subject) return undefined;
    let revoked: string | null = null;
    const controller = new AbortController();
    void getMyPersonProfile(controller.signal)
      .then(async (profile) => {
        if (controller.signal.aborted || !profile?.has_photo) return;
        const blob = await getMyPersonProfilePhoto(controller.signal);
        if (controller.signal.aborted) return;
        revoked = URL.createObjectURL(blob);
        setObjectUrl(revoked);
      })
      .catch(() => {
        /* Foto é melhoria progressiva — falha mantém iniciais. */
      });
    return () => {
      controller.abort();
      setObjectUrl(null);
      if (revoked) URL.revokeObjectURL(revoked);
    };
  }, [subject]);

  return objectUrl;
}

export function EngineeringPluginShell({
  view,
  basePath,
  sections,
  getAccessToken,
  onOpenRoute,
  children,
}: EngineeringPluginShellProps) {
  const copy = HOME_COPY.topbar;
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [paletteQuery, setPaletteQuery] = useState("");
  const searchTriggerRef = useRef<HTMLButtonElement>(null);
  const { name: displayName, subject } = useDisplayName(getAccessToken);
  const avatarUrl = useAvatarPhoto(subject);
  const favoritesStrip = useFavoritesStrip(sections, onOpenRoute);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const isPaletteChord =
        (event.key === "k" || event.key === "K") &&
        (event.metaKey || event.ctrlKey);
      if (!isPaletteChord) return;
      if (isEditableTarget(event.target) && !paletteOpen) return;
      event.preventDefault();
      setPaletteOpen((open) => !open);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [paletteOpen]);

  const paletteHits = useMemo(
    () => searchCatalog(paletteQuery, sections),
    [paletteQuery, sections],
  );

  const onSelectPaletteHit = useCallback(
    (routeId: string) => {
      const found = findCatalogRouteWithSection(routeId);
      if (!found || found.route.comingSoon) return;
      onOpenRoute(found.route);
      setPaletteOpen(false);
      setPaletteQuery("");
    },
    [onOpenRoute],
  );

  return (
    <div className={`${ENG_PORTAL_SCOPE} dashboard-page`}>
      <div className="engineering-page-stack">
        <EngineeringTopBar
          aria-label={copy.ariaLabel}
          activeId={view}
          collapsible
          portalScopeClassName={ENG_PORTAL_SCOPE}
          items={NAV_ITEMS.map((item) => ({
            id: item.id,
            label: item.label,
            icon: item.icon,
            title: item.label,
            onSelect: () =>
              navigateEngineeringView(item.id, { basePath }),
          }))}
          secondary={
            <>
              <EngineeringTopBarSearchTrigger
                ref={searchTriggerRef}
                onOpen={() => setPaletteOpen(true)}
                expanded={paletteOpen}
                label={copy.searchLabel}
                shortcutLabel={copy.searchShortcut}
                aria-label={copy.searchLabel}
              />
              <EngineeringTopBarFavoritesStrip
                items={favoritesStrip.items}
                onSelect={favoritesStrip.open}
                onRemove={favoritesStrip.remove}
                title={copy.favoritesTitle}
                emptyLabel={copy.favoritesEmpty}
                openAriaLabel={copy.favoritesOpenAria}
                closeAriaLabel={copy.favoritesCloseAria}
                removeLabel={copy.favoritesRemoveLabel}
                portalScopeClassName={ENG_PORTAL_SCOPE}
              />
            </>
          }
          actions={
            <EngineeringTopBarUserIdentity
              displayName={displayName}
              fallbackLabel={copy.identityFallback}
              href={buildEngineeringPath("home", basePath)}
              avatarUrl={avatarUrl}
              avatarHref="/profile"
              avatarTitle={displayName ?? undefined}
            />
          }
        />

        {children}
      </div>

      <EngineeringCommandPalette
        open={paletteOpen}
        onClose={() => {
          setPaletteOpen(false);
          setPaletteQuery("");
        }}
        anchorRef={searchTriggerRef}
        title={copy.searchLabel}
        value={paletteQuery}
        onChange={setPaletteQuery}
        hits={paletteHits}
        onSelectHit={onSelectPaletteHit}
        placeholder={HOME_COPY.features.searchPlaceholder}
        emptyHitsLabel={HOME_COPY.features.searchEmpty}
        clearLabel={HOME_COPY.features.clearSearch}
        portalScopeClassName={ENG_PORTAL_SCOPE}
      />
    </div>
  );
}
