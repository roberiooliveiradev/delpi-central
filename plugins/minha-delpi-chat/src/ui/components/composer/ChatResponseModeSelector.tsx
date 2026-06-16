import { Gauge, Sparkles, Zap } from "lucide-react";

import type { ChatResponseModeId, ChatResponseModeOption } from "../../../data/api/chatTypes";
import { ComposerOptionSelector } from "../shared/composer/ComposerOptionSelector";
import "../shared/composer/composer-option-selector.css";

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
  return (
    <ComposerOptionSelector
      options={modes}
      value={value}
      disabled={disabled}
      onChange={onChange}
      renderIcon={modeIcon}
      menuLabel="Modo de resposta"
      tourId="composer-response-mode"
    />
  );
}
