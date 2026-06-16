import {
  BarChart3,
  GitBranch,
  LayoutDashboard,
  LayoutGrid,
  Sparkles,
  Type,
} from "lucide-react";

import type { ChatPresentationFormatId } from "../../data/api/chatTypes";
import type { ChatPresentationFormatOption } from "../../state/hooks/useChatPresentationFormat";
import { ComposerOptionSelector } from "./shared/composer/ComposerOptionSelector";

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
  return (
    <ComposerOptionSelector
      options={options}
      value={value}
      disabled={disabled}
      onChange={onChange}
      renderIcon={formatIcon}
      menuLabel="Formato da resposta"
      tourId="composer-presentation-format"
      className="mdc-composer-option-selector mdc-chat-response-mode"
    />
  );
}
