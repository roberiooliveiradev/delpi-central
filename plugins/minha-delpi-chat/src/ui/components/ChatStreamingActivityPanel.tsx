import { useEffect, useMemo, useRef, useState } from "react";

import type { ChatStreamActivityEntry } from "../../data/api/chatTypes";
import {
  activityPhaseKey,
  compactActivityLogForDisplay,
  formatActivityLogLine,
  resolveCurrentActivityLine,
  resolveStreamingHeadline,
} from "../../state/utils/streamingActivityLog";

import { ChatThinkingDots } from "./ChatThinkingDots";

import "./ChatStreamingActivityPanel.css";

type ChatStreamingActivityPanelProps = {
  status: string | null;
  entries: ChatStreamActivityEntry[];
  isActive?: boolean;
};

function ActivityLogLine({
  entry,
  compact = false,
}: {
  entry: ChatStreamActivityEntry;
  compact?: boolean;
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
        compact ? "is-compact" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <span className="mdc-chat-stream-activity__log-text">
        {formatActivityLogLine(entry)}
      </span>
      {entry.detail && !compact ? (
        <span className="mdc-chat-stream-activity__log-detail">{entry.detail}</span>
      ) : null}
    </li>
  );
}

export function ChatStreamingActivityPanel({
  status,
  entries,
  isActive = false,
}: ChatStreamingActivityPanelProps) {
  const hasIssues = useMemo(
    () => entries.some((entry) => entry.level === "warning" || entry.level === "error"),
    [entries],
  );

  const compactLines = useMemo(() => compactActivityLogForDisplay(entries), [entries]);
  const currentLine = useMemo(() => resolveCurrentActivityLine(entries), [entries]);
  const headline = resolveStreamingHeadline(status, entries);

  const [showLog, setShowLog] = useState(false);
  const groupsRef = useRef<HTMLDivElement | null>(null);
  const previousLineIdRef = useRef<string | null>(null);
  const [linePulse, setLinePulse] = useState(false);

  useEffect(() => {
    if (hasIssues || isActive) {
      setShowLog(false);
    }
  }, [hasIssues, isActive]);

  useEffect(() => {
    const lineId = currentLine?.id ?? null;

    if (lineId && lineId !== previousLineIdRef.current) {
      previousLineIdRef.current = lineId;
      setLinePulse(true);
      const timer = window.setTimeout(() => setLinePulse(false), 320);
      return () => window.clearTimeout(timer);
    }

    previousLineIdRef.current = lineId;
    return undefined;
  }, [currentLine?.id]);

  useEffect(() => {
    if (!showLog || !groupsRef.current) {
      return;
    }

    groupsRef.current.scrollTop = groupsRef.current.scrollHeight;
  }, [compactLines, showLog]);

  const hasLog = compactLines.length > 0;

  return (
    <div className="mdc-chat-stream-activity" role="status" aria-live="polite">
      {isActive ? <ChatThinkingDots label={headline} /> : null}

      {currentLine ? (
        <p
          key={currentLine.id}
          className={[
            "mdc-chat-stream-activity__current-line",
            linePulse ? "is-updating" : "",
            currentLine.state === "active" ? "is-active" : "",
          ]
            .filter(Boolean)
            .join(" ")}
        >
          {formatActivityLogLine(currentLine)}
        </p>
      ) : isActive ? (
        <p className="mdc-chat-stream-activity__current-line is-active">{headline}</p>
      ) : null}

      {hasLog ? (
        <>
          <button
            type="button"
            className="mdc-chat-stream-activity__collapse"
            aria-expanded={showLog}
            onClick={() => setShowLog((current) => !current)}
          >
            {showLog ? "Ocultar etapas" : `Ver etapas (${compactLines.length})`}
          </button>

          {showLog ? (
            <div ref={groupsRef} className="mdc-chat-stream-activity__log">
              <ul className="mdc-chat-stream-activity__log-lines">
                {compactLines.map((entry) => (
                  <ActivityLogLine
                    key={activityPhaseKey(entry)}
                    entry={entry}
                    compact
                  />
                ))}
              </ul>
            </div>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
