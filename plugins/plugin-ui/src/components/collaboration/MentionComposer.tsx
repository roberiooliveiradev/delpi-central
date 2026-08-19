import {
  Bold,
  Code,
  Italic,
  Link,
  List,
  ListOrdered,
  Paperclip,
  Quote,
  SendHorizontal,
  Strikethrough,
  Type,
} from "lucide-react";
import {
  useEffect,
  useId,
  useRef,
  useState,
  type ClipboardEvent,
  type KeyboardEvent,
  type ReactNode,
} from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";
import {
  execRichTextCommand,
  getRichTextSelectionRange,
  insertRichTextHtmlFragment,
  insertRichTextLink,
  restoreRichTextSelection,
  runRichTextCommand,
} from "../rich-text/richTextCommands";
import {
  clipboardHasUsefulHtml,
  markdownToRichTextHtml,
  richTextHtmlToMarkdown,
} from "../rich-text/richTextMarkdown";
import { stripDangerousRichTextTags } from "../rich-text/richTextHtmlFormat";
import {
  MentionMenu,
  mentionMenuBemClasses,
  type MentionMenuClassNames,
  type MentionMenuHit,
} from "./MentionMenu";
import {
  detectActiveMention,
  expandCollapsedSelectionForFormat,
  insertMentionToken,
  replaceEditablePlainRange,
  snapshotEditablePlaintext,
  type ActiveMentionQuery,
} from "./mentionComposerCaret";

export type MentionComposerClassNames = {
  root: string;
  body: string;
  textarea: string;
  empty: string;
  toolbar: string;
  actions: string;
  attach: string;
  formatBar: string;
  formatToggle: string;
  format: string;
  send: string;
  footer: string;
  fileInput: string;
  menu: MentionMenuClassNames;
};

export type MentionComposerLabels = {
  placeholder: string;
  sendAriaLabel: string;
  attachAriaLabel: string;
  mentionListAriaLabel: string;
  mentionEmptyLabel: string;
  formatToggleAriaLabel?: string;
  formatBoldAriaLabel?: string;
  formatItalicAriaLabel?: string;
  formatStrikeAriaLabel?: string;
  formatListAriaLabel?: string;
  formatOrderedListAriaLabel?: string;
  formatCodeAriaLabel?: string;
  formatQuoteAriaLabel?: string;
  formatLinkAriaLabel?: string;
};

export type MentionComposerProps = {
  value: string;
  onChange: (value: string) => void;
  /** Recebe o markdown atual da superfície (não depender só do state controlado). */
  onSubmit: (markdown: string) => void;
  labels: MentionComposerLabels;
  classNames: MentionComposerClassNames;
  mentionHits?: readonly MentionMenuHit[];
  onMentionQueryChange?: (query: string | null) => void;
  onMentionInserted?: (hit: MentionMenuHit, token: string) => void;
  disabled?: boolean;
  submitting?: boolean;
  rows?: number;
  showAttach?: boolean;
  onAttachClick?: () => void;
  onFilesSelected?: (files: File[]) => void;
  fileAccept?: string;
  fileMultiple?: boolean;
  hasAttachments?: boolean;
  footer?: ReactNode;
  className?: string;
  portalScopeClassName?: string;
  /** Submit on Ctrl/Cmd+Enter (default true). */
  submitOnModEnter?: boolean;
  /** Submit on Enter (Shift+Enter quebra). Default true. */
  submitOnEnter?: boolean;
};

export function mentionComposerBemClasses(prefix: string): MentionComposerClassNames {
  const base = `${prefix}-mention-composer`;
  const ui = "delpi-ui-mention-composer";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    body: pair(`${base}__body`, `${ui}__body`),
    textarea: pair(`${base}__textarea`, `${ui}__textarea`),
    empty: pair(`${base}__textarea--empty`, `${ui}__textarea--empty`),
    toolbar: pair(`${base}__toolbar`, `${ui}__toolbar`),
    actions: pair(`${base}__actions`, `${ui}__actions`),
    attach: pair(`${base}__attach`, `${ui}__attach`),
    formatBar: pair(`${base}__format-bar`, `${ui}__format-bar`),
    formatToggle: pair(`${base}__format-toggle`, `${ui}__format-toggle`),
    format: pair(`${base}__format`, `${ui}__format`),
    send: pair(`${base}__send`, `${ui}__send`),
    footer: pair(`${base}__footer`, `${ui}__footer`),
    fileInput: pair(`${base}__file`, `${ui}__file`),
    menu: mentionMenuBemClasses(prefix),
  };
}

