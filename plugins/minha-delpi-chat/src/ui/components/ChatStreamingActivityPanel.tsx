import { useEffect, useMemo, useRef, useState } from "react";

import type { ChatStreamActivityEntry } from "../../data/api/chatTypes";
import {
  activityPhaseKey,
  formatActivityLogLine,
  fullActivityLogForDisplay,
  resolveStreamingHeadline,
} from "../../state/utils/streamingActivityLog";

import { ChatThinkingDots } from "./ChatThinkingDots";

import "./ChatStreamingActivityPanel.css";

type ChatStreamingActivityPanelProps = {
  status: string | null;
  entries: ChatStreamActivityEntry[];
  isActive?: boolean;
  isAnswering?: boolean;
};

const RISING_LOG_VISIBLE_LINES = 4;

function ActivityLogLine({
  entry,
  isRising,
}: {
  entry: ChatStreamActivityEntry;
  isRising: boolean;
}) {
  const isActive = entry.state === "active";
  const levelClass =
    entry.level === "error"
      ? "is-error"
      : entry.level === "warning"
        ? "is-warning"
        : entry.level === "success"
          ? "is-success"
          : "";

  return (
    <li
      className={[
        "mdc-chat-stream-activity__log-line",
        levelClass,
        isActive ? "is-active" : "",
        isRising ? "is-rising" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <span className="mdc-chat-stream-activity__log-text">
        {formatActivityLogLine(entry)}
      </span>
    </li>
  );
}

function RisingLogFeed({
  lines,
  risingIds,
}: {
  lines: ChatStreamActivityEntry[];
  risingIds: Set<string>;
}) {
  const viewportRef = useRef<HTMLDivElement | null>(null);
  const tail = lines.slice(-RISING_LOG_VISIBLE_LINES);

  useEffect(() => {
    const node = viewportRef.current;

    if (!node) {
      return;
    }

    node.scrollTop = node.scrollHeight;
  }, [lines]);

  if (tail.length === 0) {
    return null;
  }

  return (
    <div ref={viewportRef} className="mdc-chat-stream-activity__rise-viewport">
      <ul className="mdc-chat-stream-activity__log-lines mdc-chat-stream-activity__log-lines--rising">
        {tail.map((entry) => (
          <ActivityLogLine
            key={`${activityPhaseKey(entry)}-${entry.id}`}
            entry={entry}
            isRising={risingIds.has(entry.id)}
          />
        ))}
      </ul>
    </div>
  );
}

export function ChatStreamingActivityPanel({
  status,
  entries,
  isActive = false,
  isAnswering = false,
}: ChatStreamingActivityPanelProps) {
  const [showAllSteps, setShowAllSteps] = useState(false);
  const fullLines = useMemo(() => fullActivityLogForDisplay(entries), [entries]);
  const headline = resolveStreamingHeadline(status, entries);
  const dotsLabel = isAnswering
    ? status?.trim() || "Gerando resposta..."
    : headline;
  const expandedRef = useRef<HTMLDivElement | null>(null);
  const knownIdsRef = useRef<Set<string>>(new Set());
  const [risingIds, setRisingIds] = useState<Set<string>>(() => new Set());

  useEffect(() => {
    const nextRising = new Set<string>();

    const previewLines = fullLines.slice(-RISING_LOG_VISIBLE_LINES);

    for (const entry of previewLines) {
      if (!knownIdsRef.current.has(entry.id)) {
        nextRising.add(entry.id);
      }
    }

    knownIdsRef.current = new Set(previewLines.map((entry) => entry.id));
    setRisingIds(nextRising);

    if (nextRising.size === 0) {
      return undefined;
    }

    const timer = window.setTimeout(() => setRisingIds(new Set()), 480);

    return () => window.clearTimeout(timer);
  }, [fullLines]);

  useEffect(() => {
    if (!showAllSteps || !expandedRef.current) {
      return;
    }

    expandedRef.current.scrollTop = expandedRef.current.scrollHeight;
  }, [fullLines, showAllSteps]);

  const hasLog = fullLines.length > 0;
  const canExpand = fullLines.length > RISING_LOG_VISIBLE_LINES;

  return (
    <div
      className={[
        "mdc-chat-stream-activity",
        isActive ? "is-active" : "",
        isAnswering ? "is-answering" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      role="status"
      aria-live="polite"
    >
      {isActive ? <ChatThinkingDots label={dotsLabel} /> : null}

      {hasLog ? (
        <>
          {canExpand ? (
            <button
              type="button"
              className="mdc-chat-stream-activity__collapse"
              aria-expanded={showAllSteps}
              onClick={() => setShowAllSteps((current) => !current)}
            >
              {showAllSteps
                ? "Ocultar etapas"
                : `Ver todas as etapas (${fullLines.length})`}
            </button>
          ) : null}

          {showAllSteps && canExpand ? (
            <div ref={expandedRef} className="mdc-chat-stream-activity__log">
              <ul className="mdc-chat-stream-activity__log-lines">
                {fullLines.map((entry) => (
                  <ActivityLogLine
                    key={`${activityPhaseKey(entry)}-${entry.id}`}
                    entry={entry}
                    isRising={false}
                  />
                ))}
              </ul>
            </div>
          ) : (
            <RisingLogFeed lines={fullLines.slice(-RISING_LOG_VISIBLE_LINES)} risingIds={risingIds} />
          )}
        </>
      ) : null}
    </div>
  );
}
