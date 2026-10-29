import { useEffect, useState } from "react";

import {
  EngineeringActionButton,
  EngineeringPageHero,
  EngineeringPagePath,
  EngineeringSectionCard,
} from "../../ui/engineeringUi";
import {
  buildEngineeringPath,
  navigateEngineeringView,
} from "../../app/engineeringRoutes";
import { LEGACY_NONCONFORMITIES_HREF, LMPS_ROUTES } from "./constants/routes";
import { useLmpsRouterPath } from "./hooks/useLmpsRouterPath";
import { DashboardLmpsPage } from "./pages/DashboardLmpsPage";
import { LmpDetailPage } from "./pages/LmpDetailPage";
import {
  normalizeLmpsPath,
  parseLmpsPath,
  readOvBranchFromUrl,
} from "./utils/routeParser";
import { navigateLmps } from "./utils/navigation";

type LmpsFeatureProps = {
  pathname?: string;
};

/** Rotas de NC ainda não migradas — estado honesto apontando para o
 * MFE legado, que permanece operacional e autorizado. */
function NcLegacyRedirectNotice() {
  return (
    <main className="engineering-lmps">
      <EngineeringPagePath
        back={{
          label: "Início",
          href: buildEngineeringPath("home"),
          onNavigate: (event) => {
            event.preventDefault();
            navigateEngineeringView("home");
          },
        }}
        items={[]}
        current="Não conformidades"
      />
      <EngineeringPageHero
        eyebrow="Portal Engenharia • LMPs"
        title="Não conformidades"
        description="O registro de não conformidades continua disponível no aplicativo de acompanhamento de LMPs."
      />
      <EngineeringSectionCard
        title="Funcionalidade no aplicativo legado"
        subtitle="A migração desta área será tratada em gate próprio; o aplicativo legado permanece operacional e autorizado."
      >
        <div className="engineering-lmps-nc-actions">
          <EngineeringActionButton
            variant="primary"
            onClick={() => {
              window.location.assign(LEGACY_NONCONFORMITIES_HREF);
            }}
          >
            Abrir registro de não conformidades
          </EngineeringActionButton>
          <EngineeringActionButton
            variant="ghost"
            onClick={() => navigateLmps(LMPS_ROUTES.home)}
          >
            Voltar ao dashboard
          </EngineeringActionButton>
        </div>
      </EngineeringSectionCard>
    </main>
  );
}

/** Raiz da feature LMP no Portal Engenharia — mesmo padrão do MFE
 * legado: o dashboard permanece montado (oculto) durante o detalhe da
 * OV para preservar filtros, scroll e estado de tabela. */
export function LmpsFeature({ pathname: pathnameFromHost }: LmpsFeatureProps) {
  const pathname = useLmpsRouterPath(pathnameFromHost);
  const path = normalizeLmpsPath(pathname);
  const route = parseLmpsPath(path);
  const showDashboard = route.view === "dashboard";
  const showNcPending =
    route.view === "nonconformities" ||
    route.view === "nonconformity-detail" ||
    route.view === "nonconformity-new";
  const showDetail = route.view === "ov-detail" && Boolean(route.saleNumber);

  const [dashboardMounted, setDashboardMounted] = useState(showDashboard);

  useEffect(() => {
    if (showDashboard) {
      setDashboardMounted(true);
    }
  }, [showDashboard]);

  return (
    <>
      {dashboardMounted ? (
        <div hidden={!showDashboard} aria-hidden={!showDashboard}>
          <DashboardLmpsPage pathname={path} isActive={showDashboard} />
        </div>
      ) : null}

      {showNcPending ? <NcLegacyRedirectNotice /> : null}

      {showDetail && route.saleNumber ? (
        <LmpDetailPage
          saleNumber={route.saleNumber}
          branch={readOvBranchFromUrl()}
        />
      ) : null}
    </>
  );
}
