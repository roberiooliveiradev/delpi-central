import { useCallback, useMemo, useState } from "react";

import { valuesEqual } from "../utils/valuesEqual";

function cloneValue<T>(value: T): T {
  if (typeof structuredClone === "function") {
    return structuredClone(value);
  }
  return JSON.parse(JSON.stringify(value)) as T;
}

export type EditableDraft<T> = {
  value: T;
  setValue: (next: T | ((current: T) => T)) => void;
  dirty: boolean;
  /** Substitui valor e baseline (após load / cancelar). */
  replace: (next: T) => void;
  /** Congela o valor atual como baseline (após save bem-sucedido). */
  markSaved: (next?: T) => void;
  /** Volta o valor para o baseline. */
  reset: () => void;
};

/**
 * Draft editável com detecção centralizada de `dirty` (baseline × valor atual).
 *
 * Ao cancelar edição num `EditableSectionCard`, o kit remonta o conteúdo
 * (`key` read/edit) para descartar o draft. Em formulários no pai, o `onCancel`
 * deve chamar `reset()` / restaurar o baseline explicitamente.
 */
export function useEditableDraft<T>(initial: T): EditableDraft<T> {
  const [baseline, setBaseline] = useState<T>(() => cloneValue(initial));
  const [value, setValueState] = useState<T>(() => cloneValue(initial));

  const setValue = useCallback((next: T | ((current: T) => T)) => {
    setValueState((current) =>
      typeof next === "function" ? (next as (current: T) => T)(current) : next
    );
  }, []);

  const replace = useCallback((next: T) => {
    const cloned = cloneValue(next);
    setBaseline(cloned);
    setValueState(cloned);
  }, []);

  const markSaved = useCallback((next?: T) => {
    setValueState((current) => {
      const saved = cloneValue(next !== undefined ? next : current);
      setBaseline(saved);
      return saved;
    });
  }, []);

  const reset = useCallback(() => {
    setValueState(cloneValue(baseline));
  }, [baseline]);

  const dirty = useMemo(() => !valuesEqual(value, baseline), [baseline, value]);

  return useMemo(
    () => ({ value, setValue, dirty, replace, markSaved, reset }),
    [dirty, markSaved, replace, reset, setValue, value]
  );
}
