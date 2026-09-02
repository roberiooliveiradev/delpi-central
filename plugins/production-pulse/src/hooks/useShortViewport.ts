import { useEffect, useState } from "react";

import { isShortViewportHeight } from "../utils/viewportLayout";

/** Viewport baixo (ex.: landscape ~375px ou portrait ≤700px) — operador compacto sem scroll. */
export function useShortViewport(): boolean {
  const [short, setShort] = useState(() =>
    typeof window !== "undefined" ? isShortViewportHeight(window.innerHeight) : false,
  );

  useEffect(() => {
    const sync = () => setShort(isShortViewportHeight(window.innerHeight));
    window.addEventListener("resize", sync);
    return () => window.removeEventListener("resize", sync);
  }, []);

  return short;
}
