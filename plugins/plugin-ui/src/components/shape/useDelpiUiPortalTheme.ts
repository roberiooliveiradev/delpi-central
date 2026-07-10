import { useLayoutEffect, useState } from "react";
import type { RefObject } from "react";

import {
  DELPI_UI_SHAPE_THEME_HOST_CLASS,
  resolveDelpiUiPortalTheme,
  type DelpiUiPortalTheme,
} from "./delpiUiPortalTheme";

export function useDelpiUiPortalTheme(
  active: boolean,
  anchorRef?: RefObject<HTMLElement | null>,
): DelpiUiPortalTheme & { hostClassName: string } {
  const [theme, setTheme] = useState<DelpiUiPortalTheme>(() => resolveDelpiUiPortalTheme());

  useLayoutEffect(() => {
    if (!active) return;

    const refresh = () => {
      setTheme(resolveDelpiUiPortalTheme(anchorRef?.current ?? undefined));
    };

    refresh();
    const raf = requestAnimationFrame(refresh);

    window.addEventListener("resize", refresh);
    const observer = new MutationObserver(refresh);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme", "class"],
    });

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", refresh);
      observer.disconnect();
    };
  }, [active, anchorRef]);

  return {
    ...theme,
    hostClassName: DELPI_UI_SHAPE_THEME_HOST_CLASS,
  };
}
