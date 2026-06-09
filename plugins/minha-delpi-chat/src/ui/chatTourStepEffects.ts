import type { AssistantOnboardingTourStep } from "../data/api/chatTypes";
import {
  fillShortcutTemplate,
  normalizeShortcutTemplate,
  SEARCH_QUERY_PLACEHOLDER,
} from "./chatShortcutPrompt";

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
  welcome: "home-greeting",
  highlights: "home-highlights",
  ask: "composer-input",
  agent: "composer-plus-menu-agents",
  attach: "composer-attach",
  chips: "follow-up-demo",
  canvas: "composer-input",
};

const STEP_DEFAULT_EFFECTS: Record<string, Partial<ChatTourStepEffect>> = {
  welcome: { pulseTarget: true },
  highlights: { pulseTarget: true },
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
    searchQuery: SEARCH_QUERY_PLACEHOLDER,
    period: "últimos 30 dias",
    productDescription: "exemplo de busca",
  });
}

/** Atualiza o composer em poucos passos (evita centenas de re-renders por segundo). */
export async function animateTourTyping(
  query: string,
  onChange: (value: string) => void,
  signal: AbortSignal,
): Promise<void> {
  if (signal.aborted) {
    return;
  }

  const text = query.trim();

  if (!text) {
    onChange("");
    return;
  }

  onChange("");

  const maxSteps = 8;
  const chunkSize = Math.max(1, Math.ceil(text.length / maxSteps));

  for (let index = chunkSize; index < text.length; index += chunkSize) {
    if (signal.aborted) {
      return;
    }

    onChange(text.slice(0, index));
    await new Promise<void>((resolve) => {
      window.setTimeout(resolve, 80);
    });
  }

  if (!signal.aborted) {
    onChange(text);
  }
}
