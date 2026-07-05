import { useCallback, useEffect, useRef, useState } from "react";

export function useFullscreenStage() {
  const ref = useRef<HTMLDivElement | null>(null);
  const [fullscreen, setFullscreen] = useState(false);

  const toggleFullscreen = useCallback(async () => {
    const node = ref.current;
    if (!node) return;
    if (!document.fullscreenElement) {
      await node.requestFullscreen?.();
    } else {
      await document.exitFullscreen?.();
    }
  }, []);

  useEffect(() => {
    const onChange = () => setFullscreen(Boolean(document.fullscreenElement));
    document.addEventListener("fullscreenchange", onChange);
    return () => document.removeEventListener("fullscreenchange", onChange);
  }, []);

  return { ref, fullscreen, toggleFullscreen };
}
