import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { X } from "lucide-react";

import type { AssistantOnboardingTourStep } from "../../../data/api/chatTypes";
import {
  animateTourTyping,
  tourDemoQueryForDisplay,
  resolveTourStepEffect,
  tourTargetSelector,
} from "../../chatTourStepEffects";
import {
  computeTourTooltipLayout,
  type SpotlightRect,
  type TourTooltipLayout,
} from "../../chatTourTooltipPosition";
import { ChatFollowUpChips } from "../message/ChatFollowUpChips";
import { ModalPortal } from "../shared/overlay/ModalPortal";
import { OverlayScrim } from "../shared/overlay/OverlayScrim";
import {
  isOverlayPortalContained,
  resolveOverlayPortalContainer,
} from "../shared/overlay/modalPortalTarget";

import "./ChatOnboardingTour.css";

const STORAGE_KEY = "minha-delpi-chat:onboarding-tour-completed";

function readViewportSize(): { width: number; height: number } {
  if (typeof window === "undefined") {
    return { width: 1280, height: 800 };
  }

  const container = resolveOverlayPortalContainer();

  if (isOverlayPortalContained(container)) {
    return {
      width: container.clientWidth,
      height: container.clientHeight,
    };
  }

  return {
    width: window.visualViewport?.width ?? window.innerWidth,
    height: window.visualViewport?.height ?? window.innerHeight,
  };
}

function spotlightFromElementRect(rect: DOMRect, padding: number): SpotlightRect {
  const container = resolveOverlayPortalContainer();
  const contained = isOverlayPortalContained(container);
  const containerRect = contained ? container.getBoundingClientRect() : null;
  const offsetTop = containerRect?.top ?? 0;
  const offsetLeft = containerRect?.left ?? 0;

  return {
    top: Math.max(0, rect.top - offsetTop - padding),
    left: Math.max(0, rect.left - offsetLeft - padding),
    width: rect.width + padding * 2,
    height: rect.height + padding * 2,
  };
}

type ChatOnboardingTourProps = {
  steps: AssistantOnboardingTourStep[];
  /** Só abre o overlay quando true (evita loop de layout na home). */
  autoStart?: boolean;
  onDismiss?: () => void;
  onStepChange?: (step: AssistantOnboardingTourStep, index: number) => void;
  onDemoQuery?: (query: string) => void;
  onPlusMenuOpen?: (open: boolean) => void;
};

export function isOnboardingTourCompleted(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) === "1";
  } catch {
    return false;
  }
}

function markOnboardingTourCompleted(): void {
  try {
    localStorage.setItem(STORAGE_KEY, "1");
  } catch {
    /* ignore quota errors */
  }
}

function spotlightRectsEqual(
  current: SpotlightRect | null,
  next: SpotlightRect | null,
): boolean {
  if (!current || !next) {
    return current === next;
  }

  return (
    current.top === next.top &&
    current.left === next.left &&
    current.width === next.width &&
    current.height === next.height
  );
}

