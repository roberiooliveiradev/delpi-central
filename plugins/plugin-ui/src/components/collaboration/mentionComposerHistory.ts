/** Pilha undo/redo do MentionComposer — snapshots markdown+html (semântica TV commitWithHistory). */

export const MENTION_COMPOSER_HISTORY_LIMIT = 50;

export type MentionComposerHistorySnapshot = {
  markdown: string;
  /** HTML do contenteditable — restauração fiel (markdown **texto.** pode falhar no marked). */
  html: string;
  cursor: number;
};

export type MentionComposerHistory = {
  commit: (before: MentionComposerHistorySnapshot, after: MentionComposerHistorySnapshot) => boolean;
  /** Empilha `before` se diferente do topo; limpa future. */
  pushBefore: (before: MentionComposerHistorySnapshot) => boolean;
  undo: (current: MentionComposerHistorySnapshot) => MentionComposerHistorySnapshot | null;
  redo: (current: MentionComposerHistorySnapshot) => MentionComposerHistorySnapshot | null;
  clear: () => void;
  canUndo: () => boolean;
  canRedo: () => boolean;
  pastLength: () => number;
  futureLength: () => number;
};

export function fingerprintMentionComposerSnapshot(
  snapshot: MentionComposerHistorySnapshot,
): string {
  return `${snapshot.markdown}\0${snapshot.html}\0${snapshot.cursor}`;
}

export function snapshotsEqual(
  a: MentionComposerHistorySnapshot,
  b: MentionComposerHistorySnapshot,
): boolean {
  return fingerprintMentionComposerSnapshot(a) === fingerprintMentionComposerSnapshot(b);
}

export function createMentionComposerHistory(
  limit = MENTION_COMPOSER_HISTORY_LIMIT,
): MentionComposerHistory {
  const safeLimit = Math.max(1, Math.floor(limit));
  let past: MentionComposerHistorySnapshot[] = [];
  let future: MentionComposerHistorySnapshot[] = [];

  const clone = (s: MentionComposerHistorySnapshot): MentionComposerHistorySnapshot => ({
    markdown: s.markdown,
    html: s.html,
    cursor: s.cursor,
  });

  const pushPast = (snapshot: MentionComposerHistorySnapshot) => {
    past = [...past.slice(-(safeLimit - 1)), clone(snapshot)];
    future = [];
  };

  return {
    commit(before, after) {
      if (snapshotsEqual(before, after)) return false;
      pushPast(before);
      return true;
    },
    pushBefore(before) {
      const top = past[past.length - 1];
      if (top && snapshotsEqual(top, before)) return false;
      pushPast(before);
      return true;
    },
    undo(current) {
      const previous = past.pop();
      if (!previous) return null;
      future.push(clone(current));
      return clone(previous);
    },
    redo(current) {
      const next = future.pop();
      if (!next) return null;
      past.push(clone(current));
      return clone(next);
    },
    clear() {
      past = [];
      future = [];
    },
    canUndo: () => past.length > 0,
    canRedo: () => future.length > 0,
    pastLength: () => past.length,
    futureLength: () => future.length,
  };
}
