import {
  useLayoutEffect,
  useRef,
  useState,
  type CSSProperties,
  type ReactElement,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";

import { useDeckKeyTips } from "../context/DeckKeyTipsProvider";
import {
  normalizeKeyTipLetter,
  type DeckKeyTipScope,
} from "../utils/deckKeyTips";
import {
  resolveShortcutTipPosition,
  type ShortcutTipPlacement,
} from "../utils/shortcutTipPosition";

type Props = {
  /** Letra/dígito exibido e capturado (ex.: "P", "1"). */
  letter: string;
  scope: DeckKeyTipScope;
  children: ReactElement;
  className?: string;
  placement?: ShortcutTipPlacement;
};

const TIP_Z_INDEX = 11100;

/**
 * Anota um controle com KeyTip F (abas/ações) e mostra balão quando o modo
 * correspondente está ativo.
 */
export function DeckKeyTip({
  letter,
  scope,
  children,
  className,
  placement = "bottom",
}: Props): ReactNode {
  const { showTabTips, showActionTips } = useDeckKeyTips();
  const tip = normalizeKeyTipLetter(letter);
  const show = scope === "tabs" ? showTabTips : showActionTips;
  const anchorRef = useRef<HTMLSpanElement>(null);
  const tipRef = useRef<HTMLSpanElement>(null);
  const [style, setStyle] = useState<CSSProperties | null>(null);
  const [resolvedPlacement, setResolvedPlacement] = useState<ShortcutTipPlacement>(placement);

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
      const next = resolveShortcutTipPosition({
        anchor: rect,
        tipWidth: tipEl.offsetWidth || 28,
        tipHeight: tipEl.offsetHeight || 24,
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

  const badge = show
    ? createPortal(
        <div className="dashboard-tv-dashboard td-shortcut-tip-layer" aria-hidden="true">
          <span
            ref={tipRef}
            className={[
              "td-shortcut-tip__badge",
              "td-shortcut-tip__badge--portal",
              "td-shortcut-tip__badge--keytip",
              resolvedPlacement === "bottom" ? "td-shortcut-tip__badge--bottom" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            style={style ?? { position: "fixed", top: -9999, left: -9999, visibility: "hidden" }}
            role="tooltip"
          >
            {tip}
          </span>
        </div>,
        document.body,
      )
    : null;

  return (
    <span
      ref={anchorRef}
      className={["td-shortcut-tip", "td-deck-keytip", className].filter(Boolean).join(" ")}
      data-td-keytip={tip}
      data-td-keytip-scope={scope}
    >
      {children}
      {badge}
    </span>
  );
}
