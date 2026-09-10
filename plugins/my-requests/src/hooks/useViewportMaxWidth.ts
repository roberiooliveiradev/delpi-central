import { useEffect, useState } from "react";

/** True when viewport max-width matches (e.g. compact ProgressTracker). */
export function useViewportMaxWidth(maxWidthPx: number): boolean {
  const query = `(max-width: ${maxWidthPx}px)`;
  const [matches, setMatches] = useState(() => {
    if (typeof window === "undefined") return false;
    return window.matchMedia(query).matches;
  });

  useEffect(() => {
    const media = window.matchMedia(query);
    const sync = () => setMatches(media.matches);
    sync();
    media.addEventListener("change", sync);
    return () => media.removeEventListener("change", sync);
  }, [query]);

  return matches;
}
