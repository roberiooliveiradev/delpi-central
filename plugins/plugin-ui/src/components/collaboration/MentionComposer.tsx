import { Paperclip, SendHorizontal } from "lucide-react";
import {
  useEffect,
  useId,
  useRef,
  useState,
  type KeyboardEvent,
  type ReactNode,
} from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";
import {
  execRichTextCommand,
  insertRichTextHtmlFragment,
  insertRichTextLink,
  runRichTextCommand,
} from "../rich-text/richTextCommands";
import {
  markdownToRichTextHtml,
  richTextHtmlToMarkdown,
} from "../rich-text/richTextMarkdown";
import {
  MentionMenu,
  mentionMenuBemClasses,
  type MentionMenuClassNames,
  type MentionMenuHit,
} from "./MentionMenu";
import {
  detectActiveMention,
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
};

export type MentionComposerProps = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
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
    send: pair(`${base}__send`, `${ui}__send`),
    footer: pair(`${base}__footer`, `${ui}__footer`),
    fileInput: pair(`${base}__file`, `${ui}__file`),
    menu: mentionMenuBemClasses(prefix),
  };
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
}: MentionComposerProps) {
  const surfaceId = useId();
  const surfaceRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [activeMention, setActiveMention] = useState<ActiveMentionQuery | null>(null);
  const menuOpen = Boolean(activeMention) && !disabled;
  const empty = !value.trim();

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

  const canSubmit =
    !disabled && !submitting && (value.trim().length > 0 || hasAttachments);

  const applyShortcut = (event: KeyboardEvent<HTMLDivElement>): boolean => {
    const mod = event.ctrlKey || event.metaKey;
    if (!mod || event.altKey) return false;
    const el = surfaceRef.current;
    if (!el) return false;
    const key = event.key.toLowerCase();
    if (key === "b" && !event.shiftKey) {
      runRichTextCommand(el, "bold");
      return true;
    }
    if (key === "i" && !event.shiftKey) {
      runRichTextCommand(el, "italic");
      return true;
    }
    if (key === "x" && event.shiftKey) {
      runRichTextCommand(el, "strikeThrough");
      return true;
    }
    if (key === "`" || (key === "e" && !event.shiftKey)) {
      wrapSelectionWithTag(el, "code");
      return true;
    }
    if (key === "8" && event.shiftKey) {
      runRichTextCommand(el, "insertUnorderedList");
      return true;
    }
    if (key === "7" && event.shiftKey) {
      runRichTextCommand(el, "insertOrderedList");
      return true;
    }
    if (key === "." && event.shiftKey) {
      execRichTextCommand("formatBlock", "blockquote");
      return true;
    }
    if (key === "k" && !event.shiftKey) {
      insertRichTextLink(el, "https://");
      return true;
    }
    return false;
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
    if (
      submitOnModEnter &&
      event.key === "Enter" &&
      (event.ctrlKey || event.metaKey) &&
      canSubmit
    ) {
      event.preventDefault();
      onSubmit();
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
          onInput={emitMarkdownAndMention}
          onKeyDown={handleKeyDown}
          onClick={emitMarkdownAndMention}
          onKeyUp={(event) => {
            if (event.key === "Escape") return;
            emitMarkdownAndMention();
          }}
        />
        <div className={classNames.toolbar}>
          <div className={classNames.actions}>
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
            onClick={() => onSubmit()}
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
