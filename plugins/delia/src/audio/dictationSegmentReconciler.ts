/**
 * VD-F06 deterministic edit reconciliation for progressive dictation.
 *
 * One reconciler instance tracks a single dictation session's segments
 * against a plain-text draft. Every draft mutation flows through exactly
 * one of two doors:
 *
 *   noteUserEdit(prev, next)  — human edit (type/delete/paste/undo/IME)
 *   applyRevision(...)        — real STT segment revision (partial/final)
 *
 * Anchoring and authority follow the doc-123 §5 decisions:
 *
 * - Each segment captures the caret/selection at segment start; later
 *   caret movement never relocates that segment.
 * - A revision may only rewrite the text range the segment still owns.
 *   Any human edit intersecting an owned range forfeits STT authority —
 *   late revisions are dropped, never clobbering human text.
 * - Human edits outside owned ranges shift anchors by a deterministic
 *   contiguous-diff transform (no stale absolute offsets, no appends).
 * - Duplicate, older or post-final revisions are dropped by revision id;
 *   unknown segments and foreign sessions are dropped by id.
 * - Cancel removes only ranges still owned by unfinished segments;
 *   confirmed text and human edits are preserved (doc-123 case E).
 *
 * Pure module: no DOM, no React, no provider vocabulary — independently
 * testable per the C3 checkpoint.
 */

export type DictationSegmentAnchor = {
  sessionId: string;
  segmentId: string;
  sequence: number;
  /** Caret position (draft index) captured at segment start. */
  anchorStart: number;
  /** Selection end captured at segment start; == anchorStart for a caret. */
  anchorEnd: number;
};

export type ApplyResult = {
  text: string;
  applied: boolean;
  /** True when the applied revision was the segment's final. */
  final: boolean;
  /**
   * The draft range the revision owns after the write. When the user's
   * caret sits exactly at `start`, the host should advance it to `end`
   * — inserting at the caret moves it, exactly like typing. Carets
   * elsewhere are never touched.
   */
  range: { start: number; end: number } | null;
};

type SegmentStatus =
  | "pending" // anchored, no STT text yet
  | "provisional" // owns an inserted range, still revisable
  | "final" // confirmed — becomes plain draft text
  | "userOwned" // human edit intersected; STT authority forfeited
  | "cancelled";

type TrackedSegment = {
  segmentId: string;
  sequence: number;
  status: SegmentStatus;
  /** Anchor captured at segment start (pending segments). */
  anchorStart: number;
  anchorEnd: number;
  /** Inserted range in current draft coordinates (provisional). */
  insStart: number;
  insEnd: number;
  /** Anchor region was edited before first text — insert, never replace. */
  anchorInvalidated: boolean;
  lastRevision: number;
};

export class DictationSegmentReconciler {
  private readonly sessionId: string;
  private readonly segments = new Map<string, TrackedSegment>();

  constructor(sessionId: string) {
    this.sessionId = sessionId;
  }

  beginSegment(anchor: DictationSegmentAnchor): void {
    if (anchor.sessionId !== this.sessionId) return;
    if (this.segments.has(anchor.segmentId)) return;
    this.segments.set(anchor.segmentId, {
      segmentId: anchor.segmentId,
      sequence: anchor.sequence,
      status: "pending",
      anchorStart: Math.max(0, anchor.anchorStart),
      anchorEnd: Math.max(anchor.anchorStart, anchor.anchorEnd),
      insStart: 0,
      insEnd: 0,
      anchorInvalidated: false,
      lastRevision: 0,
    });
  }

  /**
   * Register a human edit (the only caller-supplied draft transition).
   * Computes the contiguous diff prev→next and transforms every tracked
   * anchor/range; intersections forfeit STT authority.
   */
  noteUserEdit(prev: string, next: string): void {
    if (prev === next) return;
    const { start, prevEnd, delta } = contiguousDiff(prev, next);
    this.transformRanges(start, prevEnd, delta, null);
  }

