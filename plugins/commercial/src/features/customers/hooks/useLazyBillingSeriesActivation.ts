import { useCallback, useEffect, useRef, useState, type RefObject } from "react";

type VisibilityEntry = { isIntersecting: boolean };
type VisibilityObserver = {
  observe: (target: Element) => void;
  disconnect: () => void;
};
type VisibilityObserverFactory = (
  callback: (entries: readonly VisibilityEntry[]) => void,
) => VisibilityObserver;

export function observeElementOnce(
  target: Element,
  activate: () => void,
  observerFactory?: VisibilityObserverFactory,
): () => void {
  const factory =
    observerFactory ??
    (typeof IntersectionObserver === "undefined"
      ? null
      : (callback: (entries: readonly VisibilityEntry[]) => void) =>
          new IntersectionObserver(callback));
  if (!factory) {
    activate();
    return () => undefined;
  }

  let activated = false;
  const observer = factory((entries) => {
    if (activated || !entries.some((entry) => entry.isIntersecting)) return;
    activated = true;
    observer.disconnect();
    activate();
  });
  observer.observe(target);
  return () => observer.disconnect();
}

export function isMobileBillingViewport(): boolean {
  return typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(max-width: 768px)").matches;
}

export function useLazyBillingSeriesActivation(): {
  anchorRef: RefObject<HTMLDivElement | null>;
  open: boolean;
  setOpen: (open: boolean) => void;
  enabled: boolean;
} {
  const initialMobile = isMobileBillingViewport();
  const [mobile] = useState(initialMobile);
  const anchorRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(!initialMobile);
  const [enabled, setEnabled] = useState(false);
  const activatedRef = useRef(false);
  const activate = useCallback(() => {
    if (activatedRef.current) return;
    activatedRef.current = true;
    setEnabled(true);
  }, []);

  useEffect(() => {
    if (!open || activatedRef.current) return;
    if (mobile) {
      activate();
      return;
    }
    const target = anchorRef.current;
    if (!target) return;
    return observeElementOnce(target, activate);
  }, [activate, mobile, open]);

  return { anchorRef, open, setOpen, enabled };
}
