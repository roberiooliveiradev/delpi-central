import { useCallback, useEffect, useState } from "react";

import {
  SUPPLIES_FILTER_TEXT_DEBOUNCE_MS,
  useDebouncedValue,
} from "./useDebouncedValue";

/**
 * Draft text in the UI; commits to the query after debounce (or flush / Enter).
 * URL and fetch should depend only on the committed value.
 */
export function useCommittedTextFilter(
  committed: string,
  onCommit: (value: string) => void,
  delayMs = SUPPLIES_FILTER_TEXT_DEBOUNCE_MS,
) {
  const [draft, setDraft] = useState(committed);
  const debounced = useDebouncedValue(draft, delayMs);

  useEffect(() => {
    setDraft(committed);
  }, [committed]);

  useEffect(() => {
    if (debounced === committed) return;
    onCommit(debounced);
  }, [committed, debounced, onCommit]);

  const flush = useCallback(() => {
    if (draft === committed) return;
    onCommit(draft);
  }, [committed, draft, onCommit]);

  return { draft, setDraft, flush };
}
