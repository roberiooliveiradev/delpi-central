import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { Home, ListChecks } from "lucide-react";
import { formatPortalGreeting } from "@delpi/plugin-ui/index";
import { cfApiUrl, httpGetImageBlob } from "../api/httpClient";

import {
  collectSearchHits,
  findHubRouteById,
  HUB_CONTENT,
  resolveHubSections,
} from "../content/pluginRouteCatalog";
import { CF_HELP } from "../content/helpTooltips";
import { resolveShellNavItems, SHELL_NAV_CONTENT } from "../content/shellNav";
import { navigatePluginView } from "./pluginNavigation";
import { resolveActiveNavId, type PluginNavId, type PluginView } from "./pluginRoutes";
import { useViewerContext } from "./ViewerContext";
import {
  CF_PORTAL_SCOPE,
  CfCommandPalette,
  CfPageHero,
  CfStatusBadge,
  CfTitleWithHelp,
  CfTopBar,
  CfTopBarSearchTrigger,
  CfTopBarUserIdentity,
  CfTopBarUtilityCluster,
  CfViewTransition,
} from "./controllershipFinanceUi";

type PluginShellProps = {
  view: PluginView;
  basePath: string;
  children: ReactNode;
};

const NAV_ICONS: Record<PluginNavId, ReactNode> = {
  home: <Home size={16} strokeWidth={1.75} aria-hidden="true" />,
  dre_home: <Home size={16} strokeWidth={1.75} aria-hidden="true" />,
  my_tasks: <ListChecks size={16} strokeWidth={1.75} aria-hidden="true" />,
};

const NAV_HELP: Partial<Record<PluginNavId, string>> = {
  home: CF_HELP.shell.navHome,
  dre_home: CF_HELP.shell.navHome,
  my_tasks: CF_HELP.myTasks.page,
};

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  if (target.isContentEditable) return true;
  const tag = target.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT";
}