  /**
   * Deterministic range transform for one contiguous change:
   * prev[start..prevEnd) replaced by delta-shifted content. Any segment
   * the change still owns nothing of is shifted; intersections forfeit
   * provisional authority; edits inside a pending anchor region turn its
   * first insert into insert-only (never replace human text).
   */
  private transformRanges(
    start: number,
    prevEnd: number,
    delta: number,
    exceptSegmentId: string | null,
  ): void {
    for (const seg of this.segments.values()) {
      if (seg.segmentId === exceptSegmentId) continue;
      if (seg.status === "final" || seg.status === "cancelled") continue;
      if (seg.status === "provisional") {
        const overlaps = prevEnd > seg.insStart && start < seg.insEnd;
        // Pure insertion exactly at insStart is ambiguous → conservative
        // forfeit (never clobber what the user meant to type first).
        const insertedAtStart = prevEnd === start && start === seg.insStart;
        if (overlaps || insertedAtStart) {
          seg.status = "userOwned";
          continue;
        }
        if (prevEnd <= seg.insStart) {
          seg.insStart += delta;
          seg.insEnd += delta;
        }
        continue;
      }
      // pending or userOwned: transform anchors for edits strictly
      // before them; edits inside the anchor region invalidate replace.
      if (prevEnd <= seg.anchorStart) {
        seg.anchorStart += delta;
        seg.anchorEnd += delta;
      } else if (
        seg.status === "pending" &&
        prevEnd > seg.anchorStart &&
        start < seg.anchorEnd
      ) {
        seg.anchorInvalidated = true;
      }
    }
  }

  /**
   * Apply a real STT revision. Returns the resulting draft text;
   * `applied=false` means the event was safely dropped (duplicate,
   * stale, forfeited, unknown or post-final).
   */
  applyRevision(
    draft: string,
    segmentId: string,
    revision: number,
    text: string,
    isFinal: boolean,
  ): ApplyResult {
    const seg = this.segments.get(segmentId);
    if (
      !seg ||
      seg.status === "cancelled" ||
      seg.status === "final" ||
      seg.status === "userOwned" ||
      revision <= seg.lastRevision
    ) {
      return { text: draft, applied: false, final: false, range: null };
    }
    seg.lastRevision = revision;
    // The segment's own edit mutates the draft too: sibling anchors and
    // owned ranges must shift through the same deterministic transform
    // as a human edit would — otherwise a later STT insert before an
    // owned range silently corrupts it.
    if (seg.status === "pending") {
      const start = clamp(seg.anchorStart, draft.length);
      const end = seg.anchorInvalidated
        ? start
        : clamp(seg.anchorEnd, draft.length);
      this.transformRanges(start, end, text.length - (end - start), segmentId);
      seg.insStart = start;
      seg.insEnd = start + text.length;
      seg.status = isFinal ? "final" : "provisional";
      return {
        text: draft.slice(0, start) + text + draft.slice(end),
        applied: true,
        final: isFinal,
        range: { start, end: start + text.length },
      };
    }
    // provisional: rewrite only the owned range
    const start = clamp(seg.insStart, draft.length);
    const end = clamp(seg.insEnd, draft.length);
    this.transformRanges(start, end, text.length - (end - start), segmentId);
    seg.insEnd = start + text.length;
    if (isFinal) seg.status = "final";
    return {
      text: draft.slice(0, start) + text + draft.slice(end),
      applied: true,
      final: isFinal,
      range: { start, end: start + text.length },
    };
  }

  /**
   * Session cancel: drop text still owned by unfinished segments
   * (pending or provisional — never finalized or human-owned), keep
   * everything else (doc-123 case E).
   */
  cancelSession(draft: string): { text: string } {
    const removable = [...this.segments.values()]
      .filter(
        (s) =>
          s.status === "provisional" ||
          (s.status === "pending" && s.insEnd > s.insStart),
      )
      .sort((a, b) => b.insStart - a.insStart);
    let text = draft;
    for (const seg of removable) {
      const start = clamp(seg.insStart, text.length);
      const end = clamp(seg.insEnd, text.length);
      text = text.slice(0, start) + text.slice(end);
      seg.status = "cancelled";
    }
    for (const seg of this.segments.values()) {
      if (seg.status === "pending") seg.status = "cancelled";
    }
    return { text };
  }

  /** Status snapshot for honest UI (provisional strip / a11y). */
  segmentStatus(segmentId: string): SegmentStatus | undefined {
    return this.segments.get(segmentId)?.status;
  }
}

function contiguousDiff(
  prev: string,
  next: string,
): { start: number; prevEnd: number; nextEnd: number; delta: number } {
  let start = 0;
  const min = Math.min(prev.length, next.length);
  while (start < min && prev[start] === next[start]) start += 1;
  let prevEnd = prev.length;
  let nextEnd = next.length;
  while (
    prevEnd > start &&
    nextEnd > start &&
    prev[prevEnd - 1] === next[nextEnd - 1]
  ) {
    prevEnd -= 1;
    nextEnd -= 1;
  }
  return { start, prevEnd, nextEnd, delta: nextEnd - prevEnd };
}

function clamp(index: number, length: number): number {
  return Math.max(0, Math.min(index, length));
}
