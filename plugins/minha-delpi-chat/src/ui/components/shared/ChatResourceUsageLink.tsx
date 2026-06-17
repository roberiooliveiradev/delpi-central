import { Copy } from "lucide-react";
import { useMemo, useState } from "react";

import { handleChatNavClick } from "../../../navigation/chatNavigation";

import "./ChatResourceUsageLink.css";

type ChatResourceUsageLinkProps = {
  href: string;
  label?: string;
  hint?: string;
};

export function ChatResourceUsageLink({
  href,
  label = "Link de uso",
  hint = "Mesma URL usada ao abrir no chat.",
}: ChatResourceUsageLinkProps) {
  const [copied, setCopied] = useState(false);
  const fullUrl = useMemo(() => {
    if (typeof window === "undefined") {
      return href;
    }

    return `${window.location.origin}${href}`;
  }, [href]);

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(fullUrl);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      // ignore clipboard errors silently
    }
  }

  return (
    <div className="mdc-chat-resource-link">
      <span className="mdc-chat-resource-link__label">{label}</span>
      <div className="mdc-chat-resource-link__row">
        <a href={href} onClick={(event) => handleChatNavClick(event, href)}>
          {fullUrl}
        </a>
        <button
          type="button"
          className="mdc-chat-ws-outline-btn"
          onClick={() => void copyLink()}
          title={`Copiar ${label.toLowerCase()}`}
        >
          <Copy size={15} aria-hidden="true" />
          <span>{copied ? "Copiado" : "Copiar"}</span>
        </button>
      </div>
      {hint ? <small>{hint}</small> : null}
    </div>
  );
}
