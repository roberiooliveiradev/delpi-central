import { useCallback, useEffect, useRef, useState } from "react";
import { Check, ClipboardX, Copy, FileCode2 } from "lucide-react";

import { HelpTooltip } from "../help/HelpTooltip";

/**
 * Inert, presentation-only fenced code block for conversational surfaces.
 *
 * Render-only: `code` is treated as untrusted literal text rendered as a React
 * child — never HTML, never executed, never a business action. No backend,
 * provider, MCP, AuthZ, persistence or execution dependencies.
 *
 * CSS: `styles/conversation-code-block.css` (`delpi-ui-conversation-code-block`).
 * Spec: docs/12-roadmap-e-evolucao/delia/96 §9.
 */

export type ConversationCodeBlockLabels = {
  /** Accessible name of the block group, e.g. "Bloco de código". */
  blockLabel: string;
  /** Accessible name of the scrollable code region. */
  codeRegionLabel: string;
  /** Copy action label and tooltip. */
  copyCode: string;
  /** Transient success feedback (only after clipboard resolves). */
  copied: string;
  /** Transient failure/unavailable feedback. */
  copyError: string;
};

const DEFAULT_LABELS: ConversationCodeBlockLabels = {
  blockLabel: "Bloco de código",
  codeRegionLabel: "Conteúdo do código",
  copyCode: "Copiar código",
  copied: "Copiado",
  copyError: "Não foi possível copiar",
};

/** Display allowlist: info-string → safe presentation label. */
const LANGUAGE_DISPLAY_LABELS: Readonly<Record<string, string>> = {
  sql: "SQL",
  python: "Python",
  json: "JSON",
  typescript: "TypeScript",
  javascript: "JavaScript",
  bash: "Bash",
  yaml: "YAML",
  text: "Texto",
};

const FALLBACK_LANGUAGE_LABEL = "Código";
const LANGUAGE_LABEL_MAX_LENGTH = 20;
const LANGUAGE_LABEL_ALLOWED = /[^a-z0-9+#.-]/g;

function languageDisplayLabel(language: string | undefined): string {
  if (!language) return FALLBACK_LANGUAGE_LABEL;
  const safe = language
    .trim()
    .toLowerCase()
    .replace(LANGUAGE_LABEL_ALLOWED, "")
    .slice(0, LANGUAGE_LABEL_MAX_LENGTH);
  if (!safe) return FALLBACK_LANGUAGE_LABEL;
  return LANGUAGE_DISPLAY_LABELS[safe] ?? safe;
}

const COPY_FEEDBACK_MS = 1600;

export type ConversationCodeBlockProps = {
  /** Literal code body — token.text, never token.raw (no fences/info-string). */
  code: string;
  /** Admitted info-string; presentation metadata only, never an instruction. */
  language?: string;
  /** Host-controlled availability of the copy affordance. */
  copyEnabled?: boolean;
  className?: string;
  /** Text customization without a separate localization subsystem. */
  labels?: Partial<ConversationCodeBlockLabels>;
};

type CopyStatus = "idle" | "copied" | "error";

export function ConversationCodeBlock({
  code,
  language,
  copyEnabled = true,
  className,
  labels: labelsOverride,
}: ConversationCodeBlockProps) {
  const labels = { ...DEFAULT_LABELS, ...labelsOverride };
  const langLabel = languageDisplayLabel(language);

  const [status, setStatus] = useState<CopyStatus>("idle");
  const mountedRef = useRef(true);
  const opRef = useRef(0);
  const timerRef = useRef<number | undefined>(undefined);

  useEffect(
    () => () => {
      mountedRef.current = false;
      window.clearTimeout(timerRef.current);
    },
    [],
  );

  const onCopy = useCallback(() => {
    const op = ++opRef.current;
    const settle = (next: Exclude<CopyStatus, "idle">) => {
      if (!mountedRef.current || op !== opRef.current) return;
      setStatus(next);
      window.clearTimeout(timerRef.current);
      timerRef.current = window.setTimeout(() => {
        if (mountedRef.current && op === opRef.current) setStatus("idle");
      }, COPY_FEEDBACK_MS);
    };
    const clipboard =
      typeof navigator === "undefined" ? undefined : navigator.clipboard;
    if (!clipboard?.writeText) {
      settle("error");
      return;
    }
    clipboard.writeText(code).then(
      () => settle("copied"),
      () => settle("error"),
    );
  }, [code]);

  const statusText =
    status === "copied"
      ? labels.copied
      : status === "error"
        ? labels.copyError
        : "";

  const rootClass = [
    "delpi-ui-conversation-code-block",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={rootClass}
      role="group"
      aria-label={
        language ? `${labels.blockLabel} ${langLabel}` : labels.blockLabel
      }
      data-delpi-ui="conversation-code-block"
    >
      <div className="delpi-ui-conversation-code-block__bar">
        <span className="delpi-ui-conversation-code-block__lang">
          <FileCode2 size={13} aria-hidden="true" />
          {langLabel}
        </span>
        {copyEnabled ? (
          <HelpTooltip wrap content={labels.copyCode}>
            <button
              type="button"
              className={[
                "delpi-ui-conversation-code-block__copy",
                status === "copied"
                  ? "delpi-ui-conversation-code-block__copy--copied"
                  : null,
                status === "error"
                  ? "delpi-ui-conversation-code-block__copy--error"
                  : null,
              ]
                .filter(Boolean)
                .join(" ")}
              onClick={onCopy}
              aria-label={labels.copyCode}
            >
              {status === "copied" ? (
                <Check size={13} aria-hidden="true" />
              ) : status === "error" ? (
                <ClipboardX size={13} aria-hidden="true" />
              ) : (
                <Copy size={13} aria-hidden="true" />
              )}
              <span
                className="delpi-ui-conversation-code-block__copy-label"
                aria-live="polite"
              >
                {status === "idle" ? labels.copyCode : statusText}
              </span>
            </button>
          </HelpTooltip>
        ) : null}
      </div>
      <pre
        className="delpi-ui-conversation-code-block__pre"
        tabIndex={0}
        role="region"
        aria-label={labels.codeRegionLabel}
      >
        <code>{code}</code>
      </pre>
    </div>
  );
}
