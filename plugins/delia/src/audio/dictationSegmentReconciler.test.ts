/**
 * dictationSegmentReconciler — VD-F06 deterministic edit reconciliation.
 *
 * Reconciles real STT segment events (partial/final revisions) with
 * concurrent human edits on one plain-text draft. Human edits always
 * win: an STT revision may only rewrite the text range it still owns.
 */

import { describe, expect, it } from "vitest";
import { DictationSegmentReconciler } from "./dictationSegmentReconciler";

const S = "sess-1";

function begin(
  r: DictationSegmentReconciler,
  caret: number,
  selectionEnd?: number,
  segmentId = "seg-1",
  sequence = 1,
) {
  r.beginSegment({
    sessionId: S,
    segmentId,
    sequence,
    anchorStart: caret,
    anchorEnd: selectionEnd ?? caret,
  });
}

describe("insert at caret positions", () => {
  it("inserts partial at end caret", () => {
    const r = new DictationSegmentReconciler(S);
    let draft = "Analise os setores.";
    begin(r, draft.length);
    const res = r.applyRevision(draft, "seg-1", 1, "Mais detalhes", false);
    expect(res.text).toBe("Analise os setores.Mais detalhes");
    expect(res.applied).toBe(true);
  });

  it("inserts partial at middle caret (reference case A)", () => {
    const r = new DictationSegmentReconciler(S);
    const draft = "Analise os setores.";
    // caret before "setores" → index 11
    begin(r, 11);
    const res = r.applyRevision(draft, "seg-1", 1, "três principais ", false);
    expect(res.text).toBe("Analise os três principais setores.");
  });

  it("inserts at start caret", () => {
    const r = new DictationSegmentReconciler(S);
    const draft = "setores.";
    begin(r, 0);
    const res = r.applyRevision(draft, "seg-1", 1, "Analise ", false);
    expect(res.text).toBe("Analise setores.");
  });
});

describe("selection replacement", () => {
  it("replaces the captured selection exactly (case D)", () => {
    const r = new DictationSegmentReconciler(S);
    const draft = "dados da última semana aqui";
    // select "última semana" → start 9, end 22
    begin(r, 9, 22);
    const res = r.applyRevision(draft, "seg-1", 1, "último trimestre", true);
    expect(res.text).toBe("dados da último trimestre aqui");
    expect(res.final).toBe(true);
  });

  it("does not re-select when a later revision arrives (anchor fixed)", () => {
    const r = new DictationSegmentReconciler(S);
    let draft = "dados da última semana aqui";
    begin(r, 9, 22);
    draft = r.applyRevision(draft, "seg-1", 1, "último", false).text;
    expect(draft).toBe("dados da último aqui");
    // next revision rewrites only the owned range
    draft = r.applyRevision(draft, "seg-1", 2, "último trimestre", true).text;
    expect(draft).toBe("dados da último trimestre aqui");
  });
});

describe("human edit priority", () => {
  it("late STT revision cannot overwrite a user edit inside the partial (case B)", () => {
    const r = new DictationSegmentReconciler(S);
    let draft = "Analise os setores.";
    begin(r, 11);
    draft = r.applyRevision(draft, "seg-1", 1, "setor ", false).text;
    expect(draft).toBe("Analise os setor setores.");
    // user corrects "setor" to "linha" inside the provisional range
    const prev = draft;
    draft = draft.replace("setor", "linha");
    r.noteUserEdit(prev, draft);
    // late STT revision trying to rewrite "setor" must be dropped
    const res = r.applyRevision(draft, "seg-1", 2, "registro ", true);
    expect(res.applied).toBe(false);
    expect(draft).toContain("linha");
  });

  it("user edit outside the provisional range shifts anchors deterministically", () => {
    const r = new DictationSegmentReconciler(S);
    let draft = "Analise os setores.";
    begin(r, 11);
    draft = r.applyRevision(draft, "seg-1", 1, "três ", false).text;
    expect(draft).toBe("Analise os três setores.");
    // user appends text at the end — outside the provisional range
    const prev = draft;
    draft = prev + " hoje";
    r.noteUserEdit(prev, draft);
    const res = r.applyRevision(draft, "seg-1", 2, "três principais ", true);
    expect(res.applied).toBe(true);
    expect(res.text).toBe("Analise os três principais setores. hoje");
  });

  it("user deletion covering the whole provisional range forfeits it", () => {
    const r = new DictationSegmentReconciler(S);
    let draft = "abc";
    begin(r, 3);
    draft = r.applyRevision(draft, "seg-1", 1, "xyz", false).text;
    expect(draft).toBe("abcxyz");
    const prev = draft;
    draft = "abc";
    r.noteUserEdit(prev, draft);
    const res = r.applyRevision(draft, "seg-1", 2, "xyz final", true);
    expect(res.applied).toBe(false);
    expect(res.text).toBe("abc");
  });
});

