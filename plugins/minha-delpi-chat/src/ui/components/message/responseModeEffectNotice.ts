import type { ChatMessageMetadata } from "../../../data/api/chatTypes";

export function resolveResponseModeEffectNotice(
  metadata: ChatMessageMetadata | null | undefined,
): string | null {
  const intelligence = metadata?.intelligence;

  if (!intelligence || typeof intelligence !== "object") {
    return null;
  }

  const pipeline = (intelligence as { pipeline?: unknown }).pipeline;

  if (!pipeline || typeof pipeline !== "object") {
    return null;
  }

  const effect = String(
    (pipeline as { responseModeEffect?: unknown }).responseModeEffect ?? "",
  )
    .trim()
    .toLowerCase();

  if (effect !== "llm_synthesis" && effect !== "llm_synthesis_brief") {
    return null;
  }

  if ((pipeline as { directResponse?: unknown }).directResponse === true) {
    return null;
  }

  const notice = String(
    (pipeline as { responseModeEffectNotice?: unknown }).responseModeEffectNotice ?? "",
  ).trim();

  return notice || null;
}
