import { useEffect, useState } from "react";

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
    <main className="dashboard-lmps dashboard-page">
      <div className="lmps-card lmps-state-box">
        <p>
          O registro de não conformidades continua disponível no aplicativo
          de acompanhamento de LMPs.
        </p>
        <div>
          <a className="lmps-primary-btn" href={LEGACY_NONCONFORMITIES_HREF}>
            Abrir registro de não conformidades
          </a>{" "}
          <button
            type="button"
            className="lmps-ghost-btn"
            onClick={() => navigateLmps(LMPS_ROUTES.home)}
          >
            Voltar ao dashboard
          </button>
        </div>
      </div>
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