function escapePlainText(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\n/g, "<br>");
}

function wrapSelectionWithTag(editor: HTMLElement, tag: string) {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) {
    insertRichTextHtmlFragment(editor, `<${tag}>\u200b</${tag}>`);
    return;
  }
  const range = selection.getRangeAt(0);
  if (!editor.contains(range.commonAncestorContainer)) {
    insertRichTextHtmlFragment(editor, `<${tag}>\u200b</${tag}>`);
    return;
  }
  if (range.collapsed) {
    insertRichTextHtmlFragment(editor, `<${tag}>\u200b</${tag}>`);
    return;
  }
  const el = document.createElement(tag);
  try {
    range.surroundContents(el);
  } catch {
    el.appendChild(range.extractContents());
    range.insertNode(el);
  }
}

function applyComposerFormat(editor: HTMLElement, kind: string) {
  expandCollapsedSelectionForFormat(editor);
  if (kind === "bold") wrapSelectionWithTag(editor, "strong");
  else if (kind === "italic") wrapSelectionWithTag(editor, "em");
  else if (kind === "strike") wrapSelectionWithTag(editor, "s");
  else if (kind === "ul") runRichTextCommand(editor, "insertUnorderedList");
  else if (kind === "ol") runRichTextCommand(editor, "insertOrderedList");
  else if (kind === "code") wrapSelectionWithTag(editor, "code");
  else if (kind === "quote") execRichTextCommand("formatBlock", "blockquote");
  else if (kind === "link") insertRichTextLink(editor, "https://");
}

/**
 * Composer da sala: superfície contenteditable; contrato `value`/`onChange` = markdown.
 * Sem RichTextEditor de deck.
 */
