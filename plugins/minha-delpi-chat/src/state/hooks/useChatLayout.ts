import { useEffect, useState } from "react";

export type ChatLayoutState = {
  isDesktop: boolean;
  isCompact: boolean;
  isNarrow: boolean;
  isLandscape: boolean;
};

const DESKTOP_QUERY = "(min-width: 1024px)";
const NARROW_QUERY = "(max-width: 480px)";
const LANDSCAPE_COMPACT_QUERY = "(orientation: landscape) and (max-height: 520px)";

function readLayout(): ChatLayoutState {
  if (typeof window === "undefined") {
    return { isDesktop: true, isCompact: false, isNarrow: false, isLandscape: false };
  }

  return {
    isDesktop: window.matchMedia(DESKTOP_QUERY).matches,
    isCompact: !window.matchMedia(DESKTOP_QUERY).matches,
    isNarrow: window.matchMedia(NARROW_QUERY).matches,
    isLandscape: window.matchMedia(LANDSCAPE_COMPACT_QUERY).matches,
  };
}

export function useChatLayout(): ChatLayoutState {
  const [layout, setLayout] = useState<ChatLayoutState>(readLayout);

  useEffect(() => {
    const desktopMq = window.matchMedia(DESKTOP_QUERY);
    const narrowMq = window.matchMedia(NARROW_QUERY);
    const landscapeMq = window.matchMedia(LANDSCAPE_COMPACT_QUERY);

    function update() {
      setLayout(readLayout());
    }

    desktopMq.addEventListener("change", update);
    narrowMq.addEventListener("change", update);
    landscapeMq.addEventListener("change", update);
    update();

    return () => {
      desktopMq.removeEventListener("change", update);
      narrowMq.removeEventListener("change", update);
      landscapeMq.removeEventListener("change", update);
    };
  }, []);

  return layout;
}
