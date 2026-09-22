export {
  RichTextEditor,
  type RichTextEditorHandle,
  type RichTextEditorMode,
  type RichTextEditorProps,
  type RichTextMentionLabels,
  type RichTextPasteImagesHandler,
  type MentionMenuHit,
} from "./RichTextEditor";
export {
  buildGlpiUserMentionLabel,
  createGlpiUserMentionElement,
  insertGlpiUserMentionAtPlainRange,
  isGlpiUserMentionId,
  refreshActiveUserMention,
} from "./richTextUserMention";
export type { RichTextInlineImageInsert } from "./richTextInlineImage";
export {
  applyFormat,
  formatIntent,
  resolveFormatTarget,
  type ApplyFormatOptions,
  type FormatIntent,
  type FormatIntentClass,
  type FormatTarget,
} from "./formatApply";
export {
  applyRichTextInlineCss,
  type ApplyRichTextInlineCssOptions,
  type RichTextInlineCssPatch,
} from "./richTextCommands";
export {
  DeckContentRunsView,
  plainTextFromDeckContentRuns,
  shouldPersistDeckContentRuns,
  type DeckContentRun,
  type DeckContentRunStyle,
} from "./deckContentRuns";