export function ChatOnboardingTour({
  steps,
  autoStart = false,
  onDismiss,
  onStepChange,
  onDemoQuery,
  onPlusMenuOpen,
}: ChatOnboardingTourProps) {
  const [index, setIndex] = useState(0);
  const [visible, setVisible] = useState(false);
  const [spotlight, setSpotlight] = useState<SpotlightRect | null>(null);
  const [tooltipLayout, setTooltipLayout] = useState<TourTooltipLayout | null>(null);
  const [pulseTarget, setPulseTarget] = useState(false);
  const demoAbortRef = useRef<AbortController | null>(null);
  const highlightedRef = useRef<HTMLElement | null>(null);
  const tooltipRef = useRef<HTMLElement | null>(null);
  const scrolledStepIdRef = useRef<string | null>(null);
  const measureFrameRef = useRef<number | null>(null);

  const step = steps[Math.min(index, steps.length - 1)];
  const stepId = step?.id;
  const isLast = index >= steps.length - 1;
  const effect = useMemo(
    () => (step ? resolveTourStepEffect(step) : null),
    [step, stepId],
  );
  const openPlusMenu = Boolean(effect?.openPlusMenu);
  const demoQuery = effect?.demoQuery?.trim() ?? "";

  const clearHighlight = useCallback(() => {
    if (highlightedRef.current) {
      highlightedRef.current.classList.remove("mdc-chat-tour-target--active");
      highlightedRef.current = null;
    }
  }, []);

  const applyStepEffects = useCallback(
    (activeStep: AssistantOnboardingTourStep) => {
      demoAbortRef.current?.abort();
      demoAbortRef.current = new AbortController();
      const signal = demoAbortRef.current.signal;
      const activeEffect = resolveTourStepEffect(activeStep);

      onPlusMenuOpen?.(Boolean(activeEffect.openPlusMenu));
      setPulseTarget(Boolean(activeEffect.pulseTarget));

      if (activeEffect.demoQuery && onDemoQuery) {
        void animateTourTyping(
          tourDemoQueryForDisplay(activeEffect.demoQuery),
          onDemoQuery,
          signal,
        );
      } else {
        onDemoQuery?.("");
      }
    },
    [onDemoQuery, onPlusMenuOpen],
  );

  useEffect(() => {
    if (!autoStart || steps.length === 0) {
      return;
    }

    setVisible(true);
    setIndex(0);
  }, [autoStart, steps.length]);

  useEffect(() => {
    if (!visible) {
      return;
    }

    scrolledStepIdRef.current = null;
    setTooltipLayout(null);
  }, [visible, stepId]);

  const applyTooltipLayout = useCallback(() => {
    if (!spotlight) {
      setTooltipLayout(null);
      return;
    }

    const viewport = readViewportSize();
    const element = tooltipRef.current;
    const measuredHeight = element?.offsetHeight ?? undefined;
    const measuredWidth =
      element && element.offsetWidth > 120 ? element.offsetWidth : undefined;

    const layout = computeTourTooltipLayout(
      spotlight,
      viewport.width,
      viewport.height,
      {
        estimatedHeight: measuredHeight,
        maxWidth: measuredWidth,
      },
    );

    setTooltipLayout((current) => {
      if (
        current &&
        current.top === layout.top &&
        current.left === layout.left &&
        current.width === layout.width &&
        current.placement === layout.placement
      ) {
        return current;
      }

      return layout;
    });
  }, [spotlight]);

  useLayoutEffect(() => {
    if (!visible || !spotlight) {
      setTooltipLayout(null);
      return;
    }

    applyTooltipLayout();

    const refineFrame = requestAnimationFrame(() => {
      applyTooltipLayout();
    });

    return () => {
      cancelAnimationFrame(refineFrame);
    };
  }, [applyTooltipLayout, spotlight, visible, stepId, index]);

  useEffect(() => {
    if (!visible || !step || !stepId) {
      return;
    }

    onStepChange?.(step, index);
    applyStepEffects(step);
  }, [visible, stepId, index, onStepChange, applyStepEffects, step]);

  useLayoutEffect(() => {
    if (!visible || !stepId || !effect) {
      setSpotlight(null);
      clearHighlight();
      return;
    }

    const selector = tourTargetSelector(step);

    function measureTarget() {
      const element = document.querySelector(selector) as HTMLElement | null;

      clearHighlight();

      if (!element) {
        setSpotlight((current) => (current === null ? current : null));
        return;
      }

      highlightedRef.current = element;
      element.classList.add("mdc-chat-tour-target--active");

      if (scrolledStepIdRef.current !== stepId) {
        scrolledStepIdRef.current = stepId;
        element.scrollIntoView({ block: "nearest", behavior: "auto" });
      }

      const rect = element.getBoundingClientRect();
      const padding = 8;

      const nextSpotlight = spotlightFromElementRect(rect, padding);

      setSpotlight((current) =>
        spotlightRectsEqual(current, nextSpotlight) ? current : nextSpotlight,
      );
    }

    function scheduleMeasure() {
      if (measureFrameRef.current != null) {
        cancelAnimationFrame(measureFrameRef.current);
      }

      measureFrameRef.current = requestAnimationFrame(() => {
        measureFrameRef.current = null;
        measureTarget();
      });
    }

    scheduleMeasure();

    const resizeObserver =
      typeof ResizeObserver !== "undefined"
        ? new ResizeObserver(() => {
            scheduleMeasure();
          })
        : null;

    const observed = document.querySelector(selector) as HTMLElement | null;

    if (observed && resizeObserver) {
      resizeObserver.observe(observed);
    }

    window.addEventListener("resize", scheduleMeasure);
    window.visualViewport?.addEventListener("resize", scheduleMeasure);
    window.visualViewport?.addEventListener("scroll", scheduleMeasure);

    const retryTimers = [120, 320].map((delay) =>
      window.setTimeout(scheduleMeasure, delay),
    );

    return () => {
      if (measureFrameRef.current != null) {
        cancelAnimationFrame(measureFrameRef.current);
        measureFrameRef.current = null;
      }

      retryTimers.forEach((timer) => window.clearTimeout(timer));
      window.removeEventListener("resize", scheduleMeasure);
      window.visualViewport?.removeEventListener("resize", scheduleMeasure);
      window.visualViewport?.removeEventListener("scroll", scheduleMeasure);
      resizeObserver?.disconnect();
      clearHighlight();
    };
  }, [visible, stepId, index, clearHighlight, openPlusMenu, demoQuery]);

  function closeTour() {
    demoAbortRef.current?.abort();
    onPlusMenuOpen?.(false);
    onDemoQuery?.("");
    clearHighlight();
    markOnboardingTourCompleted();
    setVisible(false);
    onDismiss?.();
  }

  function handleNext() {
    if (isLast) {
      closeTour();
      return;
    }

    setIndex((current) => current + 1);
  }

  if (!visible || steps.length === 0 || !step) {
    return null;
  }

  const showDemoChips =
    step.id === "chips" && Boolean(effect?.demoSuggestions && effect.demoSuggestions.length > 0);

  const overlay = (
    <div className="mdc-chat-tour-root" role="presentation">
      {spotlight ? (
        <div
          className="mdc-chat-tour-spotlight"
          style={{
            top: spotlight.top,
            left: spotlight.left,
            width: spotlight.width,
            height: spotlight.height,
          }}
          data-pulse={pulseTarget ? "true" : undefined}
        />
      ) : null}

      <OverlayScrim className="mdc-chat-tour-backdrop" onMouseDown={closeTour} />

      {showDemoChips ? (
        <div className="mdc-chat-tour-follow-up-anchor" data-tour="follow-up-demo">
          <ChatFollowUpChips
            suggestions={effect?.demoSuggestions ?? []}
            onUseSuggestion={(query) => onDemoQuery?.(query)}
            groupLabel="Próximos passos (exemplo)"
            ariaLabel="Demonstração de próximos passos"
          />
        </div>
      ) : null}

      <aside
        ref={tooltipRef}
        className={[
          "mdc-chat-onboarding-tour",
          "mdc-chat-onboarding-tour--anchored",
          tooltipLayout
            ? `mdc-chat-onboarding-tour--placement-${tooltipLayout.placement}`
            : "",
        ]
          .filter(Boolean)
          .join(" ")}
        role="dialog"
        aria-label="Tour rápido do chat"
        aria-live="polite"
        data-placement={tooltipLayout?.placement}
        style={
          tooltipLayout
            ? {
                top: tooltipLayout.top,
                left: tooltipLayout.left,
                width: tooltipLayout.width,
              }
            : spotlight
              ? {
                  visibility: "hidden",
                  top: 12,
                  left: 12,
                  width: "min(22rem, calc(100vw - 1.5rem))",
                }
              : undefined
        }
      >
        <div className="mdc-chat-onboarding-tour__header">
          <p className="mdc-chat-onboarding-tour__eyebrow">
            Tour · passo {index + 1} de {steps.length}
          </p>

          <button
            type="button"
            className="mdc-chat-modal-icon-btn mdc-chat-modal-icon-btn--sm"
            onClick={closeTour}
            aria-label="Fechar tour"
          >
            <X size={16} aria-hidden="true" />
          </button>
        </div>

        <h3>{step.title}</h3>
        {step.body ? <p>{step.body}</p> : null}

        <div className="mdc-chat-onboarding-tour__actions">
          <button type="button" className="mdc-chat-onboarding-tour__skip" onClick={closeTour}>
            Pular tour
          </button>

          <button type="button" className="mdc-chat-onboarding-tour__next" onClick={handleNext}>
            {isLast ? "Começar" : "Próximo"}
          </button>
        </div>
      </aside>
    </div>
  );

  return <ModalPortal lockScroll>{overlay}</ModalPortal>;
}
