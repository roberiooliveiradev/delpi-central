import { ExternalLink, Pencil, Unlink } from "lucide-react";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ClipboardEvent,
} from "react";

import { RichTextLinkDialog } from "./RichTextLinkDialog";
import { RichTextSourceEditor } from "./RichTextSourceEditor";
import { RichTextToolbar, type RichTextSourceKind } from "./RichTextToolbar";
import {
  applyRichTextLinkAtRange,
  findRichTextLinkAtSelection,
  insertRichTextHtmlFragment,
  normalizeRichTextLinkUrl,
  unwrapRichTextLink,
} from "./richTextCommands";
import { tryDeleteRichTextAtEmphasisBoundary } from "./richTextDeleteBoundary";
import { prettyPrintRichTextHtml, stripDangerousRichTextTags } from "./richTextHtmlFormat";
import { RICH_TEXT_LABELS } from "./richTextLabels";
import {
  clipboardHasUsefulHtml,
  clipboardLooksLikeMarkdown,
  markdownToRichTextHtml,
  richTextHtmlToMarkdown,
} from "./richTextMarkdown";
import { normalizeRichTextPastedHtml } from "./richTextTable";

export type RichTextEditorMode = "edit" | "preview";
export type { RichTextSourceKind };

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

function sanitizeEditorHtml(html: string): string {
  let cleaned = stripDangerousRichTextTags(html);
  if (/<table[\s>]/i.test(cleaned)) {
    cleaned = normalizeRichTextPastedHtml(cleaned) || cleaned;
  }
  return cleaned || "<p></p>";
}

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
  const [sourceKind, setSourceKind] = useState<RichTextSourceKind>("visual");
  const [sourceDraft, setSourceDraft] = useState("");
  const [linkDialog, setLinkDialog] = useState<LinkDialogState | null>(null);
  const [activeLink, setActiveLink] = useState<ActiveLinkState | null>(null);
  const sourceMode = sourceKind !== "visual";
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

  const flushHtmlSourceDraft = useCallback(
    (draft: string) => {
      const cleaned = sanitizeEditorHtml(draft);
      onChange(cleaned);
      return cleaned;
    },
    [onChange],
  );

  const flushMarkdownSourceDraft = useCallback(
    (draft: string) => {
      const cleaned = sanitizeEditorHtml(markdownToRichTextHtml(draft));
      onChange(cleaned);
      return cleaned;
    },
    [onChange],
  );

  function handleSourceDraftChange(next: string) {
    setSourceDraft(next);
    if (sourceDebounceRef.current) clearTimeout(sourceDebounceRef.current);
    sourceDebounceRef.current = setTimeout(() => {
      if (sourceKind === "markdown") flushMarkdownSourceDraft(next);
      else flushHtmlSourceDraft(next);
    }, SOURCE_CHANGE_DEBOUNCE_MS);
  }

  function currentEditorHtml(): string {
    return ref.current?.innerHTML || value || "<p></p>";
  }

  function applyHtmlToVisual(cleaned: string) {
    requestAnimationFrame(() => {
      if (ref.current) {
        ref.current.innerHTML = cleaned;
      }
    });
  }

  function handleSourceKindChange(next: RichTextSourceKind) {
    if (disabled || next === sourceKind) return;
    if (sourceDebounceRef.current) {
      clearTimeout(sourceDebounceRef.current);
      sourceDebounceRef.current = null;
    }

    focusedRef.current = false;
    setActiveLink(null);
    setLinkDialog(null);

    if (sourceKind === "html") {
      const cleaned = flushHtmlSourceDraft(sourceDraft);
      if (next === "visual") {
        setSourceKind("visual");
        applyHtmlToVisual(cleaned);
        return;
      }
      setSourceDraft(richTextHtmlToMarkdown(cleaned));
      setSourceKind("markdown");
      return;
    }

    if (sourceKind === "markdown") {
      const cleaned = flushMarkdownSourceDraft(sourceDraft);
      if (next === "visual") {
        setSourceKind("visual");
        applyHtmlToVisual(cleaned);
        return;
      }
      setSourceDraft(prettyPrintRichTextHtml(cleaned));
      setSourceKind("html");
      return;
    }

    // visual → html | markdown
    const current = currentEditorHtml();
    if (next === "html") {
      setSourceDraft(prettyPrintRichTextHtml(current));
      setSourceKind("html");
      return;
    }
    setSourceDraft(richTextHtmlToMarkdown(current));
    setSourceKind("markdown");
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

  function handlePaste(event: ClipboardEvent<HTMLDivElement>) {
    if (sourceMode) return;
    const html = event.clipboardData?.getData("text/html");
    const plain = event.clipboardData?.getData("text/plain") ?? "";

    if (html && /<table[\s>]/i.test(html)) {
      const normalized = normalizeRichTextPastedHtml(html);
      if (!normalized) return;
      event.preventDefault();
      insertRichTextHtmlFragment(ref.current, normalized);
      emitChange();
      return;
    }

    if (!clipboardHasUsefulHtml(html) && clipboardLooksLikeMarkdown(plain)) {
      event.preventDefault();
      const converted = sanitizeEditorHtml(markdownToRichTextHtml(plain));
      insertRichTextHtmlFragment(ref.current, converted);
      emitChange();
    }
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
        sourceKind={sourceKind}
        onSourceKindChange={handleSourceKindChange}
        portalScopeClassName={portalScopeClassName}
        onFormatted={emitChange}
        onRequestLink={handleRequestLink}
      />
      {sourceKind === "html" ? (
        <RichTextSourceEditor
          value={sourceDraft}
          onChange={handleSourceDraftChange}
          minHeight={minHeight}
          disabled={disabled}
          assistMode="html"
          ariaLabel={RICH_TEXT_LABELS.sourceEditor}
          hint={RICH_TEXT_LABELS.sourceHint}
        />
      ) : null}
      {sourceKind === "markdown" ? (
        <RichTextSourceEditor
          value={sourceDraft}
          onChange={handleSourceDraftChange}
          minHeight={minHeight}
          disabled={disabled}
          assistMode="plain"
          ariaLabel={RICH_TEXT_LABELS.sourceMarkdownEditor}
          hint={RICH_TEXT_LABELS.sourceMarkdownHint}
        />
      ) : null}
      {/*
        Mantém o contentEditable montado (só esconde no modo fonte) para não
        invalidar Ranges da toolbar — remount quebrava negrito/alinhamento.
      */}
      <div
        ref={ref}
        className="delpi-ui-rich-text__editor"
        style={{ minHeight, display: sourceMode ? "none" : undefined }}
        contentEditable={!sourceMode}
        role="textbox"
        aria-multiline="true"
        aria-label={ariaLabel}
        aria-hidden={sourceMode || undefined}
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
          if (sourceMode) return;
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
        onPaste={handlePaste}
      />

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
