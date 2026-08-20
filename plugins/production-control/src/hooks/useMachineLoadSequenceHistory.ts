import { useCallback, useEffect, useRef, useState } from "react";

export type SequenceKey = {
  production_order: string;
  operation_code: string;
};

const MAX_STACK = 50;

function sameKeys(a: SequenceKey[], b: SequenceKey[]): boolean {
  if (a.length !== b.length) return false;
  return a.every(
    (item, index) =>
      item.production_order === b[index]?.production_order &&
      item.operation_code === b[index]?.operation_code,
  );
}

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return true;
  return target.isContentEditable;
}

/**
 * Pilha de undo/redo da sequência do CT ativo.
 * Escopo: branch + período + workCenter — limpa ao trocar de contexto.
 */
export function useMachineLoadSequenceHistory(scopeKey: string) {
  const undoRef = useRef<SequenceKey[][]>([]);
  const redoRef = useRef<SequenceKey[][]>([]);
  const [, setTick] = useState(0);
  const scopeRef = useRef(scopeKey);

  const bump = useCallback(() => setTick((value) => value + 1), []);

  useEffect(() => {
    if (scopeRef.current === scopeKey) return;
    scopeRef.current = scopeKey;
    undoRef.current = [];
    redoRef.current = [];
    bump();
  }, [bump, scopeKey]);

  const pushUndo = useCallback(
    (previous: SequenceKey[]) => {
      const last = undoRef.current[undoRef.current.length - 1];
      if (last && sameKeys(last, previous)) return;
      undoRef.current = [...undoRef.current, previous].slice(-MAX_STACK);
      redoRef.current = [];
      bump();
    },
    [bump],
  );

  const undo = useCallback((): SequenceKey[] | null => {
    if (undoRef.current.length === 0) return null;
    const next = [...undoRef.current];
    const restored = next.pop() ?? null;
    undoRef.current = next;
    bump();
    return restored;
  }, [bump]);

  const redo = useCallback((): SequenceKey[] | null => {
    if (redoRef.current.length === 0) return null;
    const next = [...redoRef.current];
    const restored = next.pop() ?? null;
    redoRef.current = next;
    bump();
    return restored;
  }, [bump]);

  const rememberForRedo = useCallback(
    (current: SequenceKey[]) => {
      redoRef.current = [...redoRef.current, current].slice(-MAX_STACK);
      bump();
    },
    [bump],
  );

  const rememberForUndoAfterRedo = useCallback(
    (current: SequenceKey[]) => {
      undoRef.current = [...undoRef.current, current].slice(-MAX_STACK);
      bump();
    },
    [bump],
  );

  /** Limpa undo/redo quando a fila muda fora do CT ativo (ex.: priorização de conjunto). */
  const reset = useCallback(() => {
    undoRef.current = [];
    redoRef.current = [];
    bump();
  }, [bump]);

  const bindKeyboard = useCallback(
    (handlers: { onUndo: () => void; onRedo: () => void }) => {
      const onKeyDown = (event: KeyboardEvent) => {
        if (isEditableTarget(event.target)) return;
        const mod = event.ctrlKey || event.metaKey;
        if (!mod || event.key.toLowerCase() !== "z") return;
        event.preventDefault();
        if (event.shiftKey) handlers.onRedo();
        else handlers.onUndo();
      };
      window.addEventListener("keydown", onKeyDown);
      return () => window.removeEventListener("keydown", onKeyDown);
    },
    [],
  );

  return {
    canUndo: undoRef.current.length > 0,
    canRedo: redoRef.current.length > 0,
    pushUndo,
    undo,
    redo,
    rememberForRedo,
    rememberForUndoAfterRedo,
    reset,
    bindKeyboard,
  };
}

export function keysFromOperations(
  items: Array<{ production_order: string; operation_code: string }>,
): SequenceKey[] {
  return items.map((item) => ({
    production_order: item.production_order,
    operation_code: item.operation_code,
  }));
}

export function applyKeyOrder<T extends { production_order: string; operation_code: string }>(
  items: T[],
  keys: SequenceKey[],
): T[] {
  const byKey = new Map(
    items.map((item) => [`${item.production_order}|${item.operation_code}`, item] as const),
  );
  const ordered: T[] = [];
  for (const key of keys) {
    const hit = byKey.get(`${key.production_order}|${key.operation_code}`);
    if (hit) ordered.push(hit);
  }
  return ordered.length === items.length ? ordered : items;
}
