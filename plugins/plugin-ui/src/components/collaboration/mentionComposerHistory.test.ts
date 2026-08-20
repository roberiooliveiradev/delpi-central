import { describe, expect, it } from "vitest";

import {
  createMentionComposerHistory,
  MENTION_COMPOSER_HISTORY_LIMIT,
  snapshotsEqual,
} from "./mentionComposerHistory";

function snap(markdown: string, html = markdown, cursor = markdown.length) {
  return { markdown, html, cursor };
}

describe("createMentionComposerHistory", () => {
  it("commit → undo → redo restaura snapshots", () => {
    const history = createMentionComposerHistory();
    const v1 = snap("ola", "ola");
    const v2 = snap("**ola**", "<strong>ola</strong>");
    expect(history.commit(v1, v2)).toBe(true);
    expect(history.canUndo()).toBe(true);
    expect(history.canRedo()).toBe(false);

    const undone = history.undo(v2);
    expect(undone).toEqual(v1);
    expect(history.canRedo()).toBe(true);

    const redone = history.redo(v1);
    expect(redone).toEqual(v2);
    expect(history.canUndo()).toBe(true);
  });

  it("no-op quando before === after", () => {
    const history = createMentionComposerHistory();
    const v1 = snap("mesmo");
    expect(history.commit(v1, snap("mesmo"))).toBe(false);
    expect(history.pastLength()).toBe(0);
  });

  it("novo commit limpa future", () => {
    const history = createMentionComposerHistory();
    history.commit(snap("a"), snap("b"));
    history.undo(snap("b"));
    expect(history.canRedo()).toBe(true);
    history.commit(snap("a"), snap("c"));
    expect(history.canRedo()).toBe(false);
    expect(history.pastLength()).toBe(1);
  });

  it("respeita limite de past", () => {
    const history = createMentionComposerHistory(3);
    history.commit(snap("0"), snap("1"));
    history.commit(snap("1"), snap("2"));
    history.commit(snap("2"), snap("3"));
    history.commit(snap("3"), snap("4"));
    expect(history.pastLength()).toBe(3);
    expect(history.undo(snap("4"))).toEqual(snap("3"));
    expect(history.undo(snap("3"))).toEqual(snap("2"));
    expect(history.undo(snap("2"))).toEqual(snap("1"));
    expect(history.undo(snap("1"))).toBeNull();
  });

  it("pushBefore não duplica o mesmo topo", () => {
    const history = createMentionComposerHistory();
    expect(history.pushBefore(snap("x"))).toBe(true);
    expect(history.pushBefore(snap("x"))).toBe(false);
    expect(history.pastLength()).toBe(1);
  });

  it("clear zera past e future", () => {
    const history = createMentionComposerHistory();
    history.commit(snap("a"), snap("b"));
    history.undo(snap("b"));
    history.clear();
    expect(history.canUndo()).toBe(false);
    expect(history.canRedo()).toBe(false);
  });

  it("snapshotsEqual ignora referência", () => {
    expect(snapshotsEqual(snap("a", "a", 1), { markdown: "a", html: "a", cursor: 1 })).toBe(
      true,
    );
    expect(snapshotsEqual(snap("a", "a", 1), snap("a", "a", 2))).toBe(false);
    expect(snapshotsEqual(snap("a", "<b>a</b>", 1), snap("a", "a", 1))).toBe(false);
  });

  it("limite default é 50", () => {
    expect(MENTION_COMPOSER_HISTORY_LIMIT).toBe(50);
  });
});
