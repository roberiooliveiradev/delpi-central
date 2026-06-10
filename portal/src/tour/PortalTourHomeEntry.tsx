import { useContext, useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, Trophy } from "lucide-react";
import { AuthContext } from "../state/AuthContext";
import { ApiClient } from "../data/apiClient";
import { CoreApi, type PortalTourCatalogResponse, type PortalTourProgressResponse } from "../data/coreApi";
import { loadPortalTourProgress } from "./portalTourPersistence";
import {
  openPortalTourPanel,
  resumePortalTour,
  usePortalTourSession,
} from "./portalTourSession";
import { resolvePortalTourHomeEntryState } from "./portalTourHomeEntry";

export function PortalTourHomeEntry() {
  const { user, coreLoaded, getAccessToken, refreshToken } = useContext(AuthContext);
  const session = usePortalTourSession();
  const [progress, setProgress] = useState<PortalTourProgressResponse | null>(null);
  const [catalog, setCatalog] = useState<PortalTourCatalogResponse | null>(null);
  const [dataReady, setDataReady] = useState(false);

  const coreApi = useMemo(
    () =>
      new CoreApi(
        new ApiClient("", getAccessToken, {
          refreshToken: async () => {
            await refreshToken();
            return Boolean(getAccessToken());
          },
        }),
      ),
    [getAccessToken, refreshToken],
  );

  useEffect(() => {
    if (!coreLoaded || !user?.id) return;

    let cancelled = false;

    void Promise.all([
      loadPortalTourProgress(coreApi, user.id),
      coreApi.getPortalTourCatalog().catch(() => null),
    ]).then(([remoteProgress, remoteCatalog]) => {
      if (cancelled) return;
      setProgress(remoteProgress);
      if (remoteCatalog) setCatalog(remoteCatalog);
      setDataReady(true);
    });

    return () => {
      cancelled = true;
    };
  }, [coreLoaded, user?.id, coreApi]);

  const entry = useMemo(
    () =>
      resolvePortalTourHomeEntryState(
        user?.id,
        progress,
        catalog,
        session.panelOpen,
      ),
    [user?.id, progress, catalog, session.panelOpen],
  );

  const display = session.sessionActive
    ? {
        requiredDone: session.requiredDone,
        requiredTotal: session.requiredTotal,
        progressPercent: session.progressPercent,
        explorerLevel: session.explorerLevel,
      }
    : {
        requiredDone: entry.requiredDone,
        requiredTotal: entry.requiredTotal,
        progressPercent: entry.progressPercent,
        explorerLevel: entry.explorerLevel,
      };

  const showEntry = dataReady && entry.visible;

  if (!showEntry) return null;

  const handleOpen = () => {
    if (session.sessionActive) {
      openPortalTourPanel();
      return;
    }
    resumePortalTour();
  };

  return (
    <motion.button
      type="button"
      className="home-summary-card portal-tour-home-entry"
      data-tour="home-portal-tour-resume"
      onClick={handleOpen}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2 }}
      whileTap={{ scale: 0.98 }}
    >
      <span className="home-summary-icon">
        <Trophy size={18} aria-hidden />
      </span>

      <span className="home-summary-main">
        <span className="home-summary-title">Descubra o portal</span>
        <span className="home-summary-value">
          {display.requiredTotal > 0
            ? `${display.requiredDone}/${display.requiredTotal}`
            : "Explorar"}
        </span>
        <span className="home-summary-sub">
          {display.progressPercent}% · {display.explorerLevel}
        </span>
      </span>

      <span className="home-summary-arrow">
        <ArrowRight size={16} aria-hidden />
      </span>
    </motion.button>
  );
}
