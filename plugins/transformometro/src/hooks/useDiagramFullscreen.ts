import { useCallback, useEffect, useState } from "react";

export function useDiagramFullscreen() {
  const [isFullscreen, setIsFullscreen] = useState(false);

  const exit = useCallback(() => setIsFullscreen(false), []);
  const enter = useCallback(() => setIsFullscreen(true), []);
  const toggle = useCallback(() => setIsFullscreen((current) => !current), []);

  useEffect(() => {
    if (!isFullscreen) return undefined;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      const target = event.target as HTMLElement | null;
      if (target?.closest(".tm-diagram-inline-edit")) return;
      setIsFullscreen(false);
    };

    window.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [isFullscreen]);

  return { isFullscreen, enter, exit, toggle };
}
