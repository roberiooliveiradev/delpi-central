/**
 * Interaction Presentation adapter — DELIA-UX-S1-PRESENTATION-ADAPTER-01.
 *
 * Defensive parse-only adapter for the additive `presentation` object
 * emitted by delia-api (contract `version: "1"` — see
 * delia-api/app/application/interaction/presentation.py).
 *
 * Never authority: it validates shapes and normalizes vocabulary, but
 * it cannot authorize actions, promote content, or fabricate state.
 * Unknown message kinds, block kinds, block roles, contract versions,
 * or interaction names degrade to safe neutral values — never to a
 * privileged or misleading rendering.
 */

export const PRESENTATION_CONTRACT_VERSION = "1";

/** Canonical message kinds — the exact GovernedCapabilityStatus-derived
 *  vocabulary published by the backend. Never extended client-side. */
export type DeliaMessageKind =
  | "RESULT"
  | "CLARIFICATION_REQUIRED"
  | "CONFIRMATION_REQUIRED"
  | "WRITE_REJECTED"
  | "AUTHZ_DENIED"
  | "SOURCE_UNAVAILABLE"
  | "PRECONDITION_REQUIRED";

const KNOWN_MESSAGE_KINDS: ReadonlySet<string> = new Set<string>([
  "RESULT",
  "CLARIFICATION_REQUIRED",
  "CONFIRMATION_REQUIRED",
  "WRITE_REJECTED",
  "AUTHZ_DENIED",
  "SOURCE_UNAVAILABLE",
  "PRECONDITION_REQUIRED",
]);

/** Closed block allowlist — mirrors the backend emit set. Any other
 *  kind is dropped silently; unknown notice roles are dropped too. */
export type DeliaPresentationBlock =
  | { kind: "text"; text: string }
  | { kind: "notice"; role: "owner_hint"; text: string };

export type DeliaAllowedInteraction = "reply" | "confirm" | "reject";

const KNOWN_INTERACTIONS: ReadonlySet<string> = new Set<string>([
  "reply",
  "confirm",
  "reject",
]);

/** Defensive bounds mirroring the backend emit bounds. */
const MAX_BLOCKS = 8;
const MAX_BLOCK_TEXT_CHARS = 16_384;

/**
 * Normalized presentation projection. `messageKind` is null when the
 * wire value is outside the published vocabulary — callers must render
 * that as neutral content, never as a success or an action surface.
 */
export type DeliaPresentation = {
  messageKind: DeliaMessageKind | null;
  semanticStatus: string | null;
  groundingStatus: "GROUNDED" | "NON_GROUNDED" | null;
  blocks: DeliaPresentationBlock[];
  allowedInteractions: DeliaAllowedInteraction[];
};

/**
 * Parses the additive `presentation` field. Returns null for absent,
 * malformed, or unknown-version payloads so callers fall back to the
 * legacy fields (`content`, `epistemic_class`, `limitations`, …).
 */
export function parsePresentation(raw: unknown): DeliaPresentation | null {
  if (!raw || typeof raw !== "object") return null;
  const record = raw as Record<string, unknown>;
  if (record.version !== PRESENTATION_CONTRACT_VERSION) return null;

  const rawKind =
    typeof record.message_kind === "string" ? record.message_kind : "";
  const messageKind = KNOWN_MESSAGE_KINDS.has(rawKind)
    ? (rawKind as DeliaMessageKind)
    : null;

  const rawBlocks = Array.isArray(record.blocks) ? record.blocks : [];
  const blocks: DeliaPresentationBlock[] = [];
  for (const rawBlock of rawBlocks.slice(0, MAX_BLOCKS)) {
    if (!rawBlock || typeof rawBlock !== "object") continue;
    const block = rawBlock as Record<string, unknown>;
    if (typeof block.text !== "string") continue;
    const text = block.text.slice(0, MAX_BLOCK_TEXT_CHARS);
    if (block.kind === "text") {
      blocks.push({ kind: "text", text });
    } else if (block.kind === "notice" && block.role === "owner_hint") {
      blocks.push({ kind: "notice", role: "owner_hint", text });
    }
    // Unknown kinds and roles are dropped — closed allowlist.
  }

  const rawInteractions = Array.isArray(record.allowed_interactions)
    ? record.allowed_interactions
    : [];
  const allowedInteractions = rawInteractions.filter(
    (item): item is DeliaAllowedInteraction =>
      typeof item === "string" && KNOWN_INTERACTIONS.has(item),
  );

  return {
    messageKind,
    semanticStatus:
      typeof record.semantic_status === "string"
        ? record.semantic_status
        : null,
    groundingStatus:
      record.grounding_status === "GROUNDED" ||
      record.grounding_status === "NON_GROUNDED"
        ? record.grounding_status
        : null,
    blocks,
    allowedInteractions,
  };
}

/** Bounded owner-hint text when the presentation carries one. */
export function presentationOwnerHint(
  presentation: DeliaPresentation | null,
): string | null {
  if (!presentation) return null;
  const notice = presentation.blocks.find(
    (block) => block.kind === "notice",
  );
  return notice?.kind === "notice" ? notice.text : null;
}

const OWNER_HINT_CONTENT_PREFIX = " A fonte informou: ";

/**
 * The legacy `content` field embeds the owner hint as a
 * `" A fonte informou: <hint>"` suffix while `presentation.blocks`
 * carries the same hint as a `notice` block. When both are present,
 * strip the suffix for display so the hint is shown exactly once.
 * Pure suffix operation — never rewrites owner vocabulary, never
 * touches content that does not carry the exact backend suffix.
 */
export function dedupeOwnerHintContent(
  content: string,
  ownerHint: string | null,
): string {
  if (!ownerHint) return content;
  const suffix = `${OWNER_HINT_CONTENT_PREFIX}${ownerHint}`;
  return content.endsWith(suffix)
    ? content.slice(0, content.length - suffix.length)
    : content;
}
