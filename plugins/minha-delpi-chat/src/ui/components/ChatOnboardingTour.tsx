import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";

import type { AssistantOnboardingTourStep } from "../../data/api/chatTypes";
import {
  animateTourTyping,
  tourDemoQueryForDisplay,
  resolveTourStepEffect,
  tourTargetSelector,
} from "../chatTourStepEffects";
import { ChatFollowUpChips } from "./ChatFollowUpChips";

import "./ChatOnboardingTour.css";

const STORAGE_KEY = "minha-delpi-chat:onboarding-tour-completed";

type SpotlightRect = {
  top: number;
  left: number;
  width: number;
  height: number;
};

type ChatOnboardingTourProps = {
  steps: AssistantOnboardingTourStep[];
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

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

export function ChatOnboardingTour({
  steps,
  onDismiss,
  onStepChange,
  onDemoQuery,
  onPlusMenuOpen,
}: ChatOnboardingTourProps) {
  const [index, setIndex] = useState(0);
  const [visible, setVisible] = useState(false);
  const [spotlight, setSpotlight] = useState<SpotlightRect | null>(null);
  const [pulseTarget, setPulseTarget] = useState(false);
  const demoAbortRef = useRef<AbortController | null>(null);
  const highlightedRef = useRef<HTMLElement | null>(null);

  const step = steps[Math.min(index, steps.length - 1)];
  const isLast = index >= steps.length - 1;
  const effect = step ? resolveTourStepEffect(step) : null;

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
    if (steps.length === 0 || isOnboardingTourCompleted()) {
      return;
    }

    setVisible(true);
  }, [steps.length]);

  useEffect(() => {
    if (!visible || !step) {
      return;
    }

    onStepChange?.(step, index);
    applyStepEffects(step);
  }, [visible, step, index, onStepChange, applyStepEffects]);

  useLayoutEffect(() => {
    if (!visible || !step || !effect) {
      setSpotlight(null);
      clearHighlight();
      return;
    }

    const selector = tourTargetSelector(step);

    function measureTarget() {
      const element = document.querySelector(selector) as HTMLElement | null;

      clearHighlight();

      if (!element) {
        setSpotlight(null);
        return;
      }

      highlightedRef.current = element;
      element.classList.add("mdc-chat-tour-target--active");
      element.scrollIntoView({ block: "nearest", behavior: "smooth" });

      const rect = element.getBoundingClientRect();
      const padding = 8;

      setSpotlight({
        top: Math.max(0, rect.top - padding),
        left: Math.max(0, rect.left - padding),
        width: rect.width + padding * 2,
        height: rect.height + padding * 2,
      });
    }

    measureTarget();

    const resizeObserver =
      typeof ResizeObserver !== "undefined"
        ? new ResizeObserver(() => {
            measureTarget();
          })
        : null;

    const observed = document.querySelector(selector) as HTMLElement | null;

    if (observed && resizeObserver) {
      resizeObserver.observe(observed);
    }

    window.addEventListener("resize", measureTarget);
    window.addEventListener("scroll", measureTarget, true);

    const retryTimers = [120, 320, 520].map((delay) => window.setTimeout(measureTarget, delay));

    return () => {
      retryTimers.forEach((timer) => window.clearTimeout(timer));
      window.removeEventListener("resize", measureTarget);
      window.removeEventListener("scroll", measureTarget, true);
      resizeObserver?.disconnect();
      clearHighlight();
    };
  }, [visible, step, effect, index, clearHighlight, effect?.openPlusMenu, step?.id]);

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

  const tooltipTop = spotlight
    ? clamp(spotlight.top + spotlight.height + 12, 12, window.innerHeight - 220)
    : undefined;
  const tooltipLeft = spotlight
    ? clamp(spotlight.left, 12, window.innerWidth - 320)
    : undefined;
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

      <div className="mdc-chat-tour-backdrop" onClick={closeTour} aria-hidden="true" />

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
        className="mdc-chat-onboarding-tour mdc-chat-onboarding-tour--anchored"
        role="dialog"
        aria-label="Tour rápido do chat"
        aria-live="polite"
        style={
          tooltipTop !== undefined && tooltipLeft !== undefined
            ? { top: tooltipTop, left: tooltipLeft }
            : undefined
        }
      >
        <div className="mdc-chat-onboarding-tour__header">
          <p className="mdc-chat-onboarding-tour__eyebrow">
            Tour · passo {index + 1} de {steps.length}
          </p>

          <button
            type="button"
            className="mdc-chat-onboarding-tour__close"
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

  return createPortal(overlay, document.body);
}
