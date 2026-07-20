import { useLayoutEffect, useState } from "react";
import type { CSSProperties } from "react";

import {
  containedModalBoxToStyle,
  measureContainedModalBox,
  resolveContainedModalScrollPort,
  type ContainedModalBox,
} from "./containedModalViewport";

const EMPTY_BOX: ContainedModalBox = { top: 0, left: 0, width: 0, height: 0 };

/**
 * Estilo `position: fixed` alinhado ao scrollport visível do host MFE.
 * Atualiza em resize / mudança de layout (sidebar, etc.).
 */
export function useContainedModalViewportStyle(
  active: boolean,
  host: HTMLElement | null,
): CSSProperties | undefined {
  const [box, setBox] = useState<ContainedModalBox>(EMPTY_BOX);

  useLayoutEffect(() => {
    if (!active || !host) {
      setBox(EMPTY_BOX);
      return;
    }

    const update = () => {
      setBox(measureContainedModalBox(host));
    };
    update();

    const scrollPort = resolveContainedModalScrollPort(host);
    const ro = typeof ResizeObserver !== "undefined" ? new ResizeObserver(update) : null;
    ro?.observe(host);
    if (scrollPort !== host) {
      ro?.observe(scrollPort);
    }
    window.addEventListener("resize", update);
    window.visualViewport?.addEventListener("resize", update);

    return () => {
      ro?.disconnect();
      window.removeEventListener("resize", update);
      window.visualViewport?.removeEventListener("resize", update);
    };
  }, [active, host]);

  if (!active || !host) return undefined;
  if (box.width <= 0 || box.height <= 0) {
    // Fallback seguro até a 1ª medição (evita flash em 0×0).
    return {
      position: "fixed",
      inset: 0,
      minWidth: 0,
      minHeight: 0,
    };
  }
  return containedModalBoxToStyle(box);
}
