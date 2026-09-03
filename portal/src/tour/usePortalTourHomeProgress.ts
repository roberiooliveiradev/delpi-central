import { useContext, useEffect, useMemo, useRef, useState } from "react";
import { AuthContext } from "../state/AuthContext";
import { ApiClient } from "../data/apiClient";
import {
  CoreApi,
  type PortalTourCatalogResponse,
  type PortalTourProgressResponse,
} from "../data/coreApi";
import {
  loadPortalTourProgress,
  repairLocalCompletedWhenRemoteIncomplete,
} from "./portalTourPersistence";
import { resolvePortalTourHomeEntryState } from "./portalTourHomeEntry";
import { shouldShowPortalTour } from "./portalTourStorage";
import {
  DELPI_PORTAL_TOUR_HOME_REFRESH_EVENT,
  usePortalTourSession,
} from "./portalTourSession";

const HOME_ENTRY_CACHE_KEY = "delpi.portal.tourHomeEntry.v1";

type HomeEntryDisplayCache = {
  requiredDone: number;
  requiredTotal: number;
  progressPercent: number;
  explorerLevel: string;
  newQuestCount?: number;
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
    const parsed = raw
      ? (JSON.parse(raw) as Record<string, HomeEntryDisplayCache>)
      : {};
    parsed[userId] = display;
    sessionStorage.setItem(HOME_ENTRY_CACHE_KEY, JSON.stringify(parsed));
  } catch {
    // cache opcional — não bloqueia UI
  }
}

export type PortalTourHomeProgress = {
  ready: boolean;
  loading: boolean;
  visible: boolean;
  requiredDone: number;
  requiredTotal: number;
  progressPercent: number;
  explorerLevel: string;
  newQuestCount: number;
  progress: PortalTourProgressResponse | null;
  catalog: PortalTourCatalogResponse | null;
};

export function usePortalTourHomeProgress(): PortalTourHomeProgress {
  const { user, coreLoaded, getAccessToken, refreshToken } =
    useContext(AuthContext);
  const session = usePortalTourSession();
  const [progress, setProgress] = useState<PortalTourProgressResponse | null>(
    null,
  );
  const [catalog, setCatalog] = useState<PortalTourCatalogResponse | null>(
    null,
  );
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

    const load = () => {
      void Promise.all([
        loadPortalTourProgress(api, user.id),
        api.getPortalTourCatalog().catch(() => null),
      ]).then(([remoteProgress, remoteCatalog]) => {
        if (cancelled) return;
        repairLocalCompletedWhenRemoteIncomplete(
          user.id,
          remoteProgress,
          remoteCatalog,
        );
        setProgress(remoteProgress);
        if (remoteCatalog) setCatalog(remoteCatalog);
        setDataReady(true);
      });
    };

    load();

    const onRefresh = () => {
      setDataReady(false);
      load();
    };
    window.addEventListener(DELPI_PORTAL_TOUR_HOME_REFRESH_EVENT, onRefresh);

    return () => {
      cancelled = true;
      window.removeEventListener(DELPI_PORTAL_TOUR_HOME_REFRESH_EVENT, onRefresh);
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
      newQuestCount: entry.newQuestCount,
    });
  }, [user?.id, dataReady, entry]);

  const display = dataReady
    ? {
        requiredDone: entry.requiredDone,
        requiredTotal: entry.requiredTotal,
        progressPercent: entry.progressPercent,
        explorerLevel: entry.explorerLevel,
        newQuestCount: entry.newQuestCount,
      }
    : cachedDisplay ?? {
        requiredDone: 0,
        requiredTotal: 0,
        progressPercent: 0,
        explorerLevel: "Explorador",
        newQuestCount: 0,
      };

  const tourLikelyVisible = Boolean(
    user?.id &&
      coreLoaded &&
      (shouldShowPortalTour(user.id) ||
        (cachedDisplay != null &&
          (cachedDisplay.progressPercent < 100 ||
            cachedDisplay.requiredDone < cachedDisplay.requiredTotal))),
  );

  const loading = Boolean(user?.id && coreLoaded && !dataReady);
  const visible =
    Boolean(user?.id && coreLoaded) &&
    !session.dismissed &&
    !session.completed &&
    ((!dataReady && tourLikelyVisible) || (dataReady && entry.visible));

  return {
    ready: dataReady,
    loading,
    visible,
    requiredDone: display.requiredDone,
    requiredTotal: display.requiredTotal,
    progressPercent: display.progressPercent,
    explorerLevel: display.explorerLevel,
    newQuestCount: display.newQuestCount ?? 0,
    progress,
    catalog,
  };
}
