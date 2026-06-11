import composerContent from "./message_composer.json";

export type MessageComposerTypingCorrectionContent = {
  hint: string;
  acceptLabel: string;
  dismissLabel: string;
  previewPrefix: string;
};

export function getTypingCorrectionContent(): MessageComposerTypingCorrectionContent {
  return composerContent.typingCorrection;
}