export function MentionComposer({
  value,
  onChange,
  onSubmit,
  labels,
  classNames,
  mentionHits = [],
  onMentionQueryChange,
  onMentionInserted,
  disabled = false,
  submitting = false,
  showAttach = false,
  onAttachClick,
  onFilesSelected,
  fileAccept,
  fileMultiple = true,
  hasAttachments = false,
  footer,
  className,
  portalScopeClassName,
  submitOnModEnter = true,
  submitOnEnter = true,
}: MentionComposerProps) {
  const surfaceId = useId();
  const surfaceRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const savedRangeRef = useRef<Range | null>(null);
  const [activeMention, setActiveMention] = useState<ActiveMentionQuery | null>(null);
  const [formatOpen, setFormatOpen] = useState(false);
  const menuOpen = Boolean(activeMention) && !disabled;
  const empty = !value.trim();
  const showFormat = Boolean(labels.formatToggleAriaLabel);

  const rememberSelection = () => {
    savedRangeRef.current = getRichTextSelectionRange(surfaceRef.current);
  };

  useEffect(() => {
    const el = surfaceRef.current;
    if (!el) return;
    const current = richTextHtmlToMarkdown(el.innerHTML);
    if (current === value) return;
    if (document.activeElement === el && value.trim()) return;
    el.innerHTML = value.trim() ? markdownToRichTextHtml(value) : "";
  }, [value]);

  useEffect(() => {
    onMentionQueryChange?.(activeMention ? activeMention.query : null);
  }, [activeMention, onMentionQueryChange]);

  useEffect(() => {
    const persist = () => {
      const el = surfaceRef.current;
      if (!el) return;
      const range = getRichTextSelectionRange(el);
      if (range) savedRangeRef.current = range;
    };
    document.addEventListener("selectionchange", persist);
    return () => document.removeEventListener("selectionchange", persist);
  }, []);

  const readMarkdown = () => {
    const el = surfaceRef.current;
    return el ? richTextHtmlToMarkdown(el.innerHTML) : value;
  };

  const emitMarkdownAndMention = () => {
    const el = surfaceRef.current;
    if (!el) return;
    const markdown = richTextHtmlToMarkdown(el.innerHTML);
    onChange(markdown);
    const snap = snapshotEditablePlaintext(el);
    setActiveMention(detectActiveMention(snap.text, snap.cursor));
  };

  const applyHit = (hit: MentionMenuHit) => {
    const el = surfaceRef.current;
    if (!activeMention || !el) return;
    const snap = snapshotEditablePlaintext(el);
    const { nextValue, nextCursor, token } = insertMentionToken(
      snap.text,
      snap.cursor,
      activeMention.start,
      hit.label,
    );
    const insertion = nextValue.slice(activeMention.start, nextCursor);
    replaceEditablePlainRange(el, activeMention.start, snap.cursor, insertion);
    const markdown = richTextHtmlToMarkdown(el.innerHTML);
    onChange(markdown);
    setActiveMention(null);
    onMentionInserted?.(hit, token);
    requestAnimationFrame(() => {
      el.focus();
    });
  };

  const liveMarkdown = readMarkdown();
  const canSubmit =
    !disabled &&
    !submitting &&
    (liveMarkdown.trim().length > 0 || value.trim().length > 0 || hasAttachments);

  const flushAndSubmit = () => {
    const markdown = readMarkdown();
    if (markdown !== value) onChange(markdown);
    if (!disabled && !submitting && (markdown.trim().length > 0 || hasAttachments)) {
      onSubmit(markdown);
    }
  };

  const applyShortcut = (event: KeyboardEvent<HTMLDivElement>): boolean => {
    const mod = event.ctrlKey || event.metaKey;
    if (!mod || event.altKey) return false;
    const el = surfaceRef.current;
    if (!el) return false;
    const key = event.key.toLowerCase();
    if (key === "b" && !event.shiftKey) {
      applyComposerFormat(el, "bold");
      return true;
    }
    if (key === "i" && !event.shiftKey) {
      applyComposerFormat(el, "italic");
      return true;
    }
    if (key === "x" && event.shiftKey) {
      applyComposerFormat(el, "strike");
      return true;
    }
    if (key === "`" || (key === "e" && !event.shiftKey)) {
      applyComposerFormat(el, "code");
      return true;
    }
    if (key === "8" && event.shiftKey) {
      applyComposerFormat(el, "ul");
      return true;
    }
    if (key === "7" && event.shiftKey) {
      applyComposerFormat(el, "ol");
      return true;
    }
    if (key === "." && event.shiftKey) {
      applyComposerFormat(el, "quote");
      return true;
    }
    if (key === "k" && !event.shiftKey) {
      applyComposerFormat(el, "link");
      return true;
    }
    return false;
  };

  const runFormat = (kind: string) => {
    const el = surfaceRef.current;
    if (!el) return;
    restoreRichTextSelection(el, savedRangeRef.current);
    applyComposerFormat(el, kind);
    emitMarkdownAndMention();
  };

  const handlePaste = (event: ClipboardEvent<HTMLDivElement>) => {
    event.preventDefault();
    const el = surfaceRef.current;
    if (!el) return;
    const html = event.clipboardData?.getData("text/html") ?? "";
    const text = event.clipboardData?.getData("text/plain") ?? "";
    if (clipboardHasUsefulHtml(html)) {
      insertRichTextHtmlFragment(el, stripDangerousRichTextTags(html));
    } else if (text) {
      insertRichTextHtmlFragment(el, stripDangerousRichTextTags(escapePlainText(text)));
    }
    emitMarkdownAndMention();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (menuOpen) {
      if (event.key === "Escape") {
        event.preventDefault();
        setActiveMention(null);
      }
      return;
    }
    if (applyShortcut(event)) {
      event.preventDefault();
      emitMarkdownAndMention();
      return;
    }
    if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
      if (submitOnModEnter) {
        event.preventDefault();
        flushAndSubmit();
      }
      return;
    }
    if (event.key === "Enter" && event.shiftKey) {
      return;
    }
    if (event.key === "Enter" && submitOnEnter) {
      event.preventDefault();
      flushAndSubmit();
    }
  };

  const rootClass = [classNames.root, className].filter(Boolean).join(" ");
  const surfaceClass = [classNames.textarea, empty ? classNames.empty : null]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={rootClass}>
      <div className={classNames.body}>
        <div
          id={surfaceId}
          ref={surfaceRef}
          className={surfaceClass}
          role="textbox"
          contentEditable={!(disabled || submitting)}
          suppressContentEditableWarning
          aria-multiline="true"
          aria-label={labels.placeholder}
          data-placeholder={labels.placeholder}
          onInput={() => {
            rememberSelection();
            emitMarkdownAndMention();
          }}
          onPaste={handlePaste}
          onKeyDown={handleKeyDown}
          onClick={() => {
            rememberSelection();
            emitMarkdownAndMention();
          }}
          onKeyUp={(event) => {
            rememberSelection();
            if (event.key === "Escape") return;
            emitMarkdownAndMention();
          }}
          onMouseUp={rememberSelection}
        />
        {showFormat && formatOpen ? (
          <div className={classNames.formatBar} role="toolbar" aria-label={labels.formatToggleAriaLabel}>
            {(
              [
                ["bold", labels.formatBoldAriaLabel ?? "Bold", Bold],
                ["italic", labels.formatItalicAriaLabel ?? "Italic", Italic],
                ["strike", labels.formatStrikeAriaLabel ?? "Strikethrough", Strikethrough],
                ["ul", labels.formatListAriaLabel ?? "List", List],
                ["ol", labels.formatOrderedListAriaLabel ?? "Numbered list", ListOrdered],
                ["code", labels.formatCodeAriaLabel ?? "Code", Code],
                ["quote", labels.formatQuoteAriaLabel ?? "Quote", Quote],
                ["link", labels.formatLinkAriaLabel ?? "Link", Link],
              ] as const
            ).map(([kind, aria, Icon]) => (
              <button
                key={kind}
                type="button"
                className={classNames.format}
                aria-label={aria}
                disabled={disabled || submitting}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => runFormat(kind)}
              >
                <Icon size={16} aria-hidden />
              </button>
            ))}
          </div>
        ) : null}
        <div className={classNames.toolbar}>
          <div className={classNames.actions}>
            {showFormat ? (
              <button
                type="button"
                className={classNames.formatToggle}
                aria-label={labels.formatToggleAriaLabel}
                aria-pressed={formatOpen}
                disabled={disabled || submitting}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => setFormatOpen((open) => !open)}
              >
                <Type size={16} aria-hidden />
              </button>
            ) : null}
            {showAttach ? (
              <>
                <input
                  ref={fileInputRef}
                  className={classNames.fileInput}
                  type="file"
                  hidden
                  multiple={fileMultiple}
                  accept={fileAccept}
                  disabled={disabled || submitting}
                  aria-hidden="true"
                  tabIndex={-1}
                  onChange={(event) => {
                    const files = Array.from(event.target.files ?? []);
                    event.target.value = "";
                    if (files.length) onFilesSelected?.(files);
                  }}
                />
                <button
                  type="button"
                  className={classNames.attach}
                  aria-label={labels.attachAriaLabel}
                  disabled={disabled || submitting}
                  onClick={() => {
                    if (onFilesSelected) {
                      fileInputRef.current?.click();
                      return;
                    }
                    onAttachClick?.();
                  }}
                >
                  <Paperclip size={16} aria-hidden />
                </button>
              </>
            ) : null}
          </div>
          <button
            type="button"
            className={classNames.send}
            aria-label={labels.sendAriaLabel}
            disabled={!canSubmit}
            onClick={() => flushAndSubmit()}
          >
            <SendHorizontal size={16} aria-hidden />
          </button>
        </div>
      </div>
      {footer ? <div className={classNames.footer}>{footer}</div> : null}
      <MentionMenu
        open={menuOpen}
        anchorRef={surfaceRef}
        hits={mentionHits}
        classNames={classNames.menu}
        listAriaLabel={labels.mentionListAriaLabel}
        emptyLabel={labels.mentionEmptyLabel}
        portalScopeClassName={portalScopeClassName}
        onSelect={applyHit}
        onDismiss={() => setActiveMention(null)}
      />
    </div>
  );
}

export type DashboardMentionComposerProps = Omit<MentionComposerProps, "classNames">;

export function createDashboardMentionComposer(prefix: string) {
  const classNames = mentionComposerBemClasses(prefix);
  return function DashboardMentionComposer(props: DashboardMentionComposerProps) {
    return <MentionComposer classNames={classNames} {...props} />;
  };
}
