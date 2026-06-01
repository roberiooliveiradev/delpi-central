import { ChevronDown, Gauge, Sparkles, Zap } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import type { ChatResponseModeId, ChatResponseModeOption } from "../../data/api/chatTypes";

import "./ChatResponseModeSelector.css";

type ChatResponseModeSelectorProps = {
  modes: ChatResponseModeOption[];
  value: ChatResponseModeId;
  disabled?: boolean;
  onChange: (mode: ChatResponseModeId) => void;
};

function modeIcon(mode: ChatResponseModeId) {
  if (mode === "fast") {
    return <Zap size={15} aria-hidden="true" />;
  }

  if (mode === "thinker") {
    return <Sparkles size={15} aria-hidden="true" />;
  }

  return <Gauge size={15} aria-hidden="true" />;
}

export function ChatResponseModeSelector({
  modes,
  value,
  disabled,
  onChange,
}: ChatResponseModeSelectorProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement | null>(null);
  const active = modes.find((item) => item.id === value) ?? modes[0];

  useEffect(() => {
    if (!open) {
      return;
    }

    function handlePointerDown(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", handlePointerDown);

    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
    };
  }, [open]);

  if (!active || modes.length === 0) {
    return null;
  }

  return (
    <div
      className="mdc-chat-response-mode"
      ref={rootRef}
      data-tour="composer-response-mode"
    >
      <button
        type="button"
        className="mdc-chat-response-mode__trigger"
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
        title={active.description}
      >
        {modeIcon(active.id)}
        <span>{active.label}</span>
        <ChevronDown size={14} aria-hidden="true" />
      </button>

      {open ? (
        <div className="mdc-chat-response-mode__menu" role="listbox" aria-label="Modo de resposta">
          {modes.map((mode) => (
            <button
              key={mode.id}
              type="button"
              role="option"
              aria-selected={mode.id === value}
              className={
                mode.id === value
                  ? "mdc-chat-response-mode__option mdc-chat-response-mode__option--active"
                  : "mdc-chat-response-mode__option"
              }
              onClick={() => {
                onChange(mode.id);
                setOpen(false);
              }}
            >
              <span className="mdc-chat-response-mode__option-label">
                {modeIcon(mode.id)}
                <strong>{mode.label}</strong>
              </span>
              <small>{mode.description}</small>
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
