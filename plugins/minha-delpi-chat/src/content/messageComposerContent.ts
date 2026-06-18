import composerContent from "./message_composer.json";

export type MessageComposerTypingCorrectionContent = {
  hint: string;
  acceptLabel: string;
  dismissLabel: string;
  previewPrefix: string;
};

export type MessageComposerPlusMenuContent = {
  filesSectionTitle: string;
  agentsSectionTitle: string;
  projectsSectionTitle: string;
  agentsHint: string;
  projectsHint: string;
  emptyAgents: string;
  emptyProjects: string;
};

export function getTypingCorrectionContent(): MessageComposerTypingCorrectionContent {
  return composerContent.typingCorrection;
}

export function getComposerPlusMenuContent(): MessageComposerPlusMenuContent {
  return composerContent.plusMenu;
}

export function formatComposerPlusMenuText(
  template: string,
  values: Record<string, string | number>,
): string {
  return template.replace(/\{(\w+)\}/g, (_, key: string) => String(values[key] ?? ""));
}
