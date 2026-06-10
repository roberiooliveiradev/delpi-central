import {
  BarChart3,
  ChevronDown,
  GitBranch,
  LayoutDashboard,
  LayoutGrid,
  Sparkles,
  Type,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";

import type { ChatPresentationFormatId } from "../../data/api/chatTypes";
import type { ChatPresentationFormatOption } from "../../state/hooks/useChatPresentationFormat";

import "./ChatResponseModeSelector.css";

type ChatPresentationFormatSelectorProps = {
  options: ChatPresentationFormatOption[];
  value: ChatPresentationFormatId;
  disabled?: boolean;
  onChange: (format: ChatPresentationFormatId) => void;
};

function formatIcon(format: ChatPresentationFormatId) {
  if (format === "text") {
    return <Type size={15} aria-hidden="true" />;
  }

  if (format === "table") {
    return <LayoutGrid size={15} aria-hidden="true" />;
  }

  if (format === "tree") {
    return <GitBranch size={15} aria-hidden="true" />;
  }

  if (format === "chart") {
    return <BarChart3 size={15} aria-hidden="true" />;
  }

  if (format === "dashboard") {
    return <LayoutDashboard size={15} aria-hidden="true" />;
  }

  return <Sparkles size={15} aria-hidden="true" />;
}

export function ChatPresentationFormatSelector({
  options,
  value,
  disabled,
  onChange,
}: ChatPresentationFormatSelectorProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement | null>(null);
  const active = options.find((item) => item.id === value) ?? options[0];

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

  if (!active || options.length === 0) {
    return null;
  }

  return (
    <div
      className="mdc-chat-response-mode"
      ref={rootRef}
      data-tour="composer-presentation-format"
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
        {formatIcon(active.id)}
        <span>{active.label}</span>
        <ChevronDown size={14} aria-hidden="true" />
      </button>

      {open ? (
        <div className="mdc-chat-response-mode__menu" role="listbox" aria-label="Formato da resposta">
          {options.map((option) => (
            <button
              key={option.id}
              type="button"
              role="option"
              aria-selected={option.id === value}
              className={
                option.id === value
                  ? "mdc-chat-response-mode__option mdc-chat-response-mode__option--active"
                  : "mdc-chat-response-mode__option"
              }
              onClick={() => {
                onChange(option.id);
                setOpen(false);
              }}
            >
              <span className="mdc-chat-response-mode__option-label">
                {formatIcon(option.id)}
                <strong>{option.label}</strong>
              </span>
              <small>{option.description}</small>
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
