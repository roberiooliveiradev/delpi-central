import { Activity, Clock3, History } from "lucide-react";
import { useEffect, useMemo } from "react";

import { configureHttpClient } from "./api/httpClient";
import { canUseDelpiMes, hasDelpiMesProductAccess } from "./constants/permissions";
import { AREAS, BRANCH_PERMISSIONS, type BranchCode, type DelpiMesArea } from "./constants/routes";
import { DELPI_MES_COPY } from "./content/copy";
import { buildDelpiMesHref, useDelpiMesRoute } from "./hooks/useDelpiMesRoute";
import { FoundationPage } from "./pages/FoundationPage";
import { MonitoringPage } from "./pages/MonitoringPage";
import { heroImageUrl, sidebarLogoUrl } from "./utils/assets";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  permissions?: string[];
  isSuperadmin?: boolean;
};

const AREA_ICONS = { monitoring: Activity, downtimes: Clock3, history: History };

export default function App({
  getAccessToken,
  pathname,
  permissions = [],
  isSuperadmin = false,
}: AppProps) {
  configureHttpClient(() => getAccessToken?.());
  const permissionSet = useMemo(() => new Set(permissions), [permissions]);
  const { route, navigate } = useDelpiMesRoute(pathname);
  const can = (permission: string) => canUseDelpiMes(permissionSet, permission, isSuperadmin);
  const hasProductAccess = hasDelpiMesProductAccess(permissionSet, isSuperadmin);
  const visibleAreas = hasProductAccess ? AREAS.filter((area) => can(area.permission)) : [];
  const visibleBranches = hasProductAccess
    ? (["01", "02"] as BranchCode[]).filter((branch) => can(BRANCH_PERMISSIONS[branch]))
    : [];
  const activeBranch = visibleBranches.includes(route.branch) ? route.branch : visibleBranches[0];
  const activeArea = visibleAreas.some((area) => area.id === route.area)
    ? route.area
    : visibleAreas[0]?.id;
  const heroUrl = heroImageUrl();
  const logoUrl = sidebarLogoUrl();

  useEffect(() => {
    if (!activeArea || !activeBranch) return;
    const canonical = buildDelpiMesHref(activeArea, activeBranch);
    if (`${window.location.pathname}${window.location.search}` !== canonical) navigate(canonical);
  }, [activeArea, activeBranch, navigate]);

  const navigateTo = (area: DelpiMesArea, branch: BranchCode) => {
    navigate(buildDelpiMesHref(area, branch));
  };

  const navLinks = (activeId: DelpiMesArea | undefined, branch: BranchCode | undefined, classPrefix: string) =>
    visibleAreas.map((area) => {
      const Icon = AREA_ICONS[area.id];
      const active = area.id === activeId;
      return (
        <a
          key={area.id}
          href={buildDelpiMesHref(area.id, branch ?? "01")}
          className={active ? `${classPrefix}__link ${classPrefix}__link--active` : `${classPrefix}__link`}
          aria-current={active ? "page" : undefined}
          onClick={(event) => {
            event.preventDefault();
            if (branch) navigateTo(area.id, branch);
          }}
        >
          <Icon aria-hidden="true" />
          <span>{area.label}</span>
        </a>
      );
    });

  return (
    <main className="delpi-mes-shell">
      <aside className="delpi-mes-sidebar">
        <div className="delpi-mes-sidebar__brand">
          {logoUrl ? (
            <img src={logoUrl} alt="Delpi" className="delpi-mes-sidebar__logo" />
          ) : (
            <>
              <strong>Delpi</strong>
              <span>conexões elétricas</span>
            </>
          )}
        </div>
        <nav className="delpi-mes-sidebar__nav" aria-label="Áreas do Delpi MES">
          {navLinks(activeArea, activeBranch, "delpi-mes-sidebar-nav")}
        </nav>
        <p className="delpi-mes-sidebar__tagline">
          Indústria conectada
          <br />
          Resultados reais
        </p>
      </aside>

      <div className="delpi-mes-content">
        <header className="delpi-mes-header">
          <div className="delpi-mes-brand">
            <p className="delpi-mes-eyebrow">Produção</p>
            <h1>{DELPI_MES_COPY.productName}</h1>
            <p>{DELPI_MES_COPY.productDescription}</p>
          </div>
          <div className="delpi-mes-hero">
            {heroUrl ? (
              <img src={heroUrl} alt="" aria-hidden="true" className="delpi-mes-hero__image" />
            ) : (
              <div className="delpi-mes-hero__placeholder" aria-hidden="true" />
            )}
            {activeBranch ? (
              <label className="delpi-mes-branch">
                <span>Filial</span>
                <select
                  value={activeBranch}
                  onChange={(event) => navigateTo(activeArea ?? "monitoring", event.target.value as BranchCode)}
                  aria-describedby="delpi-mes-branch-help"
                >
                  {visibleBranches.map((branch) => (
                    <option key={branch} value={branch}>{branch === "01" ? "01 - SC" : "02 - ES"}</option>
                  ))}
                </select>
                <span id="delpi-mes-branch-help" className="delpi-mes-sr-only">{DELPI_MES_COPY.help.branch}</span>
              </label>
            ) : null}
          </div>
        </header>

        {activeArea && activeBranch ? (
          <>
            <nav className="delpi-mes-nav" aria-label="Seções">
              {navLinks(activeArea, activeBranch, "delpi-mes-nav")}
            </nav>
            {activeArea === "monitoring" ? (
              <MonitoringPage
                branch={activeBranch}
                canViewHistory={can("delpi-mes.history.view")}
              />
            ) : (
              <FoundationPage area={activeArea} />
            )}
          </>
        ) : (
          <section className="delpi-mes-forbidden" role="alert">
            <h2>Acesso não disponível</h2>
            <p>Seu perfil ainda não possui área e filial habilitadas no Delpi MES.</p>
          </section>
        )}
      </div>
    </main>
  );
}
