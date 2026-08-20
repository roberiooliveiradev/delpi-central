import {
  Bold,
  Code,
  Italic,
  Link,
  List,
  ListOrdered,
  Paperclip,
  Quote,
  Redo2,
  SendHorizontal,
  Strikethrough,
  Type,
  Undo2,
} from "lucide-react";
import {
  useEffect,
  useId,
  useRef,
  useState,
  type ClipboardEvent,
  type KeyboardEvent,
  type ReactElement,
  type ReactNode,
} from "react";

import { NumberStepperControl } from "../forms/NumberStepperControl";
import { HintAction } from "../help/HintAction";
import {
  appendShortcutHint,
  editorModKeyLabel,
} from "../layout/EditorHistoryActions";
import { delpiUiClass } from "../../utils/delpiUiClass";
import {
  applyRichTextFontSize,
  getRichTextSelectionRange,
  insertRichTextHtmlFragment,
  queryRichTextFontSize,
  restoreRichTextSelection,
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
  emptyComposerFormatFlags,
  queryComposerFormatFlags,
  toggleComposerFormat,
  type ComposerFormatKind,
} from "./mentionComposerFormat";
import {
  clampComposerFontSize,
  COMPOSER_FONT_SIZE_DEFAULT,
  COMPOSER_FONT_SIZE_MAX,
  COMPOSER_FONT_SIZE_MIN,
  COMPOSER_FONT_SIZE_PRESETS,
  COMPOSER_FONT_SIZE_STEP,
} from "./mentionComposerFontSize";
import {
  detectActiveMention,
  insertMentionToken,
  replaceEditablePlainRange,
  setEditablePlainCursor,
  snapshotEditablePlaintext,
  type ActiveMentionQuery,
} from "./mentionComposerCaret";
import {
  createMentionComposerHistory,
  type MentionComposerHistorySnapshot,
} from "./mentionComposerHistory";

/** Coalesce de digitação antes de empilhar na pilha custom (ms). */
export const COMPOSER_TYPING_COALESCE_MS = 400;

export type MentionComposerClassNames = {
  root: string;
  body: string;
  field: string;
  textarea: string;
  placeholder: string;
  empty: string;
  toolbar: string;
  actions: string;
  attach: string;
  formatBar: string;
  formatToggle: string;
  format: string;
  fontSize: string;
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
  formatFontSizeAriaLabel?: string;
  formatFontSizeDecreaseAriaLabel?: string;
  formatFontSizeIncreaseAriaLabel?: string;
  formatUndoAriaLabel?: string;
  formatRedoAriaLabel?: string;
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
    field: pair(`${base}__field`, `${ui}__field`),
    textarea: pair(`${base}__textarea`, `${ui}__textarea`),
    placeholder: pair(`${base}__placeholder`, `${ui}__placeholder`),
    empty: pair(`${base}__textarea--empty`, `${ui}__textarea--empty`),
    toolbar: pair(`${base}__toolbar`, `${ui}__toolbar`),
    actions: pair(`${base}__actions`, `${ui}__actions`),
    attach: pair(`${base}__attach`, `${ui}__attach`),
    formatBar: pair(`${base}__format-bar`, `${ui}__format-bar`),
    formatToggle: pair(`${base}__format-toggle`, `${ui}__format-toggle`),
    format: pair(`${base}__format`, `${ui}__format`),
    fontSize: pair(`${base}__font-size`, `${ui}__font-size`),
    send: pair(`${base}__send`, `${ui}__send`),
    footer: pair(`${base}__footer`, `${ui}__footer`),
    fileInput: pair(`${base}__file`, `${ui}__file`),
    menu: mentionMenuBemClasses(prefix),
  };
}

function placeCaretAtStart(editor: HTMLElement) {
  const range = document.createRange();
  range.selectNodeContents(editor);
  range.collapse(true);
  const selection = window.getSelection();
  selection?.removeAllRanges();
  selection?.addRange(range);
}

function ComposerHint({ hint, children }: { hint: string; children: ReactElement }) {
  return (
    <HintAction hint={hint} ariaLabel={hint} placement="top">
      {children}
    </HintAction>
  );
}

