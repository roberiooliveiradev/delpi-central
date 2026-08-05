import { ExternalLink, Pencil, Unlink } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { RichTextLinkDialog } from "./RichTextLinkDialog";
import { RichTextSourceEditor } from "./RichTextSourceEditor";
import { RichTextToolbar } from "./RichTextToolbar";
import {
  applyRichTextLinkAtRange,
  execRichTextCommand,
  findRichTextLinkAtSelection,
  normalizeRichTextLinkUrl,
  unwrapRichTextLink,
} from "./richTextCommands";
import { tryDeleteRichTextAtEmphasisBoundary } from "./richTextDeleteBoundary";
import { prettyPrintRichTextHtml, stripDangerousRichTextTags } from "./richTextHtmlFormat";
import { RICH_TEXT_LABELS } from "./richTextLabels";
import { normalizeRichTextPastedHtml } from "./richTextTable";

export type RichTextEditorMode = "edit" | "preview";

export type RichTextEditorProps = {
  value: string;
  onChange: (next: string) => void;
  mode?: RichTextEditorMode;
  disabled?: boolean;
  className?: string;
  ariaLabel?: string;
  /** Escopo CSS do host para portais (select/cor/modal de link). Ex.: `dashboard-cipa`. */
  portalScopeClassName?: string;
  minHeight?: number;
};

type LinkDialogState =
  | { mode: "create"; range: Range | null }
  | { mode: "edit"; element: HTMLAnchorElement };

type ActiveLinkState = {
  element: HTMLAnchorElement;
  href: string;
  top: number;
  left: number;
};

const SOURCE_CHANGE_DEBOUNCE_MS = 150;

