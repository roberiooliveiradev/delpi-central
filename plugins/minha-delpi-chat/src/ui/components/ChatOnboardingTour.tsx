import { useEffect, useState } from "react";
import { X } from "lucide-react";

import type { AssistantOnboardingTourStep } from "../../data/api/chatTypes";

import "./ChatOnboardingTour.css";

const STORAGE_KEY = "minha-delpi-chat:onboarding-tour-completed";

type ChatOnboardingTourProps = {
  steps: AssistantOnboardingTourStep[];
  onDismiss?: () => void;
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

export function ChatOnboardingTour({ steps, onDismiss }: ChatOnboardingTourProps) {
  const [index, setIndex] = useState(0);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (steps.length === 0 || isOnboardingTourCompleted()) {
      return;
    }

    setVisible(true);
  }, [steps.length]);

  if (!visible || steps.length === 0) {
    return null;
  }

  const step = steps[Math.min(index, steps.length - 1)];
  const isLast = index >= steps.length - 1;

  function closeTour() {
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

  return (
    <aside
      className="mdc-chat-onboarding-tour"
      role="dialog"
      aria-label="Tour rápido do chat"
      aria-live="polite"
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
  );
}
