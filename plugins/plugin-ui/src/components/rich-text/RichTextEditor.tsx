import { ExternalLink, Pencil, Unlink } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { RichTextLinkDialog } from "./RichTextLinkDialog";
import { RichTextToolbar } from "./RichTextToolbar";
import {
  applyRichTextLinkAtRange,
  findRichTextLinkAtSelection,
  normalizeRichTextLinkUrl,
  unwrapRichTextLink,
} from "./richTextCommands";
import { RICH_TEXT_LABELS } from "./richTextLabels";

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
  const [linkDialog, setLinkDialog] = useState<LinkDialogState | null>(null);
  const [activeLink, setActiveLink] = useState<ActiveLinkState | null>(null);
  const rootClass = useMemo(
    () => ["delpi-ui-rich-text", className].filter(Boolean).join(" "),
    [className],
  );

  useEffect(() => {
    if (mode !== "edit" || disabled || !ref.current || focusedRef.current) return;
    const next = value || "<p></p>";
    if (ref.current.innerHTML !== next) {
      ref.current.innerHTML = next;
    }
  }, [mode, disabled, value]);

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

  function handleRequestLink() {
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
        dangerouslySetInnerHTML={{ __html: value || "<p></p>" }}
      />
    );
  }

  return (
    <div className={rootClass} ref={rootRef}>
      <RichTextToolbar
        editorRef={ref}
        disabled={disabled}
        portalScopeClassName={portalScopeClassName}
        onFormatted={emitChange}
        onRequestLink={handleRequestLink}
      />
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
      />

      {activeLink ? (
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
        open={linkDialog !== null}
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