export function RichTextEditor({
  value,
  onChange,
  mode = "edit",
  disabled = false,
  className,
  ariaLabel = "Editor de texto",
  portalScopeClassName,
  minHeight = 200,
}: RichTextEditorProps) {
  const rootRef = useRef<HTMLDivElement>(null);
  const ref = useRef<HTMLDivElement>(null);
  const focusedRef = useRef(false);
  const sourceDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [sourceMode, setSourceMode] = useState(false);
  const [sourceDraft, setSourceDraft] = useState("");
  const [linkDialog, setLinkDialog] = useState<LinkDialogState | null>(null);
  const [activeLink, setActiveLink] = useState<ActiveLinkState | null>(null);
  const rootClass = useMemo(
    () => ["delpi-ui-rich-text", className].filter(Boolean).join(" "),
    [className],
  );

  const resolvedHtml = useMemo(() => {
    const raw = value || "<p></p>";
    if (!/<table[\s>]/i.test(raw)) return raw;
    return normalizeRichTextPastedHtml(raw) || raw;
  }, [value]);

  useEffect(() => {
    if (mode !== "edit" || disabled || sourceMode || !ref.current || focusedRef.current) {
      return;
    }
    if (ref.current.innerHTML !== resolvedHtml) {
      ref.current.innerHTML = resolvedHtml;
    }
  }, [mode, disabled, sourceMode, resolvedHtml]);

  useEffect(() => {
    return () => {
      if (sourceDebounceRef.current) clearTimeout(sourceDebounceRef.current);
    };
  }, []);

  /** Badge segue o link sob o cursor/seleção (posição relativa ao root). */
  const syncActiveLink = useCallback(() => {
    const editorEl = ref.current;
    const rootEl = rootRef.current;
    if (!editorEl || !rootEl) {
      setActiveLink(null);
      return;
    }
    const anchor = findRichTextLinkAtSelection(editorEl);
    if (!anchor) {
      setActiveLink(null);
      return;
    }
    const rect = anchor.getBoundingClientRect();
    const rootRect = rootEl.getBoundingClientRect();
    setActiveLink({
      element: anchor,
      href: anchor.getAttribute("href") ?? "",
      top: rect.bottom - rootRect.top + 6,
      left: Math.max(8, rect.left - rootRect.left),
    });
  }, []);

  const emitChange = useCallback(() => {
    onChange(ref.current?.innerHTML || "");
  }, [onChange]);

  const flushSourceDraft = useCallback(
    (draft: string) => {
      const cleaned = stripDangerousRichTextTags(draft);
      onChange(cleaned);
      return cleaned;
    },
    [onChange],
  );

  function handleSourceDraftChange(next: string) {
    setSourceDraft(next);
    if (sourceDebounceRef.current) clearTimeout(sourceDebounceRef.current);
    sourceDebounceRef.current = setTimeout(() => {
      flushSourceDraft(next);
    }, SOURCE_CHANGE_DEBOUNCE_MS);
  }

  function handleToggleSource() {
    if (disabled) return;
    if (sourceDebounceRef.current) {
      clearTimeout(sourceDebounceRef.current);
      sourceDebounceRef.current = null;
    }

    if (!sourceMode) {
      const current = ref.current?.innerHTML || value || "<p></p>";
      focusedRef.current = false;
      setActiveLink(null);
      setLinkDialog(null);
      setSourceDraft(prettyPrintRichTextHtml(current));
      setSourceMode(true);
      return;
    }

    const cleaned = flushSourceDraft(sourceDraft);
    setSourceMode(false);
    requestAnimationFrame(() => {
      if (ref.current) {
        ref.current.innerHTML = cleaned;
      }
    });
  }

  function handleRequestLink() {
    if (sourceMode) return;
    const editorEl = ref.current;
    if (!editorEl) return;
    const anchor = findRichTextLinkAtSelection(editorEl);
    if (anchor) {
      setLinkDialog({ mode: "edit", element: anchor });
      return;
    }
    const selection = window.getSelection();
    const range =
      selection &&
      selection.rangeCount > 0 &&
      editorEl.contains(selection.getRangeAt(0).commonAncestorContainer)
        ? selection.getRangeAt(0).cloneRange()
        : null;
    setLinkDialog({ mode: "create", range });
  }

  function handleLinkSubmit(url: string) {
    const editorEl = ref.current;
    if (!editorEl || !linkDialog) return;
    const normalized = normalizeRichTextLinkUrl(url);
    if (!normalized) return;
    if (linkDialog.mode === "edit") {
      linkDialog.element.setAttribute("href", normalized);
    } else {
      applyRichTextLinkAtRange(editorEl, linkDialog.range, normalized);
    }
    setLinkDialog(null);
    emitChange();
    syncActiveLink();
  }

  function handleLinkRemove() {
    if (!activeLink) return;
    unwrapRichTextLink(activeLink.element);
    setActiveLink(null);
    emitChange();
  }

  if (mode === "preview" || disabled) {
    return (
      <div
        className={`${rootClass} delpi-ui-rich-text--preview`}
        style={{ minHeight }}
        dangerouslySetInnerHTML={{ __html: resolvedHtml }}
      />
    );
  }

  return (
    <div className={rootClass} ref={rootRef}>
      <RichTextToolbar
        editorRef={ref}
        disabled={disabled}
        sourceMode={sourceMode}
        onToggleSource={handleToggleSource}
        portalScopeClassName={portalScopeClassName}
        onFormatted={emitChange}
        onRequestLink={handleRequestLink}
      />
      {sourceMode ? (
        <RichTextSourceEditor
          value={sourceDraft}
          onChange={handleSourceDraftChange}
          minHeight={minHeight}
          disabled={disabled}
        />
      ) : (
        <div
          ref={ref}
          className="delpi-ui-rich-text__editor"
          style={{ minHeight }}
          contentEditable
          role="textbox"
          aria-multiline="true"
          aria-label={ariaLabel}
          suppressContentEditableWarning
          onFocus={() => {
            focusedRef.current = true;
          }}
          onBlur={() => {
            focusedRef.current = false;
            setActiveLink(null);
            emitChange();
          }}
          onInput={emitChange}
          onMouseUp={syncActiveLink}
          onKeyUp={syncActiveLink}
          onBeforeInput={(event) => {
            const inputType = event.nativeEvent.inputType;
            if (
              inputType !== "deleteContentBackward" &&
              inputType !== "deleteContentForward"
            ) {
              return;
            }
            const editorEl = ref.current;
            if (!editorEl) return;
            const direction =
              inputType === "deleteContentBackward" ? "backward" : "forward";
            if (tryDeleteRichTextAtEmphasisBoundary(editorEl, direction)) {
              event.preventDefault();
              emitChange();
              syncActiveLink();
            }
          }}
          onPaste={(event) => {
            const html = event.clipboardData?.getData("text/html");
            if (!html || !/<table[\s>]/i.test(html)) return;
            const normalized = normalizeRichTextPastedHtml(html);
            if (!normalized) return;
            event.preventDefault();
            execRichTextCommand("insertHTML", normalized);
            emitChange();
          }}
        />
      )}

      {!sourceMode && activeLink ? (
        <div
          className="delpi-ui-rich-text__link-badge"
          style={{ top: activeLink.top, left: activeLink.left }}
          onMouseDown={(event) => event.preventDefault()}
        >
          <a
            className="delpi-ui-rich-text__link-badge-url"
            href={activeLink.href}
            target="_blank"
            rel="noopener noreferrer"
            title={RICH_TEXT_LABELS.linkOpen}
          >
            <ExternalLink size={12} aria-hidden="true" />
            <span>{activeLink.href}</span>
          </a>
          <button
            type="button"
            className="delpi-ui-rich-text__link-badge-btn"
            aria-label={RICH_TEXT_LABELS.linkEditAction}
            title={RICH_TEXT_LABELS.linkEditAction}
            onClick={() => setLinkDialog({ mode: "edit", element: activeLink.element })}
          >
            <Pencil size={13} aria-hidden="true" />
          </button>
          <button
            type="button"
            className="delpi-ui-rich-text__link-badge-btn"
            aria-label={RICH_TEXT_LABELS.linkRemove}
            title={RICH_TEXT_LABELS.linkRemove}
            onClick={handleLinkRemove}
          >
            <Unlink size={13} aria-hidden="true" />
          </button>
        </div>
      ) : null}

      <RichTextLinkDialog
        open={linkDialog !== null && !sourceMode}
        editing={linkDialog?.mode === "edit"}
        initialUrl={
          linkDialog?.mode === "edit"
            ? (linkDialog.element.getAttribute("href") ?? "")
            : ""
        }
        portalScopeClassName={portalScopeClassName}
        onSubmit={handleLinkSubmit}
        onClose={() => setLinkDialog(null)}
      />
    </div>
  );
}