function escapePlainText(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\n/g, "<br>");
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
  const historyRef = useRef(createMentionComposerHistory());
  const lastStableRef = useRef<MentionComposerHistorySnapshot>({
    markdown: value,
    html: value.trim() ? markdownToRichTextHtml(value) : "",
    cursor: 0,
  });
  const typingBeforeRef = useRef<MentionComposerHistorySnapshot | null>(null);
  const typingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [activeMention, setActiveMention] = useState<ActiveMentionQuery | null>(null);
  const [formatOpen, setFormatOpen] = useState(false);
  const [fontSize, setFontSize] = useState(COMPOSER_FONT_SIZE_DEFAULT);
  const [formatFlags, setFormatFlags] = useState(emptyComposerFormatFlags());
  const [historyTick, setHistoryTick] = useState(0);
  const menuOpen = Boolean(activeMention) && !disabled;
  const empty = !value.trim();
  const showFormat = Boolean(labels.formatToggleAriaLabel);
  const canUndo = historyRef.current.canUndo();
  const canRedo = historyRef.current.canRedo();
  void historyTick;

  const refreshHistoryFlags = () => {
    setHistoryTick((tick) => tick + 1);
  };

  const readSnapshot = (): MentionComposerHistorySnapshot => {
    const el = surfaceRef.current;
    if (!el) {
      return {
        markdown: value,
        html: value.trim() ? markdownToRichTextHtml(value) : "",
        cursor: value.length,
      };
    }
    const markdown = richTextHtmlToMarkdown(el.innerHTML);
    const plain = snapshotEditablePlaintext(el);
    return { markdown, html: el.innerHTML, cursor: plain.cursor };
  };

  const flushTypingCoalesce = () => {
    if (typingTimerRef.current) {
      clearTimeout(typingTimerRef.current);
      typingTimerRef.current = null;
    }
    const before = typingBeforeRef.current;
    typingBeforeRef.current = null;
    if (!before) return;
    const after = readSnapshot();
    historyRef.current.commit(before, after);
    lastStableRef.current = after;
  };

  const commitBeforeMutation = () => {
    flushTypingCoalesce();
    const before = readSnapshot();
    historyRef.current.pushBefore(before);
    lastStableRef.current = before;
  };

  const noteTypingInput = () => {
    if (!typingBeforeRef.current) {
      typingBeforeRef.current = { ...lastStableRef.current };
    }
    lastStableRef.current = readSnapshot();
    if (typingTimerRef.current) clearTimeout(typingTimerRef.current);
    typingTimerRef.current = setTimeout(() => {
      typingTimerRef.current = null;
      const before = typingBeforeRef.current;
      typingBeforeRef.current = null;
      if (!before) return;
      const after = readSnapshot();
      historyRef.current.commit(before, after);
      lastStableRef.current = after;
    }, COMPOSER_TYPING_COALESCE_MS);
  };

  const rememberSelection = () => {
    savedRangeRef.current = getRichTextSelectionRange(surfaceRef.current);
  };

  const resetEmptySurface = () => {
    const el = surfaceRef.current;
    if (!el || value.trim()) return;
    if (el.innerHTML && el.innerHTML !== "") {
      el.innerHTML = "";
    }
    placeCaretAtStart(el);
  };

  const handleSurfaceFocus = () => {
    resetEmptySurface();
    rememberSelection();
  };

  useEffect(() => {
    const el = surfaceRef.current;
    if (!el) return;
    const current = richTextHtmlToMarkdown(el.innerHTML);
    if (current === value) {
      lastStableRef.current = {
        markdown: value,
        html: el.innerHTML,
        cursor: lastStableRef.current.cursor,
      };
      return;
    }
    // Preserva a pilha nativa / custom enquanto o editor está focado.
    if (document.activeElement === el) return;
    el.innerHTML = value.trim() ? markdownToRichTextHtml(value) : "";
    lastStableRef.current = {
      markdown: value,
      html: el.innerHTML,
      cursor: value.length,
    };
    historyRef.current.clear();
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
      const size = queryRichTextFontSize(el);
      if (size) setFontSize(clampComposerFontSize(size));
      setFormatFlags(queryComposerFormatFlags(el));
      refreshHistoryFlags();
    };
    document.addEventListener("selectionchange", persist);
    return () => document.removeEventListener("selectionchange", persist);
  }, []);

  useEffect(() => {
    return () => {
      if (typingTimerRef.current) clearTimeout(typingTimerRef.current);
    };
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
    commitBeforeMutation();
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
    lastStableRef.current = readSnapshot();
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
    flushTypingCoalesce();
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
    const run = (kind: ComposerFormatKind) => {
      commitBeforeMutation();
      toggleComposerFormat(el, kind);
      return true;
    };
    if (key === "b" && !event.shiftKey) return run("bold");
    if (key === "i" && !event.shiftKey) return run("italic");
    if (key === "x" && event.shiftKey) return run("strike");
    if (key === "`" || (key === "e" && !event.shiftKey)) return run("code");
    if (key === "8" && event.shiftKey) return run("ul");
    if (key === "7" && event.shiftKey) return run("ol");
    if (key === "." && event.shiftKey) return run("quote");
    if (key === "k" && !event.shiftKey) return run("link");
    return false;
  };

  const runFormat = (kind: ComposerFormatKind) => {
    const el = surfaceRef.current;
    if (!el) return;
    restoreRichTextSelection(el, savedRangeRef.current);
    commitBeforeMutation();
    toggleComposerFormat(el, kind);
    setFormatFlags(queryComposerFormatFlags(el));
    lastStableRef.current = readSnapshot();
    refreshHistoryFlags();
    emitMarkdownAndMention();
  };

  const applySnapshot = (snapshot: MentionComposerHistorySnapshot) => {
    const el = surfaceRef.current;
    if (!el) return;
    el.focus();
    el.innerHTML = snapshot.html;
    setEditablePlainCursor(el, snapshot.cursor);
    savedRangeRef.current = getRichTextSelectionRange(el);
    lastStableRef.current = snapshot;
    setFormatFlags(queryComposerFormatFlags(el));
    const size = queryRichTextFontSize(el);
    if (size) setFontSize(clampComposerFontSize(size));
    onChange(snapshot.markdown);
    const plain = snapshotEditablePlaintext(el);
    setActiveMention(detectActiveMention(plain.text, plain.cursor));
    refreshHistoryFlags();
  };

  const runHistory = (command: "undo" | "redo") => {
    const el = surfaceRef.current;
    if (!el) return;
    flushTypingCoalesce();
    const current = readSnapshot();
    const next =
      command === "undo"
        ? historyRef.current.undo(current)
        : historyRef.current.redo(current);
    if (!next) {
      refreshHistoryFlags();
      return;
    }
    applySnapshot(next);
  };

  const applyFontSize = (nextRaw: number) => {
    const el = surfaceRef.current;
    if (!el) return;
    const next = clampComposerFontSize(nextRaw);
    restoreRichTextSelection(el, savedRangeRef.current);
    commitBeforeMutation();
    applyRichTextFontSize(el, next);
    setFontSize(next);
    lastStableRef.current = readSnapshot();
    refreshHistoryFlags();
    emitMarkdownAndMention();
  };

  const handlePaste = (event: ClipboardEvent<HTMLDivElement>) => {
    event.preventDefault();
    const el = surfaceRef.current;
    if (!el) return;
    commitBeforeMutation();
    const html = event.clipboardData?.getData("text/html") ?? "";
    const text = event.clipboardData?.getData("text/plain") ?? "";
    if (clipboardHasUsefulHtml(html)) {
      insertRichTextHtmlFragment(el, stripDangerousRichTextTags(html));
    } else if (text) {
      insertRichTextHtmlFragment(el, stripDangerousRichTextTags(escapePlainText(text)));
    }
    lastStableRef.current = readSnapshot();
    emitMarkdownAndMention();
  };

  const handleSurfaceBlur = () => {
    flushTypingCoalesce();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (menuOpen) {
      if (event.key === "Escape") {
        event.preventDefault();
        setActiveMention(null);
      }
      return;
    }
    const mod = event.ctrlKey || event.metaKey;
    if (mod && !event.altKey) {
      const key = event.key.toLowerCase();
      if (key === "z" && !event.shiftKey) {
        event.preventDefault();
        runHistory("undo");
        return;
      }
      if (key === "y" || (key === "z" && event.shiftKey)) {
        event.preventDefault();
        runHistory("redo");
        return;
      }
    }
    if (applyShortcut(event)) {
      event.preventDefault();
      lastStableRef.current = readSnapshot();
      emitMarkdownAndMention();
      setFormatFlags(queryComposerFormatFlags(surfaceRef.current));
      refreshHistoryFlags();
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
  const surfaceClass = classNames.textarea;
  const modKey = editorModKeyLabel();
  const undoLabel = labels.formatUndoAriaLabel ?? "Undo";
  const redoLabel = labels.formatRedoAriaLabel ?? "Redo";
  const undoHint = appendShortcutHint(undoLabel, `${modKey}+Z`);
  const redoHint = appendShortcutHint(redoLabel, `${modKey}+Y`);

  return (
    <div className={rootClass}>
      <div className={classNames.body}>
        <div className={classNames.field}>
          {empty ? (
            <span className={classNames.placeholder} aria-hidden="true">
              {labels.placeholder}
            </span>
          ) : null}
          <div
            id={surfaceId}
            ref={surfaceRef}
            className={surfaceClass}
            role="textbox"
            contentEditable={!(disabled || submitting)}
            suppressContentEditableWarning
            aria-multiline="true"
            aria-label={labels.placeholder}
            aria-placeholder={labels.placeholder}
            onFocus={handleSurfaceFocus}
            onBlur={handleSurfaceBlur}
            onInput={() => {
              rememberSelection();
              noteTypingInput();
              emitMarkdownAndMention();
            }}
            onPaste={handlePaste}
            onKeyDown={handleKeyDown}
            onClick={() => {
              resetEmptySurface();
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
        </div>
        {showFormat && formatOpen ? (
          <div className={classNames.formatBar} role="toolbar" aria-label={labels.formatToggleAriaLabel}>
            <ComposerHint hint={undoHint}>
              <button
                type="button"
                className={classNames.format}
                aria-label={undoLabel}
                disabled={disabled || submitting || !canUndo}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => runHistory("undo")}
              >
                <Undo2 size={16} aria-hidden />
              </button>
            </ComposerHint>
            <ComposerHint hint={redoHint}>
              <button
                type="button"
                className={classNames.format}
                aria-label={redoLabel}
                disabled={disabled || submitting || !canRedo}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => runHistory("redo")}
              >
                <Redo2 size={16} aria-hidden />
              </button>
            </ComposerHint>
            <HintAction
              hint={labels.formatFontSizeAriaLabel ?? "Font size"}
              ariaLabel={labels.formatFontSizeAriaLabel ?? "Font size"}
              placement="top"
            >
              <div className={classNames.fontSize}>
                <NumberStepperControl
                  value={fontSize}
                  onChange={applyFontSize}
                  onStepDown={() => applyFontSize(fontSize - COMPOSER_FONT_SIZE_STEP)}
                  onStepUp={() => applyFontSize(fontSize + COMPOSER_FONT_SIZE_STEP)}
                  options={COMPOSER_FONT_SIZE_PRESETS}
                  min={COMPOSER_FONT_SIZE_MIN}
                  max={COMPOSER_FONT_SIZE_MAX}
                  clamp={clampComposerFontSize}
                  disabled={disabled || submitting}
                  compact
                  square={false}
                  aria-label={labels.formatFontSizeAriaLabel ?? "Font size"}
                  groupAriaLabel={labels.formatFontSizeAriaLabel ?? "Font size"}
                  stepDownAriaLabel={labels.formatFontSizeDecreaseAriaLabel ?? "Decrease font size"}
                  stepUpAriaLabel={labels.formatFontSizeIncreaseAriaLabel ?? "Increase font size"}
                  portalScopeClassName={portalScopeClassName}
                />
              </div>
            </HintAction>
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
              <ComposerHint key={kind} hint={aria}>
                <button
                  type="button"
                  className={classNames.format}
                  aria-label={aria}
                  aria-pressed={formatFlags[kind]}
                  disabled={disabled || submitting}
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => runFormat(kind)}
                >
                  <Icon size={16} aria-hidden />
                </button>
              </ComposerHint>
            ))}
          </div>
        ) : null}
        <div className={classNames.toolbar}>
          <div className={classNames.actions}>
            {showFormat ? (
              <ComposerHint hint={labels.formatToggleAriaLabel ?? "Format"}>
                <button
                  type="button"
                  className={classNames.formatToggle}
                  aria-label={labels.formatToggleAriaLabel}
                  aria-pressed={formatOpen}
                  disabled={disabled || submitting}
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => {
                    setFormatOpen((open) => {
                      const next = !open;
                      if (next) refreshHistoryFlags();
                      return next;
                    });
                  }}
                >
                  <Type size={16} aria-hidden />
                </button>
              </ComposerHint>
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
                <ComposerHint hint={labels.attachAriaLabel}>
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
                </ComposerHint>
              </>
            ) : null}
          </div>
          <ComposerHint hint={labels.sendAriaLabel}>
            <button
              type="button"
              className={classNames.send}
              aria-label={labels.sendAriaLabel}
              disabled={!canSubmit}
              onClick={() => flushAndSubmit()}
            >
              <SendHorizontal size={16} aria-hidden />
            </button>
          </ComposerHint>
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
