import { useContext, useEffect, useMemo, useRef, useState } from "react";
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
import { shouldShowPortalTour } from "./portalTourStorage";

const HOME_ENTRY_CACHE_KEY = "delpi.portal.tourHomeEntry.v1";

type HomeEntryDisplayCache = {
  requiredDone: number;
  requiredTotal: number;
  progressPercent: number;
  explorerLevel: string;
};

function readHomeEntryDisplayCache(
  userId: string | undefined,
): HomeEntryDisplayCache | null {
  if (!userId) return null;

  try {
    const raw = sessionStorage.getItem(HOME_ENTRY_CACHE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Record<string, HomeEntryDisplayCache>;
    const cached = parsed[userId];
    if (!cached || typeof cached !== "object") return null;
    return cached;
  } catch {
    return null;
  }
}

function writeHomeEntryDisplayCache(
  userId: string,
  display: HomeEntryDisplayCache,
): void {
  try {
    const raw = sessionStorage.getItem(HOME_ENTRY_CACHE_KEY);
    const parsed = raw ? (JSON.parse(raw) as Record<string, HomeEntryDisplayCache>) : {};
    parsed[userId] = display;
    sessionStorage.setItem(HOME_ENTRY_CACHE_KEY, JSON.stringify(parsed));
  } catch {
    // cache opcional — não bloqueia UI
  }
}

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
  const coreApiRef = useRef(coreApi);
  coreApiRef.current = coreApi;

  useEffect(() => {
    setDataReady(false);
    setProgress(null);
    setCatalog(null);
  }, [user?.id]);

  useEffect(() => {
    if (!coreLoaded || !user?.id) return;

    let cancelled = false;
    const api = coreApiRef.current;

    void Promise.all([
      loadPortalTourProgress(api, user.id),
      api.getPortalTourCatalog().catch(() => null),
    ]).then(([remoteProgress, remoteCatalog]) => {
      if (cancelled) return;
      setProgress(remoteProgress);
      if (remoteCatalog) setCatalog(remoteCatalog);
      setDataReady(true);
    });

    return () => {
      cancelled = true;
    };
  }, [coreLoaded, user?.id]);

  const entry = useMemo(
    () => resolvePortalTourHomeEntryState(user?.id, progress, catalog),
    [user?.id, progress, catalog],
  );

  const cachedDisplay = useMemo(
    () => readHomeEntryDisplayCache(user?.id),
    [user?.id],
  );

  useEffect(() => {
    if (!user?.id || !dataReady || !entry.visible) return;

    writeHomeEntryDisplayCache(user.id, {
      requiredDone: entry.requiredDone,
      requiredTotal: entry.requiredTotal,
      progressPercent: entry.progressPercent,
      explorerLevel: entry.explorerLevel,
    });
  }, [user?.id, dataReady, entry]);

  const display = dataReady
    ? {
        requiredDone: entry.requiredDone,
        requiredTotal: entry.requiredTotal,
        progressPercent: entry.progressPercent,
        explorerLevel: entry.explorerLevel,
      }
    : cachedDisplay ?? {
        requiredDone: 0,
        requiredTotal: 0,
        progressPercent: 0,
        explorerLevel: "Explorador",
      };

  const tourLikelyVisible = Boolean(
    user?.id && coreLoaded && shouldShowPortalTour(user.id),
  );

  if (!user?.id || !coreLoaded) return null;

  const shouldRender =
    (!dataReady && tourLikelyVisible) || (dataReady && entry.visible);

  if (!shouldRender) return null;

  const isLoading = !dataReady;
  const valueLabel =
    display.requiredTotal > 0
      ? `${display.requiredDone}/${display.requiredTotal}`
      : isLoading
        ? "···"
        : "Explorar";
  const subLabel = isLoading
    ? cachedDisplay
      ? `${display.progressPercent}% · ${display.explorerLevel}`
      : "Carregando…"
    : `${display.progressPercent}% · ${display.explorerLevel}`;

  const handleOpen = () => {
    if (isLoading) return;

    if (session.sessionActive) {
      openPortalTourPanel();
      return;
    }
    resumePortalTour();
  };

  return (
    <motion.button
      type="button"
      className={[
        "home-summary-card",
        "portal-tour-home-entry",
        isLoading ? "portal-tour-home-entry--loading" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      data-tour="home-portal-tour-resume"
      aria-busy={isLoading}
      disabled={isLoading}
      onClick={handleOpen}
      initial={false}
      whileHover={isLoading ? undefined : { y: -2 }}
      whileTap={isLoading ? undefined : { scale: 0.98 }}
    >
      <span className="home-summary-icon">
        <Trophy size={18} aria-hidden />
      </span>

      <span className="home-summary-main">
        <span className="home-summary-title">Descubra o portal</span>
        <span className="home-summary-value">{valueLabel}</span>
        <span className="home-summary-sub">{subLabel}</span>
      </span>

      <span className="home-summary-arrow">
        <ArrowRight size={16} aria-hidden />
      </span>
    </motion.button>
  );
}
