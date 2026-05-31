import type { AssistantOnboardingTourStep } from "../data/api/chatTypes";
import { fillShortcutTemplate, normalizeShortcutTemplate } from "./chatShortcutPrompt";

export type ChatTourDemoSuggestion = {
  label: string;
  query: string;
};

export type ChatTourStepEffect = {
  target: string;
  demoQuery?: string;
  openPlusMenu?: boolean;
  demoSuggestions?: ChatTourDemoSuggestion[];
  pulseTarget?: boolean;
};

const DEFAULT_DEMO_SUGGESTIONS: ChatTourDemoSuggestion[] = [
  { label: "Ver estoque", query: "qual o estoque do produto 10080001?" },
  { label: "Onde é usado", query: "onde o produto 10080001 é usado?" },
  { label: "Abrir lousa", query: "abra na lousa um rascunho com os pontos da reunião" },
];

const STEP_TARGET_BY_ID: Record<string, string> = {
  starters: "starter-cards",
  ask: "composer-input",
  agent: "composer-plus-menu-agents",
  attach: "composer-attach",
  chips: "follow-up-demo",
  canvas: "composer-input",
};

const STEP_DEFAULT_EFFECTS: Record<string, Partial<ChatTourStepEffect>> = {
  starters: { pulseTarget: true },
  ask: {
    demoQuery: "qual o estoque do produto 10080001?",
  },
  agent: { openPlusMenu: true },
  attach: { openPlusMenu: true },
  chips: { demoSuggestions: DEFAULT_DEMO_SUGGESTIONS },
  canvas: {
    demoQuery: "abra na lousa um rascunho com os pontos da reunião",
  },
};

export function tourTargetSelector(step: AssistantOnboardingTourStep): string {
  const target = step.target?.trim() || STEP_TARGET_BY_ID[step.id] || step.id;

  return `[data-tour="${target}"]`;
}

export function resolveTourStepEffect(step: AssistantOnboardingTourStep): ChatTourStepEffect {
  const defaults = STEP_DEFAULT_EFFECTS[step.id] ?? {};
  const demoSuggestions =
    step.demoSuggestions && step.demoSuggestions.length > 0
      ? step.demoSuggestions
      : defaults.demoSuggestions;

  return {
    target: step.target?.trim() || STEP_TARGET_BY_ID[step.id] || step.id,
    demoQuery: step.demoQuery?.trim() || defaults.demoQuery,
    openPlusMenu: step.openPlusMenu ?? defaults.openPlusMenu ?? false,
    demoSuggestions,
    pulseTarget: defaults.pulseTarget ?? false,
  };
}

/** Texto legível no composer durante o tour (não envia `{{placeholders}}`). */
export function tourDemoQueryForDisplay(query?: string): string {
  const template = normalizeShortcutTemplate(String(query ?? "").trim());

  if (!template) {
    return "";
  }

  if (!template.includes("{{")) {
    return template;
  }

  return fillShortcutTemplate(template, {
    productCode: "10080001",
    searchQuery: "manual WEG CFW500",
    period: "últimos 30 dias",
    productDescription: "exemplo de busca",
  });
}

export async function animateTourTyping(
  query: string,
  onChange: (value: string) => void,
  signal: AbortSignal,
): Promise<void> {
  onChange("");

  for (let index = 0; index <= query.length; index += 1) {
    if (signal.aborted) {
      return;
    }

    onChange(query.slice(0, index));
    await new Promise<void>((resolve) => {
      window.setTimeout(resolve, 32);
    });
  }
}
