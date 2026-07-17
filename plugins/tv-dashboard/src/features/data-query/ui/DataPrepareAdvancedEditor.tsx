import { NativeTextAreaControl } from "@delpi/plugin-ui/index";
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";

import type { DataQueryCompileResult, DataQueryFunction } from "../domain/dataQueryTypes";

type Suggestion = {
  id: string;
  label: string;
  insertText: string;
  kind: string;
  detail?: DataQueryFunction;
};

type Props = {
  open: boolean;
  script: string;
  compiled: DataQueryCompileResult | null;
  functions: DataQueryFunction[];
  loadingFunctions: boolean;
  canUndo: boolean;
  canRedo: boolean;
  onChange: (script: string) => void;
  onCompile: (script: string) => Promise<unknown>;
  onFormat: () => Promise<unknown>;
  onUndo: () => void;
  onRedo: () => void;
  onClose: () => void;
};

function completionStart(value: string, caret: number): number {
  let start = caret;
  while (start > 0 && /[\p{L}\p{N}_#."]/u.test(value[start - 1] ?? "")) start -= 1;
  return start;
}

function highlightedScript(script: string, compiled: DataQueryCompileResult | null) {
  const tokens =
    compiled?.canonicalScript === script
      ? [...compiled.syntaxTokens].sort((a, b) => a.startOffset - b.startOffset)
      : [];
  if (tokens.length === 0) return script;
  const parts: ReactNode[] = [];
  let cursor = 0;
  tokens.forEach((token, index) => {
    if (token.startOffset < cursor || token.endOffset > script.length) return;
    parts.push(script.slice(cursor, token.startOffset));
    parts.push(
      <span key={`${token.startOffset}-${index}`} className={`td-data-pq__token--${token.kind}`}>
        {script.slice(token.startOffset, token.endOffset)}
      </span>,
    );
    cursor = token.endOffset;
  });
  parts.push(script.slice(cursor));
  return parts;
}

export function DataPrepareAdvancedEditor({
  open,
  script,
  compiled,
  functions,
  loadingFunctions,
  canUndo,
  canRedo,
  onChange,
  onCompile,
  onFormat,
  onUndo,
  onRedo,
  onClose,
}: Props) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const highlightRef = useRef<HTMLPreElement>(null);
  const [suggestionsOpen, setSuggestionsOpen] = useState(false);
  const [selectedSuggestion, setSelectedSuggestion] = useState(0);
  const [completion, setCompletion] = useState({ start: 0, end: 0, prefix: "" });

  const suggestions = useMemo<Suggestion[]>(() => {
    const functionItems = functions
      .filter((item) => item.availability.advancedEditor)
      .map((item) => ({
        id: `function-${item.name}`,
        label: item.name,
        insertText: item.name,
        kind: "função",
        detail: item,
      }));
    const contextItems = (compiled?.completionContext.items ?? []).map((item) => ({
      id: `${item.kind}-${item.label}`,
      label: item.label,
      insertText: item.insertText,
      kind:
        item.kind === "column" ? "coluna" : item.kind === "query" ? "consulta" : "etapa",
    }));
    const prefix = completion.prefix.toLocaleLowerCase("pt-BR");
    return [...functionItems, ...contextItems]
      .filter((item) => !prefix || item.label.toLocaleLowerCase("pt-BR").startsWith(prefix))
      .slice(0, 40);
  }, [compiled?.completionContext.items, completion.prefix, functions]);

  useEffect(() => {
    if (!open) return;
    textareaRef.current?.focus();
  }, [open]);

  useEffect(() => {
    setSelectedSuggestion((current) => Math.min(current, Math.max(0, suggestions.length - 1)));
  }, [suggestions.length]);

  if (!open) return null;

  const requestSuggestions = () => {
    const textarea = textareaRef.current;
    const end = textarea?.selectionStart ?? script.length;
    const start = completionStart(script, end);
    setCompletion({ start, end, prefix: script.slice(start, end).replace(/^#"/, "") });
    setSelectedSuggestion(0);
    setSuggestionsOpen(true);
  };

  const chooseSuggestion = (suggestion: Suggestion) => {
    const next =
      script.slice(0, completion.start) + suggestion.insertText + script.slice(completion.end);
    const caret = completion.start + suggestion.insertText.length;
    onChange(next);
    setSuggestionsOpen(false);
    requestAnimationFrame(() => {
      textareaRef.current?.focus();
      textareaRef.current?.setSelectionRange(caret, caret);
    });
  };

  const navigateDiagnostic = (index: number) => {
    const range = compiled?.diagnostics[index]?.range;
    if (!range) return;
    textareaRef.current?.focus();
    textareaRef.current?.setSelectionRange(range.startOffset, range.endOffset);
  };

  return (
    <section className="td-data-pq__advanced" aria-label="Editor avançado M">
      <header className="td-data-pq__advanced-toolbar">
        <strong>Editor avançado</strong>
        <span className="td-data-pq__advanced-status" role="status">
          {loadingFunctions ? "Carregando catálogo…" : `${functions.length} funções disponíveis`}
        </span>
        <button type="button" className="td-btn td-btn--sm td-btn--ghost" disabled={!canUndo} onClick={onUndo}>
          Desfazer
        </button>
        <button type="button" className="td-btn td-btn--sm td-btn--ghost" disabled={!canRedo} onClick={onRedo}>
          Refazer
        </button>
        <button type="button" className="td-btn td-btn--sm td-btn--ghost" onClick={() => void onFormat()}>
          Formatar
        </button>
        <button type="button" className="td-btn td-btn--sm" onClick={() => void onCompile(script)}>
          Aplicar/compilar
        </button>
        <button type="button" className="td-btn td-btn--sm td-btn--ghost" onClick={onClose}>
          Fechar
        </button>
      </header>
      <div className="td-data-pq__editor-shell">
        <pre ref={highlightRef} className="td-data-pq__editor-highlight" aria-hidden>
          {highlightedScript(script, compiled)}
        </pre>
        <NativeTextAreaControl
          ref={textareaRef}
          value={script}
          onChange={onChange}
          className="td-data-pq__editor-input"
          aria-label="Script M"
          aria-autocomplete="list"
          aria-controls="td-m-suggestions"
          aria-expanded={suggestionsOpen}
          aria-activedescendant={
            suggestionsOpen && suggestions[selectedSuggestion]
              ? `td-m-suggestion-${suggestions[selectedSuggestion].id}`
              : undefined
          }
          spellCheck={false}
          onScroll={(event) => {
            if (!highlightRef.current) return;
            highlightRef.current.scrollTop = event.currentTarget.scrollTop;
            highlightRef.current.scrollLeft = event.currentTarget.scrollLeft;
          }}
          onKeyDown={(event) => {
            const mod = event.ctrlKey || event.metaKey;
            if (mod && event.key === " ") {
              event.preventDefault();
              requestSuggestions();
            } else if (mod && event.key.toLowerCase() === "z") {
              event.preventDefault();
              if (event.shiftKey) onRedo();
              else onUndo();
            } else if (mod && event.key.toLowerCase() === "y") {
              event.preventDefault();
              onRedo();
            } else if (mod && event.key === "Enter") {
              event.preventDefault();
              void onCompile(script);
            } else if (event.key === "Escape") {
              event.preventDefault();
              if (suggestionsOpen) setSuggestionsOpen(false);
              else onClose();
            } else if (suggestionsOpen && event.key === "ArrowDown") {
              event.preventDefault();
              setSelectedSuggestion((value) => Math.min(value + 1, suggestions.length - 1));
            } else if (suggestionsOpen && event.key === "ArrowUp") {
              event.preventDefault();
              setSelectedSuggestion((value) => Math.max(value - 1, 0));
            } else if (suggestionsOpen && (event.key === "Enter" || event.key === "Tab")) {
              const suggestion = suggestions[selectedSuggestion];
              if (suggestion) {
                event.preventDefault();
                chooseSuggestion(suggestion);
              }
            }
          }}
        />
        {suggestionsOpen ? (
          <div id="td-m-suggestions" className="td-data-pq__suggestions" role="listbox" aria-label="Sugestões M">
            {suggestions.length === 0 ? (
              <p>Nenhuma sugestão para este prefixo.</p>
            ) : (
              suggestions.map((suggestion, index) => (
                <button
                  id={`td-m-suggestion-${suggestion.id}`}
                  key={suggestion.id}
                  type="button"
                  role="option"
                  aria-selected={index === selectedSuggestion}
                  className={
                    index === selectedSuggestion
                      ? "td-data-pq__suggestion td-data-pq__suggestion--selected"
                      : "td-data-pq__suggestion"
                  }
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => chooseSuggestion(suggestion)}
                >
                  <strong>{suggestion.label}</strong>
                  <span>{suggestion.kind}</span>
                  {suggestion.detail ? (
                    <small>
                      {suggestion.detail.signature} — {suggestion.detail.description}
                      {suggestion.detail.examples[0] ? ` Ex.: ${suggestion.detail.examples[0]}` : ""}
                    </small>
                  ) : null}
                </button>
              ))
            )}
          </div>
        ) : null}
      </div>
      {compiled?.diagnostics.length ? (
        <div className="td-data-pq__advanced-diagnostics" aria-label="Navegação de diagnósticos">
          {compiled.diagnostics.map((diagnostic, index) => (
            <button
              key={`${diagnostic.code}-${index}`}
              type="button"
              onClick={() => navigateDiagnostic(index)}
            >
              {diagnostic.code}
              {diagnostic.range
                ? ` · L${diagnostic.range.startLine}:C${diagnostic.range.startColumn}`
                : ""}
              {" — "}
              {diagnostic.message}
            </button>
          ))}
        </div>
      ) : null}
    </section>
  );
}
