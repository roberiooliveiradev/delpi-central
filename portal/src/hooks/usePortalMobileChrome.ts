import { useEffect, useState } from "react";

const NARROW_QUERY = "(max-width: 1024px)";
const LANDSCAPE_MOBILE_QUERY = "(max-width: 1024px) and (orientation: landscape)";

export function usePortalMobileChrome() {
  const [isNarrowViewport, setIsNarrowViewport] = useState(
    () => typeof window !== "undefined" && window.matchMedia(NARROW_QUERY).matches,
  );
  const [isLandscapeMobile, setIsLandscapeMobile] = useState(
    () =>
      typeof window !== "undefined" &&
      window.matchMedia(LANDSCAPE_MOBILE_QUERY).matches,
  );

  useEffect(() => {
    const narrowMq = window.matchMedia(NARROW_QUERY);
    const landscapeMq = window.matchMedia(LANDSCAPE_MOBILE_QUERY);

    const sync = () => {
      setIsNarrowViewport(narrowMq.matches);
      setIsLandscapeMobile(landscapeMq.matches);
    };

    sync();
    narrowMq.addEventListener("change", sync);
    landscapeMq.addEventListener("change", sync);

    return () => {
      narrowMq.removeEventListener("change", sync);
      landscapeMq.removeEventListener("change", sync);
    };
  }, []);

  return {
    isNarrowViewport,
    isLandscapeMobile,
    showMobileNav: isNarrowViewport,
  };
}
