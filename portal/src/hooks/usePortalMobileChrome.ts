import { useEffect, useState } from "react";

import { PORTAL_NARROW_VIEWPORT_QUERY } from "./portalMobileChromePolicy";

const NARROW_QUERY = PORTAL_NARROW_VIEWPORT_QUERY;
const LANDSCAPE_MOBILE_QUERY = "(max-width: 1024px) and (orientation: landscape)";
/** Telas baixas: phones landscape + hubs/tablets landscape (ex.: Nest Hub 1024×600). */
const COMPACT_SIDEBAR_QUERY =
  "(max-width: 1024px) and (max-height: 520px), (max-width: 1024px) and (max-height: 680px) and (min-aspect-ratio: 1/1)";
/** Fallback quando `orientation` falha no DevTools (ex.: Galaxy Z Fold). */
const LANDSCAPE_LAYOUT_QUERY = "(max-width: 1024px) and (min-aspect-ratio: 1/1)";

export function usePortalMobileChrome() {
  const [isNarrowViewport, setIsNarrowViewport] = useState(
    () => typeof window !== "undefined" && window.matchMedia(NARROW_QUERY).matches,
  );
  const [isLandscapeMobile, setIsLandscapeMobile] = useState(
    () =>
      typeof window !== "undefined" &&
      window.matchMedia(LANDSCAPE_MOBILE_QUERY).matches,
  );
  const [isCompactSidebar, setIsCompactSidebar] = useState(
    () =>
      typeof window !== "undefined" &&
      window.matchMedia(COMPACT_SIDEBAR_QUERY).matches,
  );
  const [isLandscapeLayout, setIsLandscapeLayout] = useState(
    () =>
      typeof window !== "undefined" &&
      window.matchMedia(LANDSCAPE_LAYOUT_QUERY).matches,
  );

  useEffect(() => {
    const narrowMq = window.matchMedia(NARROW_QUERY);
    const landscapeMq = window.matchMedia(LANDSCAPE_MOBILE_QUERY);
    const compactMq = window.matchMedia(COMPACT_SIDEBAR_QUERY);
    const landscapeLayoutMq = window.matchMedia(LANDSCAPE_LAYOUT_QUERY);

    const sync = () => {
      setIsNarrowViewport(narrowMq.matches);
      setIsLandscapeMobile(landscapeMq.matches);
      setIsCompactSidebar(compactMq.matches);
      setIsLandscapeLayout(landscapeLayoutMq.matches);
    };

    sync();
    narrowMq.addEventListener("change", sync);
    landscapeMq.addEventListener("change", sync);
    compactMq.addEventListener("change", sync);
    landscapeLayoutMq.addEventListener("change", sync);

    return () => {
      narrowMq.removeEventListener("change", sync);
      landscapeMq.removeEventListener("change", sync);
      compactMq.removeEventListener("change", sync);
      landscapeLayoutMq.removeEventListener("change", sync);
    };
  }, []);

  return {
    isNarrowViewport,
    isLandscapeMobile,
    isLandscapeLayout,
    isCompactSidebar,
  };
}
