import {
  useCallback,
  useEffect,
  useId,
  useLayoutEffect,
  useRef,
  useState,
  type ChangeEvent,
  type KeyboardEvent,
} from "react";

import {
  applyRichTextHtmlAutoClose,
  applyRichTextSourceSuggestion,
  resolveRichTextSourceSuggestions,
  richTextHtmlQuotesBalancedBefore,
  type RichTextSourceSuggestionSession,
} from "./richTextHtmlAssist";
import { RICH_TEXT_LABELS } from "./richTextLabels";

export type RichTextSourceEditorProps = {
  value: string;
  onChange: (next: string) => void;
  minHeight?: number;
  disabled?: boolean;
  /** HTML assist (tags/CSS). Desligado no modo Markdown. */
  assistMode?: "html" | "plain";
  ariaLabel?: string;
  hint?: string;
};

type SuggestionState = RichTextSourceSuggestionSession & {
  activeIndex: number;
};

function suggestionMeta(kind: RichTextSourceSuggestionSession["kind"]): string {
  if (kind === "css-prop") return RICH_TEXT_LABELS.sourceSuggestCss;
  if (kind === "css-value") return RICH_TEXT_LABELS.sourceSuggestCssValue;
  return RICH_TEXT_LABELS.sourceSuggestTag;
}

function suggestionLabel(kind: RichTextSourceSuggestionSession["kind"], item: string): string {
  if (kind === "tag") return `<${item}>`;
  if (kind === "css-prop") return `${item}:`;
  return item;
}

/** Textarea monoespaçado; assist HTML/CSS opcional (modo fonte HTML). */
export function RichTextSourceEditor({
  value,
  onChange,
  minHeight = 200,
  disabled = false,
  assistMode = "html",
  ariaLabel = RICH_TEXT_LABELS.sourceEditor,
  hint = RICH_TEXT_LABELS.sourceHint,
}: RichTextSourceEditorProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const listId = useId();
  const pendingSelectionRef = useRef<{ start: number; end: number } | null>(null);
  const [suggestions, setSuggestions] = useState<SuggestionState | null>(null);
  const htmlAssist = assistMode === "html";

  const syncSuggestions = useCallback(
    (nextValue: string, cursor: number) => {
      if (!htmlAssist) {
        setSuggestions(null);
        return;
      }
      const session = resolveRichTextSourceSuggestions(nextValue, cursor);
      if (!session || session.items.length === 0) {
        setSuggestions(null);
        return;
      }
      setSuggestions({ ...session, activeIndex: 0 });
    },
    [htmlAssist],
  );

  useLayoutEffect(() => {
    const sel = pendingSelectionRef.current;
    const el = textareaRef.current;
    if (!sel || !el) return;
    el.focus();
    el.setSelectionRange(sel.start, sel.end);
    pendingSelectionRef.current = null;
  }, [value]);

  useEffect(() => {
    if (disabled) setSuggestions(null);
  }, [disabled]);

  function commitEdit(next: string, selectionStart: number, selectionEnd: number) {
    pendingSelectionRef.current = { start: selectionStart, end: selectionEnd };
    onChange(next);
    syncSuggestions(next, selectionStart);
  }

  function acceptSuggestion(item: string) {
    const el = textareaRef.current;
    if (!el || !suggestions) return;
    const cursor = el.selectionStart;
    const edit = applyRichTextSourceSuggestion(value, cursor, suggestions, item);
    if (!edit) return;
    setSuggestions(null);
    commitEdit(edit.value, edit.selectionStart, edit.selectionEnd);
  }

  function handleChange(event: ChangeEvent<HTMLTextAreaElement>) {
    const el = event.target;
    const next = el.value;
    const cursor = el.selectionStart;
    onChange(next);

    if (!htmlAssist) {
      setSuggestions(null);
      return;
    }

    if (
      cursor > 0 &&
      next[cursor - 1] === ">" &&
      richTextHtmlQuotesBalancedBefore(next, cursor)
    ) {
      const closed = applyRichTextHtmlAutoClose(next, cursor);
      if (closed) {
        commitEdit(closed.value, closed.selectionStart, closed.selectionEnd);
        return;
      }
    }

    syncSuggestions(next, cursor);
  }

  function handleSelect() {
    if (!htmlAssist) return;
    const el = textareaRef.current;
    if (!el) return;
    syncSuggestions(el.value, el.selectionStart);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (!htmlAssist || !suggestions || suggestions.items.length === 0) return;

    if (event.key === "ArrowDown") {
      event.preventDefault();
      setSuggestions((prev) =>
        prev
          ? { ...prev, activeIndex: (prev.activeIndex + 1) % prev.items.length }
          : prev,
      );
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      setSuggestions((prev) =>
        prev
          ? {
              ...prev,
              activeIndex:
                (prev.activeIndex - 1 + prev.items.length) % prev.items.length,
            }
          : prev,
      );
      return;
    }
    if (event.key === "Enter" || event.key === "Tab") {
      event.preventDefault();
      acceptSuggestion(suggestions.items[suggestions.activeIndex] ?? suggestions.items[0]!);
      return;
    }
    if (event.key === "Escape") {
      event.preventDefault();
      setSuggestions(null);
    }
  }

  const activeItem = suggestions?.items[suggestions.activeIndex];

  return (
    <div className="delpi-ui-rich-text__source-wrap">
      <p className="delpi-ui-rich-text__source-hint" role="note">
        {hint}
      </p>
      <div className="delpi-ui-rich-text__source-shell">
        <textarea
          ref={textareaRef}
          className="delpi-ui-rich-text__source"
          style={{ minHeight }}
          value={value}
          disabled={disabled}
          spellCheck={false}
          aria-label={ariaLabel}
          aria-autocomplete={htmlAssist ? "list" : undefined}
          aria-controls={htmlAssist && suggestions ? listId : undefined}
          aria-expanded={htmlAssist ? Boolean(suggestions) : undefined}
          aria-activedescendant={
            htmlAssist && suggestions && activeItem
              ? `${listId}-${suggestions.kind}-${activeItem}`
              : undefined
          }
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onClick={handleSelect}
          onKeyUp={handleSelect}
        />
        {htmlAssist && suggestions ? (
          <ul
            id={listId}
            className="delpi-ui-rich-text__source-suggest"
            role="listbox"
            aria-label={RICH_TEXT_LABELS.sourceSuggestList}
          >
            {suggestions.items.map((item, index) => {
              const active = index === suggestions.activeIndex;
              const optionId = `${listId}-${suggestions.kind}-${item}`;
              return (
                <li key={optionId} role="presentation">
                  <button
                    type="button"
                    id={optionId}
                    role="option"
                    aria-selected={active}
                    className={[
                      "delpi-ui-rich-text__source-suggest-item",
                      active ? "is-active" : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    onMouseDown={(event) => {
                      event.preventDefault();
                      acceptSuggestion(item);
                    }}
                  >
                    <span className="delpi-ui-rich-text__source-suggest-tag">
                      {suggestionLabel(suggestions.kind, item)}
                    </span>
                    <span className="delpi-ui-rich-text__source-suggest-meta">
                      {suggestionMeta(suggestions.kind)}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        ) : null}
      </div>
    </div>
  );
}