export function PluginShell({ view, basePath, children }: PluginShellProps) {
  const { viewer } = useViewerContext();
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!viewer?.capabilities.access) {
      setAvatarUrl(null);
      return;
    }
    const controller = new AbortController();
    let objectUrl: string | null = null;
    void httpGetImageBlob(cfApiUrl("/viewer-photo"), controller.signal)
      .then((blob) => {
        if (controller.signal.aborted || !blob) return;
        objectUrl = URL.createObjectURL(blob);
        setAvatarUrl(objectUrl);
      })
      .catch(() => {
        if (!controller.signal.aborted) setAvatarUrl(null);
      });
    return () => {
      controller.abort();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [viewer?.capabilities.access, viewer?.displayName]);

  const [paletteOpen, setPaletteOpen] = useState(false);
  const [paletteQuery, setPaletteQuery] = useState("");
  const searchTriggerRef = useRef<HTMLButtonElement>(null);

  const showManage = viewer?.capabilities.manage === true;
  const hasAccess =
    viewer === null || viewer.capabilities.access === true;
  const hasDreAccess = viewer?.capabilities.accessDre === true;

  // DRE-019/RW03 — navegação e busca são projeções das capabilities
  // efetivas: interno (`access`) e DRE (`access.dre`) veem a top bar e
  // a paleta, cada um com apenas os itens autorizados. Enquanto o
  // viewer carrega (null), o shell assume a navegação interna — a BFF
  // continua autoridade final se uma rota interna for acessada.
  const catalogViewer = hasAccess || hasDreAccess;
  // Viewer somente-DRE: usuário com `access` interno navega sempre pela
  // experiência interna — a projeção DRE (nav, seções, paleta) só aparece
  // para quem não tem `access`, evitando itens duplicados de «Início».
  const dreViewer = hasDreAccess && viewer?.capabilities.access !== true;

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const isPaletteChord =
        (event.key === "k" || event.key === "K") && (event.metaKey || event.ctrlKey);
      if (!isPaletteChord || !catalogViewer) return;
      if (isEditableTarget(event.target) && !paletteOpen) return;
      event.preventDefault();
      setPaletteOpen((open) => !open);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [paletteOpen, catalogViewer]);

  const items = catalogViewer
    ? resolveShellNavItems({
        access: hasAccess,
        manage: showManage,
        accessDre: dreViewer,
      })
    : [];

  const activeId = resolveActiveNavId(view);
  const showGreeting = view === "home" || view === "dre_home";
  /** UX-016 — hero + listagem ocupam a altura útil do mount (scroll na tabela). */
  const fillViewport =
    view === "checklist_admin" || view === "checklist_version";
  const heroTitle = formatPortalGreeting({ firstName: viewer?.firstName ?? null });

  const isDreHome = view === "dre_home" && dreViewer;
  const heroCopy = isDreHome
    ? SHELL_NAV_CONTENT.dreHero
    : SHELL_NAV_CONTENT.homeHero;
  const heroHighlights = isDreHome
    ? undefined
    : [
        {
          id: "competence",
          label: SHELL_NAV_CONTENT.homeHero.highlights.competence,
          value: SHELL_NAV_CONTENT.homeHero.highlightsUnavailable,
        },
        {
          id: "attention",
          label: SHELL_NAV_CONTENT.homeHero.highlights.attention,
          value: SHELL_NAV_CONTENT.homeHero.highlightsUnavailable,
        },
      ];

  const paletteSections = useMemo(
    () =>
      resolveHubSections({
        access: hasAccess,
        manage: showManage,
        accessDre: dreViewer,
      }),
    [hasAccess, showManage, dreViewer],
  );

  const paletteHits = useMemo(
    () => collectSearchHits(paletteSections, paletteQuery, 8),
    [paletteQuery, paletteSections],
  );

  const onSelectPaletteHit = useCallback(
    (routeId: string) => {
      const route = findHubRouteById(paletteSections, routeId);
      if (!route) return;
      navigatePluginView(route.viewId, { basePath, search: route.search });
      setPaletteOpen(false);
      setPaletteQuery("");
    },
    [basePath, paletteSections],
  );

  return (
    <div
      className={[
        CF_PORTAL_SCOPE,
        "dashboard-page",
        fillViewport ? "dashboard-page--fill" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="cf-page-stack">
        <CfTopBar
          aria-label={SHELL_NAV_CONTENT.ariaLabel}
          activeId={activeId ?? ""}
          collapsible
          collapseMode="hamburger"
          collapseTrigger="overflow"
          collapseLabel={SHELL_NAV_CONTENT.collapseLabel}
          expandLabel={SHELL_NAV_CONTENT.expandLabel}
          menuLabel={SHELL_NAV_CONTENT.menuLabel}
          portalScopeClassName={CF_PORTAL_SCOPE}
          items={items.map((item) => ({
            id: item.id,
            label: item.label,
            icon: NAV_ICONS[item.id],
            title: NAV_HELP[item.id]
              ? `${item.label}. ${NAV_HELP[item.id]}`
              : item.label,
            onSelect: () => navigatePluginView(item.id, { basePath }),
          }))}
          secondary={
            catalogViewer ? (
              <CfTopBarUtilityCluster>
                <CfTopBarSearchTrigger
                  ref={searchTriggerRef}
                  onOpen={() => setPaletteOpen(true)}
                  expanded={paletteOpen}
                  label={SHELL_NAV_CONTENT.searchLabel}
                  shortcutLabel={SHELL_NAV_CONTENT.searchShortcutLabel}
                  aria-label={SHELL_NAV_CONTENT.searchAriaLabel}
                  title={SHELL_NAV_CONTENT.searchTitle}
                />
              </CfTopBarUtilityCluster>
            ) : undefined
          }
          actions={
            <CfTopBarUserIdentity
              displayName={viewer?.displayName ?? viewer?.firstName ?? null}
              avatarUrl={avatarUrl}
              avatarHref="/profile"
              avatarTitle="Abrir Meu Perfil na Minha DELPI"
              fallbackLabel={SHELL_NAV_CONTENT.userMenu.nameFallback}
              portalScopeClassName={CF_PORTAL_SCOPE}
            />
          }
        />

        {showGreeting ? (
          <CfViewTransition transitionKey="home-hero" tone="page">
            <CfPageHero
              aria-label={heroCopy.ariaLabel}
              eyebrow={heroCopy.eyebrow}
              title={
                <CfTitleWithHelp
                  title={heroTitle}
                  hint={
                    isDreHome ? CF_HELP.dreHome.hero : CF_HELP.home.overview
                  }
                />
              }
              description={heroCopy.description}
              badge={
                <CfStatusBadge
                  label={
                    isDreHome
                      ? SHELL_NAV_CONTENT.dreHero.scopeDre
                      : SHELL_NAV_CONTENT.homeHero.scopeOwn
                  }
                  variant="neutral"
                />
              }
              highlights={heroHighlights}
            />
          </CfViewTransition>
        ) : null}

        <CfViewTransition transitionKey={view} tone="page">
          {children}
        </CfViewTransition>
      </div>

      <CfCommandPalette
        open={catalogViewer && paletteOpen}
        onClose={() => {
          setPaletteOpen(false);
          setPaletteQuery("");
        }}
        anchorRef={searchTriggerRef}
        title={HUB_CONTENT.palette.title}
        value={paletteQuery}
        onChange={setPaletteQuery}
        hits={paletteHits.map((hit) => ({
          id: hit.id,
          label: hit.label,
          groupLabel: hit.groupLabel,
        }))}
        onSelectHit={onSelectPaletteHit}
        placeholder={HUB_CONTENT.palette.placeholder}
        emptyHitsLabel={HUB_CONTENT.palette.empty}
        aria-label={CF_HELP.home.palette}
      />
    </div>
  );
}
