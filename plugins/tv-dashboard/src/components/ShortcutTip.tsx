import {
  useLayoutEffect,
  useRef,
  useState,
  type CSSProperties,
  type ReactElement,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";

import { useKeyboardShortcutsTips } from "../context/KeyboardShortcutsTipsProvider";
import {
  resolveShortcutTipPosition,
  type ShortcutTipPlacement,
} from "../utils/shortcutTipPosition";

type Props = {
  /** Id do catálogo (`TV_KEYBOARD_SHORTCUTS`). */
  shortcutId: string;
  children: ReactElement;
  className?: string;
  /** Preferência; a tela pode inverter se não couber. */
  placement?: ShortcutTipPlacement;
};

const TIP_Z_INDEX = 11100;

/**
 * Envolve um controle e, com Alt segurado, mostra o atalho em balão (KeyTip)
 * via portal — evita clip por overflow da ribbon/chrome — com flip/clamp na viewport.
 */
export function ShortcutTip({
  shortcutId,
  children,
  className,
  placement = "top",
}: Props): ReactNode {
  const { altTipsActive, getShortcut, formatKeys } = useKeyboardShortcutsTips();
  const entry = getShortcut(shortcutId);
  const anchorRef = useRef<HTMLSpanElement>(null);
  const tipRef = useRef<HTMLSpanElement>(null);
  const [style, setStyle] = useState<CSSProperties | null>(null);
  const [resolvedPlacement, setResolvedPlacement] = useState<ShortcutTipPlacement>(placement);

  const show = Boolean(entry?.showAltTip && altTipsActive);

  useLayoutEffect(() => {
    if (!show) {
      setStyle(null);
      return;
    }

    const update = () => {
      const anchor = anchorRef.current;
      const tipEl = tipRef.current;
      if (!anchor || !tipEl) return;
      const rect = anchor.getBoundingClientRect();
      const tipWidth = tipEl.offsetWidth || 64;
      const tipHeight = tipEl.offsetHeight || 28;
      const next = resolveShortcutTipPosition({
        anchor: rect,
        tipWidth,
        tipHeight,
        preferred: placement,
        viewportWidth: window.innerWidth,
        viewportHeight: window.innerHeight,
      });
      setResolvedPlacement(next.placement);
      setStyle({
        position: "fixed",
        top: next.top,
        left: next.left,
        zIndex: TIP_Z_INDEX,
        transform: "none",
      });
    };

    update();
    const raf = window.requestAnimationFrame(update);
    window.addEventListener("resize", update);
    window.addEventListener("scroll", update, true);
    return () => {
      window.cancelAnimationFrame(raf);
      window.removeEventListener("resize", update);
      window.removeEventListener("scroll", update, true);
    };
  }, [placement, show]);

  if (!entry?.showAltTip) {
    return children;
  }

  const badge = show
    ? createPortal(
        <div className="dashboard-tv-dashboard td-shortcut-tip-layer" aria-hidden="true">
          <span
            ref={tipRef}
            className={[
              "td-shortcut-tip__badge",
              "td-shortcut-tip__badge--portal",
              resolvedPlacement === "bottom" ? "td-shortcut-tip__badge--bottom" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            style={style ?? { position: "fixed", top: -9999, left: -9999, visibility: "hidden" }}
            role="tooltip"
          >
            {formatKeys(entry.keys)}
          </span>
        </div>,
        document.body,
      )
    : null;

  return (
    <span
      ref={anchorRef}
      className={["td-shortcut-tip", className].filter(Boolean).join(" ")}
      data-td-shortcut={shortcutId}
    >
      {children}
      {badge}
    </span>
  );
}
