/**
 * Interaction Presentation adapter — DELIA-UX-S1-PRESENTATION-ADAPTER-01
 * + presentation.v2 reader (parse-only, CP-333 frontend readiness).
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
 *
 * presentation.v2 is a TARGET contract reader: the MFE may admit
 * markdown_safe only when the wire declares version "2" + format
 * explicitly. The producer is NOT implemented in backend yet; fixtures
 * exercise the reader. Unknown versions never coerce into v2.
 */

export const PRESENTATION_CONTRACT_VERSION = "1";
export const PRESENTATION_CONTRACT_VERSION_V2 = "2";

export type DeliaTextFormat = "plain" | "markdown_safe";

/** Canonical message kinds — the exact GovernedCapabilityStatus-derived
 *  vocabulary published by the backend. Never extended client-side. */
export type DeliaMessageKind =
  | "RESULT"
  | "CLARIFICATION_REQUIRED"
  | "CONFIRMATION_REQUIRED"
  | "WRITE_REJECTED"
  | "AUTHZ_DENIED"
  | "SOURCE_UNAVAILABLE"
  | "PRECONDITION_REQUIRED"
  | "PROCESSING_TIMEOUT";

const KNOWN_MESSAGE_KINDS: ReadonlySet<string> = new Set<string>([
  "RESULT",
  "CLARIFICATION_REQUIRED",
  "CONFIRMATION_REQUIRED",
  "WRITE_REJECTED",
  "AUTHZ_DENIED",
  "SOURCE_UNAVAILABLE",
  "PRECONDITION_REQUIRED",
  "PROCESSING_TIMEOUT",
]);

/** Closed block allowlist — mirrors the backend emit set. Any other
 *  kind is dropped silently; unknown notice roles are dropped too. */
export type DeliaPresentationBlock =
  | { kind: "text"; text: string; format?: DeliaTextFormat }
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

const V2_ENVELOPE_KEYS = new Set([
  "version",
  "message_kind",
  "semantic_status",
  "grounding_status",
  "blocks",
  "allowed_interactions",
]);
const V2_TEXT_BLOCK_KEYS = new Set(["kind", "format", "text"]);
const V2_NOTICE_BLOCK_KEYS = new Set(["kind", "role", "text"]);
const V2_FORMATS: ReadonlySet<string> = new Set(["plain", "markdown_safe"]);

function hasOnlyKeys(
  record: Record<string, unknown>,
  allowed: ReadonlySet<string>,
): boolean {
  return Object.keys(record).every((key) => allowed.has(key));
}

export type PresentationV2ParseResult =
  | { status: "not_v2" }
  | { status: "neutral_error" }
  | { status: "ok"; presentation: DeliaPresentation };

/**
 * Parse-only reader for presentation.v2 (doc 84 proposal schema).
 *
 * - not_v2 → caller uses parsePresentation (v1) or legacy content
 * - neutral_error → structurally invalid v2 (no silent downgrade)
 * - ok → closed allowlist admitted; format required on text blocks
 *
 * Does not invent authorized links. Does not activate Markdown by itself —
 * the host enables ConversationMarkdown only when a text block carries
 * format markdown_safe.
 */
export function parsePresentationV2(raw: unknown): PresentationV2ParseResult {
  if (!raw || typeof raw !== "object") return { status: "not_v2" };
  const record = raw as Record<string, unknown>;
  if (record.version !== PRESENTATION_CONTRACT_VERSION_V2) {
    return { status: "not_v2" };
  }
  if (!hasOnlyKeys(record, V2_ENVELOPE_KEYS)) {
    return { status: "neutral_error" };
  }
  if (!Array.isArray(record.blocks) || record.blocks.length === 0) {
    return { status: "neutral_error" };
  }
  if (record.blocks.length > MAX_BLOCKS) {
    return { status: "neutral_error" };
  }
  if (!Array.isArray(record.allowed_interactions)) {
    return { status: "neutral_error" };
  }

  const rawKind =
    typeof record.message_kind === "string" ? record.message_kind : "";
  if (!KNOWN_MESSAGE_KINDS.has(rawKind)) {
    return { status: "neutral_error" };
  }

  if (
    record.grounding_status !== "GROUNDED" &&
    record.grounding_status !== "NON_GROUNDED"
  ) {
    return { status: "neutral_error" };
  }

  if (
    !(
      record.semantic_status === null ||
      typeof record.semantic_status === "string"
    )
  ) {
    return { status: "neutral_error" };
  }

  const blocks: DeliaPresentationBlock[] = [];
  for (const rawBlock of record.blocks) {
    if (!rawBlock || typeof rawBlock !== "object") {
      return { status: "neutral_error" };
    }
    const block = rawBlock as Record<string, unknown>;
    if (typeof block.text !== "string") {
      return { status: "neutral_error" };
    }
    if (block.text.length > MAX_BLOCK_TEXT_CHARS) {
      return { status: "neutral_error" };
    }
    if (block.kind === "text") {
      if (!hasOnlyKeys(block, V2_TEXT_BLOCK_KEYS)) {
        return { status: "neutral_error" };
      }
      if (typeof block.format !== "string" || !V2_FORMATS.has(block.format)) {
        return { status: "neutral_error" };
      }
      blocks.push({
        kind: "text",
        format: block.format as DeliaTextFormat,
        text: block.text,
      });
    } else if (block.kind === "notice") {
      if (!hasOnlyKeys(block, V2_NOTICE_BLOCK_KEYS)) {
        return { status: "neutral_error" };
      }
      if (block.role !== "owner_hint") {
        return { status: "neutral_error" };
      }
      blocks.push({ kind: "notice", role: "owner_hint", text: block.text });
    } else {
      return { status: "neutral_error" };
    }
  }

  if (record.allowed_interactions.length === 0) {
    return { status: "neutral_error" };
  }
  const allowedInteractions: DeliaAllowedInteraction[] = [];
  const seen = new Set<string>();
  for (const item of record.allowed_interactions) {
    if (typeof item !== "string" || !KNOWN_INTERACTIONS.has(item)) {
      return { status: "neutral_error" };
    }
    if (seen.has(item)) return { status: "neutral_error" };
    seen.add(item);
    allowedInteractions.push(item as DeliaAllowedInteraction);
  }

  return {
    status: "ok",
    presentation: {
      messageKind: rawKind as DeliaMessageKind,
      semanticStatus:
        typeof record.semantic_status === "string"
          ? record.semantic_status
          : null,
      groundingStatus: record.grounding_status,
      blocks,
      allowedInteractions,
    },
  };
}

/** First admitted text-block format; defaults to plain when absent (v1). */
export function presentationPrimaryTextFormat(
  presentation: DeliaPresentation | null,
): DeliaTextFormat {
  if (!presentation) return "plain";
  const textBlock = presentation.blocks.find((block) => block.kind === "text");
  if (textBlock?.kind === "text" && textBlock.format === "markdown_safe") {
    return "markdown_safe";
  }
  return "plain";
}

/** Markdown source from the first markdown_safe text block, if any. */
export function presentationMarkdownSource(
  presentation: DeliaPresentation | null,
): string | null {
  if (!presentation) return null;
  const textBlock = presentation.blocks.find(
    (block) => block.kind === "text" && block.format === "markdown_safe",
  );
  return textBlock?.kind === "text" ? textBlock.text : null;
}
