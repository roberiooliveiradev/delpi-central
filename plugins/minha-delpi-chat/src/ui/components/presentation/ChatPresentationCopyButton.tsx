import { useState } from "react";
import { Check, Copy } from "lucide-react";

import { copyTextToClipboard, scheduleCopyFeedback } from "../chatClipboard";

type ChatPresentationCopyButtonProps = {
  getText: () => string;
  copyLabel?: string;
  copiedLabel?: string;
  copyAriaLabel?: string;
  copiedAriaLabel?: string;
  className?: string;
};

export function ChatPresentationCopyButton({
  getText,
  copyLabel = "Copiar",
  copiedLabel = "Copiado",
  copyAriaLabel = "Copiar conteúdo",
  copiedAriaLabel = "Conteúdo copiado",
  className = "mdc-chat-code-block__copy",
}: ChatPresentationCopyButtonProps) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    const text = getText().trim();

    if (!text) {
      return;
    }

    try {
      await copyTextToClipboard(text);
      setCopied(true);
      scheduleCopyFeedback(setCopied);
    } catch {
      /* clipboard indisponível */
    }
  }

  return (
    <button
      type="button"
      className={className}
      onClick={() => void handleCopy()}
      aria-label={copied ? copiedAriaLabel : copyAriaLabel}
    >
      {copied ? <Check size={15} aria-hidden="true" /> : <Copy size={15} aria-hidden="true" />}
      <span>{copied ? copiedLabel : copyLabel}</span>
    </button>
  );
}
