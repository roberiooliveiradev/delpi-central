import { Paperclip, SendHorizontal } from "lucide-react";
import {
  useEffect,
  useId,
  useRef,
  useState,
  type ChangeEvent,
  type KeyboardEvent,
  type ReactNode,
} from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";
import {
  MentionMenu,
  mentionMenuBemClasses,
  type MentionMenuClassNames,
  type MentionMenuHit,
} from "./MentionMenu";
import {
  detectActiveMention,
  insertMentionToken,
  type ActiveMentionQuery,
} from "./mentionComposerCaret";

export type MentionComposerClassNames = {
  root: string;
  body: string;
  textarea: string;
  toolbar: string;
  actions: string;
  attach: string;
  send: string;
  footer: string;
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
  /** Hits for the open @ menu — host filters/fetches. */
  mentionHits?: readonly MentionMenuHit[];
  /** Fired when the active `@query` changes (including null when menu closes). */
  onMentionQueryChange?: (query: string | null) => void;
  /** Called after a hit is inserted into the textarea. */
  onMentionInserted?: (hit: MentionMenuHit, token: string) => void;
  disabled?: boolean;
  submitting?: boolean;
  rows?: number;
  showAttach?: boolean;
  onAttachClick?: () => void;
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
    toolbar: pair(`${base}__toolbar`, `${ui}__toolbar`),
    actions: pair(`${base}__actions`, `${ui}__actions`),
    attach: pair(`${base}__attach`, `${ui}__attach`),
    send: pair(`${base}__send`, `${ui}__send`),
    footer: pair(`${base}__footer`, `${ui}__footer`),
    menu: mentionMenuBemClasses(prefix),
  };
}

/**
 * Message composer with native textarea inside the kit.
 * Host supplies mention hits and labels — no HTTP in the kit.
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
  rows = 3,
  showAttach = false,
  onAttachClick,
  footer,
  className,
  portalScopeClassName,
  submitOnModEnter = true,
}: MentionComposerProps) {
  const textareaId = useId();
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [activeMention, setActiveMention] = useState<ActiveMentionQuery | null>(null);
  const menuOpen = Boolean(activeMention) && !disabled;

  useEffect(() => {
    onMentionQueryChange?.(activeMention ? activeMention.query : null);
  }, [activeMention, onMentionQueryChange]);

  const syncMentionFromCaret = (nextValue: string, cursor: number) => {
    setActiveMention(detectActiveMention(nextValue, cursor));
  };

  const handleChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    const nextValue = event.target.value;
    const cursor = event.target.selectionStart ?? nextValue.length;
    onChange(nextValue);
    syncMentionFromCaret(nextValue, cursor);
  };

  const applyHit = (hit: MentionMenuHit) => {
    if (!activeMention) return;
    const cursor = textareaRef.current?.selectionStart ?? activeMention.end;
    const { nextValue, nextCursor, token } = insertMentionToken(
      value,
      cursor,
      activeMention.start,
      hit.label,
    );
    onChange(nextValue);
    setActiveMention(null);
    onMentionInserted?.(hit, token);
    requestAnimationFrame(() => {
      const el = textareaRef.current;
      if (!el) return;
      el.focus();
      el.setSelectionRange(nextCursor, nextCursor);
    });
  };

  const canSubmit =
    !disabled && !submitting && value.trim().length > 0;

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (menuOpen) {
      // MentionMenu captures Arrow/Enter/Tab on window; Escape dismisses via portal.
      if (event.key === "Escape") {
        event.preventDefault();
        setActiveMention(null);
      }
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

  return (
    <div className={rootClass}>
      <div className={classNames.body}>
        <textarea
          id={textareaId}
          ref={textareaRef}
          className={classNames.textarea}
          rows={rows}
          value={value}
          placeholder={labels.placeholder}
          disabled={disabled || submitting}
          aria-label={labels.placeholder}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onClick={(event) => {
            const el = event.currentTarget;
            syncMentionFromCaret(el.value, el.selectionStart ?? el.value.length);
          }}
          onKeyUp={(event) => {
            const el = event.currentTarget;
            if (event.key === "Escape") return;
            syncMentionFromCaret(el.value, el.selectionStart ?? el.value.length);
          }}
        />
        <div className={classNames.toolbar}>
          <div className={classNames.actions}>
            {showAttach ? (
              <button
                type="button"
                className={classNames.attach}
                aria-label={labels.attachAriaLabel}
                disabled={disabled || submitting}
                onClick={() => onAttachClick?.()}
              >
                <Paperclip size={18} aria-hidden />
              </button>
            ) : null}
          </div>
          <button
            type="button"
            className={classNames.send}
            aria-label={labels.sendAriaLabel}
            disabled={!canSubmit}
            onClick={() => onSubmit()}
          >
            <SendHorizontal size={18} aria-hidden />
          </button>
        </div>
      </div>
      {footer ? <div className={classNames.footer}>{footer}</div> : null}
      <MentionMenu
        open={menuOpen}
        anchorRef={textareaRef}
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