describe("caret movement and segment anchoring", () => {
  it("caret movement during a segment does not relocate it (case C)", () => {
    const r = new DictationSegmentReconciler(S);
    let draft = "meio fim";
    // seg-1 anchored at caret 5 (between "meio" and "fim")
    r.beginSegment({
      sessionId: S,
      segmentId: "seg-1",
      sequence: 1,
      anchorStart: 5,
      anchorEnd: 5,
    });
    draft = r.applyRevision(draft, "seg-1", 1, "UM ", false).text;
    expect(draft).toBe("meio UM fim");
    // user moves caret to 0 and starts seg-2
    r.beginSegment({
      sessionId: S,
      segmentId: "seg-2",
      sequence: 2,
      anchorStart: 0,
      anchorEnd: 0,
    });
    draft = r.applyRevision(draft, "seg-2", 1, "INÍCIO ", false).text;
    expect(draft).toBe("INÍCIO meio UM fim");
    // seg-1 final stays at its own anchor
    draft = r.applyRevision(draft, "seg-1", 2, "UM dois ", true).text;
    expect(draft).toBe("INÍCIO meio UM dois fim");
  });
});

describe("duplicate, stale and out-of-order safety", () => {
  it("ignores duplicate or older revisions", () => {
    const r = new DictationSegmentReconciler(S);
    let draft = "";
    begin(r, 0);
    draft = r.applyRevision(draft, "seg-1", 2, "novo", false).text;
    const dup = r.applyRevision(draft, "seg-1", 2, "novo", false);
    expect(dup.applied).toBe(false);
    const stale = r.applyRevision(draft, "seg-1", 1, "velho", false);
    expect(stale.applied).toBe(false);
    expect(draft).toBe("novo");
  });

  it("ignores events from another session or unknown segment", () => {
    const r = new DictationSegmentReconciler(S);
    const draft = "base";
    const res = r.applyRevision(draft, "ghost", 1, "x", false);
    expect(res.applied).toBe(false);
    expect(res.text).toBe("base");
  });

  it("ignores revisions after the segment was finalized", () => {
    const r = new DictationSegmentReconciler(S);
    let draft = "";
    begin(r, 0);
    draft = r.applyRevision(draft, "seg-1", 1, "fim", true).text;
    const late = r.applyRevision(draft, "seg-1", 2, "fim tardio", false);
    expect(late.applied).toBe(false);
    expect(draft).toBe("fim");
  });
});

describe("cancel semantics (case E)", () => {
  it("cancel removes only STT-owned provisional text, keeps confirmed and human edits", () => {
    const r = new DictationSegmentReconciler(S);
    let draft = "início ";
    // seg-1 finalized
    r.beginSegment({
      sessionId: S,
      segmentId: "seg-1",
      sequence: 1,
      anchorStart: draft.length,
      anchorEnd: draft.length,
    });
    draft = r.applyRevision(draft, "seg-1", 1, "confirmado ", true).text;
    // seg-2 still provisional
    r.beginSegment({
      sessionId: S,
      segmentId: "seg-2",
      sequence: 2,
      anchorStart: draft.length,
      anchorEnd: draft.length,
    });
    draft = r.applyRevision(draft, "seg-2", 1, "parcial", false).text;
    expect(draft).toBe("início confirmado parcial");
    // user edits the confirmed part
    const prev = draft;
    draft = prev.replace("confirmado", "editado");
    r.noteUserEdit(prev, draft);
    // cancel → remove only seg-2's owned text
    const res = r.cancelSession(draft);
    expect(res.text).toBe("início editado ");
  });
});

describe("unicode / emoji / multiline", () => {
  it("handles emoji and newlines around anchors", () => {
    const r = new DictationSegmentReconciler(S);
    let draft = "oi 🚀\ntchau";
    begin(r, draft.length);
    const res = r.applyRevision(draft, "seg-1", 1, " até 🎉", false);
    expect(res.text).toBe("oi 🚀\ntchau até 🎉");
  });
});
